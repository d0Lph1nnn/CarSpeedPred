import cv2
import numpy as np
import datetime
from ultralytics import YOLO
from app.config import (
    DEVICE, MODEL_PATH, SPEED_LIMIT_KMH, REAL_WORLD_DISTANCE_METERS,
    LINE_1_RATIO, LINE_2_RATIO
)

model = YOLO(MODEL_PATH)
model.to(DEVICE)

# Vehicles classes: 2: car, 3: motorcycle, 5: bus, 7: truck
VEHICLE_CLASSES = [2, 3, 5, 7]

class SpeedTracker:
    def __init__(self, fps):
        self.fps = fps
        self.vehicle_entry_frames = {}  # {track_id: frame_idx}
        self.vehicle_speeds = {}        # {track_id: speed_kmh}
        self.records = []               # list of all speed dicts

    def process_frame(self, frame, frame_idx):
        h, w = frame.shape[:2]
        line1_y = int(h * LINE_1_RATIO)
        line2_y = int(h * LINE_2_RATIO)
        
        # Draw the virtual reference lines
        cv2.line(frame, (0, line1_y), (w, line1_y), (255, 255, 0), 2)
        cv2.line(frame, (0, line2_y), (w, line2_y), (255, 0, 255), 2)
        
        # YOLOv8 Tracking with ByteTrack (or default botsort)
        results = model.track(frame, persist=True, classes=VEHICLE_CLASSES, conf=0.25, verbose=False)
        
        active_track_ids = set()

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            
            for box, track_id in zip(boxes, track_ids):
                active_track_ids.add(track_id)
                x1, y1, x2, y2 = map(int, box)
                
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                # Check line crossings (Top to Bottom movement assumed)
                margin = 15
                
                # Entry: Line 1
                if abs(cy - line1_y) < margin and track_id not in self.vehicle_entry_frames:
                    self.vehicle_entry_frames[track_id] = frame_idx
                
                # Exit: Line 2 (Speed Calculation)
                if abs(cy - line2_y) < margin and track_id in self.vehicle_entry_frames and track_id not in self.vehicle_speeds:
                    entry_frame = self.vehicle_entry_frames[track_id]
                    dt_frames = frame_idx - entry_frame
                    if dt_frames > 0:
                        dt_seconds = dt_frames / self.fps
                        speed_ms = REAL_WORLD_DISTANCE_METERS / dt_seconds
                        speed_kmh = speed_ms * 3.6
                        self.vehicle_speeds[track_id] = speed_kmh
                        
                        is_violation = speed_kmh > SPEED_LIMIT_KMH
                        record = {
                            "track_id": track_id,
                            "speed": speed_kmh,
                            "is_violation": is_violation,
                            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                        }
                        self.records.append(record)
                
                # Drawing Minimalist Boxes and ID
                speed = self.vehicle_speeds.get(track_id)
                text = f"#{track_id}"
                
                if speed is None:
                    # Speed not calculated yet: neutral thin box
                    color = (200, 200, 200)
                    thickness = 1
                    text_color = (0, 0, 0)
                else:
                    # Speed calculated: Green or Red box
                    is_violation = speed > SPEED_LIMIT_KMH
                    color = (0, 0, 255) if is_violation else (0, 255, 0)
                    thickness = 2
                    text_color = (255, 255, 255)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                
                # Draw ID text only
                (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x1, y1 - 25), (x1 + tw, y1), color, -1)
                cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
                    
        return frame, active_track_ids
