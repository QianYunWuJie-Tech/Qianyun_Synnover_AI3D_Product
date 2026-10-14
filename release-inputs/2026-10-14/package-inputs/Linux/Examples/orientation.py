"""python orientation.py [address] --degrees 180 [--lock]"""
import argparse
from synnover_ai3d import SYNNOVERCamera

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("address", nargs="?", default="")
parser.add_argument("--degrees", type=int, choices=[0, 90, 180, 270], default=0)
parser.add_argument("--lock", action="store_true")
args = parser.parse_args()
camera = SYNNOVERCamera()
try:
    camera.open(args.address)
    orientation = camera.get_status()["orientation"]
    camera.set_orientation(orientation["degrees"], False)
    camera.set_orientation(args.degrees, args.lock)
    frame = camera.get_frame()
    print(frame.get_rgb().shape, frame.get_depth().shape)
    print("Centre depth:", frame.get_distance(frame.width // 2, frame.height // 2), "m")
finally:
    camera.stop()
