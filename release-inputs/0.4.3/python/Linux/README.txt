SYNNOVER AI3D Python SDK 0.4.3

支持 64 位 CPython 3.7–3.12。
1. 解压后，在包含 wheelhouse 的目录打开终端。
2. 进入要运行相机程序的 Python 环境。
3. 离线安装 SDK 与 NumPy：
   python -m pip install --no-index --find-links=./wheelhouse "pip>=20.3"
   python -m pip install --no-index --find-links=./wheelhouse synnover-ai3d==0.4.3
4. 检查安装：
   python -c "import synnover_ai3d, numpy; print(synnover_ai3d.__version__, numpy.__version__)"
5. 编辑示例中的推理主机地址，然后运行：
   python Examples/single_frame.py
   或 python Examples/continuous_frames.py

single_frame.py：获取一组同步彩色图、深度和点云。
continuous_frames.py：连续取帧，并查询指定像素的深度。
两个示例使用相同接口和变量命名。结束时会停止设备采集。

完整步骤和 venv / uv / Conda 命令见 Docs/SYNNOVER-AI3D-Customer-Manual.html。
SDK 客户端无需 CUDA、TensorRT 或 OpenCV。
