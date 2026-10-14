import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from synnover_ai3d import Pipeline, Config

config = Config()
config.address = sys.argv[1] if len(sys.argv) > 1 else "192.168.88.2"
config.mode = "1280x720"
output_root = Path("output").resolve()
output_run = output_root / ("single_frame_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
pipeline = Pipeline()
try:
    pipeline.open(config, timeout_ms=180000)
    frame = pipeline.wait_for_frames(timeout_ms=10000)
    color_bgr = frame.get_rgb("bgr", "left")
    depth_m = frame.get_depth("m")
    points_xyzrgb = frame.get_pcd("xyzrgb", stride=1)

    # 保存这个 frame，不再额外取一帧；点云保存完整有效点，单位米。
    output_dir = output_run / ("frame_0000_" + str(frame.frame_id))
    frame.save(str(output_dir))
    np.save(str(output_dir / "depth_meters.npy"), depth_m)
    print("帧编号：", frame.frame_id)
    print("彩色图：", color_bgr.shape, "深度图：", depth_m.shape)
    print("点云：", points_xyzrgb.shape)
    print("保存位置：", output_dir)
finally:
    pipeline.close()  # 停止设备采集，也会影响同设备的其他客户端
