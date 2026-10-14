import math
from synnover_ai3d import Pipeline, Config

config = Config()
config.address = "192.168.88.2"
config.mode = "1280x720"
pipeline = Pipeline()
try:
    pipeline.open(config, timeout_ms=180000)
    for _ in range(100):  # 连续读取 100 组；需要持续运行时可改为 while True:
        frame = pipeline.wait_for_frames(timeout_ms=10000)
        color_bgr = frame.get_rgb("bgr", "left")        # 左目彩色图，H×W×3
        depth_m = frame.get_depth("m")                 # 深度图，H×W，单位米
        points_xyzrgb = frame.get_pcd("xyzrgb", stride=2)  # 点云，N×6

        # 示例查询当前图像中心；也可换成你需要的像素坐标。
        x = frame.width // 2
        y = frame.height // 2
        depth_at_pixel_m = frame.get_distance(x, y)
        print("帧编号：", frame.frame_id, "点云：", points_xyzrgb.shape)
        if math.isfinite(depth_at_pixel_m) and depth_at_pixel_m > 0:
            print("像素：", (x, y), "深度：", depth_at_pixel_m, "米")
        else:
            print("像素：", (x, y), "深度无效，本帧跳过该点")
finally:
    pipeline.close()  # 停止设备采集，也会影响同设备的其他客户端
