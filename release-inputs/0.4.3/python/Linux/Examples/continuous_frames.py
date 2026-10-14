import csv
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from synnover_ai3d import Pipeline, Config

config = Config()
config.address = sys.argv[1] if len(sys.argv) > 1 else "192.168.88.2"
config.mode = "1280x720"
frame_count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
save_every = 20  # 保存第 1、21、41…帧；改为 1 可保存每帧，但会占用更多空间并降低取帧速度。
if frame_count < 1:
    raise ValueError("frame_count 必须大于 0")
output_root = Path("output").resolve()
output_run = output_root / ("continuous_frames_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
output_run.mkdir(parents=True, exist_ok=False)
pipeline = Pipeline()
try:
    pipeline.open(config, timeout_ms=180000)
    with (output_run / "query_pixels.csv").open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["frame_id", "x", "y", "depth_at_pixel_m", "saved_directory"])
        for index in range(frame_count):
            frame = pipeline.wait_for_frames(timeout_ms=10000)
            color_bgr = frame.get_rgb("bgr", "left")
            depth_m = frame.get_depth("m")
            points_xyzrgb = frame.get_pcd("xyzrgb", stride=1)

            # x 是列、y 是行，从 0 开始；可改成你需要的像素坐标。
            x = frame.width // 2
            y = frame.height // 2
            depth_at_pixel_m = frame.get_distance(x, y)
            saved_directory = ""
            if index % save_every == 0:
                output_dir = output_run / ("frame_%04d_%s" % (index, frame.frame_id))
                frame.save(str(output_dir))
                np.save(str(output_dir / "depth_meters.npy"), depth_m)
                saved_directory = output_dir.name
                print("保存位置：", output_dir)
            writer.writerow([frame.frame_id, x, y, depth_at_pixel_m, saved_directory])
            if math.isfinite(depth_at_pixel_m) and depth_at_pixel_m > 0:
                print("帧编号：", frame.frame_id, "像素：", (x, y), "深度：", depth_at_pixel_m, "米")
            else:
                print("帧编号：", frame.frame_id, "像素：", (x, y), "深度无效")
    print("逐帧深度记录：", output_run / "query_pixels.csv")
finally:
    pipeline.close()  # 停止设备采集，也会影响同设备的其他客户端
