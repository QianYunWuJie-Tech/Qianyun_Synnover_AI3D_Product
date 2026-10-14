SYNNOVER AI3D Python SDK 0.4.2-rc.3 (candidate)

Supported: CPython 3.7 through 3.12, x86-64; Ubuntu 22.04/24.04 or Windows 10/11 x64.
This release contains the CPU Python client only. It does not replace Viewer, C++ SDK,
TensorRT models, the RTX runtime or firmware. A configured RTX inference host is required.

1. Extract the archive to a permanent directory.
2. Activate your existing Python 3.7-3.12 environment and open a terminal here.
3. Install offline (pip selects the matching ABI and NumPy automatically):
   python -m pip install --no-index --only-binary=:all: --find-links=wheelhouse synnover-ai3d==0.4.2rc3
4. Check the install:
   python -c "import synnover_ai3d,numpy; print(synnover_ai3d.__version__,numpy.__version__)"
5. With camera and RTX connected, run:
   python Examples/camera.py 192.168.88.2

No CUDA, TensorRT, OpenCV or GPU is needed on the client for the SDK itself.
Python 3.7 uses NumPy 1.21.6; 3.8 uses 1.24.4; 3.9-3.12 use 1.26.4 in this package.
Optional GUI/YOLO examples have separate dependencies and are not implied by SDK support.

Validation: all 12 native OS/Python jobs installed the repaired wheels and passed
frame/format/ownership/NaN/save/orientation tests and lifecycle/fault recovery with
a simulated device. This is not physical camera or new RTX3060 qualification.
Protocol and API remain compatible with the existing 0.4.1 inference host.
