#!/usr/bin/env python3
"""SYNNOVER equivalent of nanning.py's camera/YOLO loop; no robot commands.

python nanning_camera.py --address 192.168.88.2
python nanning_camera.py --address 192.168.88.2 --weights ./best.pt
Requires the released synnover-ai3d SDK and NumPy; GUI needs opencv-python.
Use the existing YOLO environment and local weights for --weights.
"""
import argparse
import json
from pathlib import Path

import numpy as np


def images_from_frame(frame):
    """One owned FrameSet -> aligned BGR, depth in meters, this frame's intrinsics."""
    meta = frame.metadata
    if meta.get('synchronized') is not True:
        raise ValueError('A synchronized RGB/depth FrameSet is required')
    bgr = frame.get_rgb('bgr', 'left')
    depth_m = frame.get_depth('m')
    k = dict(meta['intrinsics'])
    height, width = depth_m.shape
    if bgr.shape != (height, width, 3) or bgr.dtype != np.uint8 or depth_m.dtype != np.float32:
        raise ValueError('RGB/depth shape or dtype does not match the SDK contract')
    if (k['width'], k['height']) != (width, height):
        raise ValueError('Intrinsics do not match this frame; do not reuse old calibration')
    if not all(np.isfinite(k[key]) for key in ('fx', 'fy', 'cx', 'cy')) or min(k['fx'], k['fy']) <= 0:
        raise ValueError('Invalid intrinsics')
    return bgr, depth_m, k


def pixel_xyz(depth_m, intrinsics, x, y):
    """XYZ in this frame's oriented left-camera coordinates, meters; invalid -> None."""
    height, width = depth_m.shape
    if not (0 <= x < width and 0 <= y < height):
        return None
    z = float(depth_m[y, x])
    if not np.isfinite(z) or z <= 0:
        return None
    k = intrinsics
    return ((x - k['cx']) * z / k['fx'], (y - k['cy']) * z / k['fy'], z)


def mask_target(depth_m, intrinsics, mask):
    """Pick an observed valid pixel nearest a mask's center; not a robot grasp pose."""
    mask = np.asarray(mask, dtype=bool)
    if mask.shape != depth_m.shape:
        raise ValueError('Segmentation mask must be in the original RGB pixel coordinates')
    my, mx = np.nonzero(mask)
    if not len(mx):
        return None
    valid = mask & np.isfinite(depth_m) & (depth_m > 0)
    ys, xs = np.nonzero(valid)
    if not len(xs):
        return None
    best = int(np.argmin((xs - mx.mean()) ** 2 + (ys - my.mean()) ** 2))
    x, y = int(xs[best]), int(ys[best])
    return {'pixel': [x, y], 'xyz_m': list(pixel_xyz(depth_m, intrinsics, x, y)),
            'valid_depth_pixels': int(len(xs)), 'mask_pixels': int(len(mx))}


def yolo_targets(result, depth_m, intrinsics):
    """Use masks.xy (already in original-image pixels), avoiding fixed letterbox crops."""
    import cv2
    if tuple(result.orig_shape) != depth_m.shape:
        raise ValueError('YOLO result and depth are from different image sizes')
    if result.masks is None or result.boxes is None:
        return []
    targets = []
    # Enumerate instances: duplicate class names must not select the same mask twice.
    for index, polygon in enumerate(result.masks.xy):
        if len(polygon) < 3:
            continue
        mask = np.zeros(depth_m.shape, dtype=np.uint8)
        cv2.fillPoly(mask, [np.rint(polygon).astype(np.int32)], 1)
        target = mask_target(depth_m, intrinsics, mask)
        if target is None:
            continue
        class_id = int(result.boxes.cls[index].item())
        target.update(instance=index, class_id=class_id, name=result.names[class_id],
                      confidence=float(result.boxes.conf[index].item()))
        targets.append(target)
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--address', default='192.168.88.2', help='127.0.0.1 on the RTX itself')
    parser.add_argument('--port', type=int, default=47650)
    parser.add_argument('--resolution', choices=('640x480', '1280x720'), default='1280x720')
    parser.add_argument('--weights', type=Path, help='Existing local YOLO segmentation .pt file')
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--frames', type=int, default=0, help='0 means run until interrupted')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--save', type=Path, help='Save the first FrameSet to a NEW directory')
    parser.add_argument('--stop-device-on-exit', action='store_true', help='Also stop camera/model for all clients')
    args = parser.parse_args()
    if args.frames < 0 or args.imgsz <= 0:
        parser.error('--frames must be nonnegative and --imgsz must be positive')
    if args.save and args.save.exists():
        parser.error('--save must name a new directory')
    model = None
    if args.weights:
        if not args.weights.is_file():
            parser.error('--weights must be an existing local file')
        from ultralytics import YOLO
        model = YOLO(str(args.weights))
    cv2 = None
    if not args.headless:
        import cv2
    from synnover_ai3d import Config, Pipeline
    config = Config()
    config.address, config.port, config.mode = args.address, args.port, args.resolution
    pipeline = Pipeline()
    displayed = {'depth': None, 'k': None}

    def click(event, x, y, flags, unused):
        if event == cv2.EVENT_LBUTTONDOWN and displayed['depth'] is not None:
            print(json.dumps({'pixel': [x, y], 'xyz_m': pixel_xyz(displayed['depth'], displayed['k'], x, y)}, ensure_ascii=False))

    try:
        # Select "synnover camera" in Viewer before starting this example.
        pipeline.start(config, timeout_ms=180000)
        if cv2 is not None:
            cv2.namedWindow('SYNNOVER camera', cv2.WINDOW_AUTOSIZE)
            cv2.setMouseCallback('SYNNOVER camera', click)
        count = 0
        while args.frames == 0 or count < args.frames:
            frame = pipeline.wait_for_frames(timeout_ms=10000)
            bgr, depth_m, k = images_from_frame(frame)
            # Already aligned, already meters: no rs.align(), no depth_scale multiplication.
            report = {'frame_id': frame.frame_id, 'source': frame.metadata.get('input_source'),
                      'simulated': frame.metadata.get('simulated'), 'intrinsics': k,
                      'center_xyz_m': pixel_xyz(depth_m, k, frame.width // 2, frame.height // 2)}
            view = bgr
            if model is not None:
                result = model(bgr, conf=0.3, imgsz=args.imgsz, verbose=False)[0]
                report['targets'] = yolo_targets(result, depth_m, k)
                view = result.plot()
            if args.save and count == 0:
                frame.save(str(args.save))
            print(json.dumps(report, ensure_ascii=False, allow_nan=False), flush=True)
            if cv2 is not None:
                displayed.update(depth=depth_m, k=k)
                cv2.imshow('SYNNOVER camera', view)
                if cv2.waitKey(1) & 0xff in (27, ord('q')):
                    break
            count += 1
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if args.stop_device_on_exit:
                pipeline.close(timeout_ms=180000)
        finally:
            pipeline.stop()  # Only disconnect this SDK client; unlike SYNNOVERCamera.stop().
            if cv2 is not None:
                cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
