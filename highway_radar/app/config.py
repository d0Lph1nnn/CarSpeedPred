import os
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_PATH = "yolov8n.pt"
SPEED_LIMIT_KMH = 80.0
REAL_WORLD_DISTANCE_METERS = 20.0

LINE_1_RATIO = 0.58
LINE_2_RATIO = 0.82

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
