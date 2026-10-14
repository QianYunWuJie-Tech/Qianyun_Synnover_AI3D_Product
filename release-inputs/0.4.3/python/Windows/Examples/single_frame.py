from synnover_ai3d import Pipeline, Config

config = Config()
config.address = "192.168.88.2"
config.mode = "1280x720"
pipeline = Pipeline()
try:
    pipeline.open(config, timeout_ms=180000)
    frame = pipeline.wait_for_frames(timeout_ms=10000)
    color_bgr = frame.get_rgb("bgr", "left")        # 左目彩色图，H×W×3
    depth_m = frame.get_depth("m")                 # 深度图，H×W，单位米
    points_xyzrgb = frame.get_pcd("xyzrgb", stride=2)  # 点云，N×6
    print("帧编号：", frame.frame_id)
    print("彩色图：", color_bgr.shape)
    print("深度图：", depth_m.shape)
    print("点云：", points_xyzrgb.shape)
finally:
    pipeline.close()  # 停止设备采集，也会影响同设备的其他客户端
