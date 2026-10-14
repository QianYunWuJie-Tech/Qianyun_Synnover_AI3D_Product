"""python camera.py [camera-address] [new-recording-directory]"""
import argparse
from synnover_ai3d import SYNNOVERCamera

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("address", nargs="?", default="")
parser.add_argument("output", nargs="?")
args = parser.parse_args()
camera = SYNNOVERCamera()
try:
    camera.open(args.address)
    depth = camera.get_depth()          # H x W, float32, meters
    points = camera.get_pcd("xyzrgb")   # N x 6: X Y Z R G B
    print("Depth:", depth.shape, "Points:", points.shape)
    if args.output:
        camera.get_frame().save(args.output)
finally:
    camera.stop()                      # Stops the camera and model on Ubuntu
