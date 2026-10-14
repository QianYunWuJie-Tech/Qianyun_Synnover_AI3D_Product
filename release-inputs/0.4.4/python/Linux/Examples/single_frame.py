import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from synnover_ai3d import Pipeline, Config, OutputOptions

config = Config()
config.address = sys.argv[1] if len(sys.argv) > 1 else "192.168.88.2"
config.mode = "1280x720"
config.camera_source = "synnover"
options = OutputOptions()
# 始终保存到 SDK 包根目录，与终端或 IDE 的工作目录无关。
output_root = Path(__file__).resolve().parent.parent / "output"
output_run = output_root / ("single_frame_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
output_run.mkdir(parents=True, exist_ok=False)
print("本次输出目录：", output_run, flush=True)
pipeline = Pipeline()
try:
    pipeline.open(config, timeout_ms=180000)
    frame = pipeline.wait_for_frames(timeout_ms=10000)
    color_bgr = frame.get_rgb("bgr", "left")
    depth_m = frame.get_depth("m")
    points_xyzrgb = frame.get_pcd("xyzrgb", options)

    # 保存这个 frame，不再额外取一帧；点云按 options 范围和步长保存，单位米。
    output_dir = output_run / ("frame_0000_" + str(frame.frame_id))
    # frame.save 会创建 frame_* 目录；不要提前创建该目录。
    frame.save(str(output_dir), options)
    np.save(str(output_dir / "depth_meters.npy"), depth_m)
    print("帧编号：", frame.frame_id)
    print("彩色图：", color_bgr.shape, "深度图：", depth_m.shape)
    print("点云：", points_xyzrgb.shape)
    print("保存位置：", output_dir)
finally:
    pipeline.close()  # 停止设备采集，也会影响同设备的其他客户端
