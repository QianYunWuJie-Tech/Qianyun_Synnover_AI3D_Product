"""python capture.py [address] [new-record-directory] [new-cloud.ply]"""
import sys
from synnover_ai3d import Config, Pipeline
config = Config()
if len(sys.argv) > 1:
    config.address = sys.argv[1]
pipeline = Pipeline()
try:
    pipeline.start(config, 180000)
    frame = pipeline.wait_for_frames(30000)
    print(frame.width, frame.height, frame.distance(frame.width // 2, frame.height // 2), "m")
    if len(sys.argv) > 2:
        frame.save(sys.argv[2])
    if len(sys.argv) > 3:
        frame.pointcloud(stride=2).export_ply(sys.argv[3])
finally:
    pipeline.stop()
