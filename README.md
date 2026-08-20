# ⚡ Highway AI Speed Radar & Violation Tracking System

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)](https://github.com/ultralytics/ultralytics)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

A high-performance, real-time computer vision and intelligent transportation system (ITS) pipeline designed to detect vehicles, assign persistent multi-object tracking IDs, calculate real-time velocities ($km/h$) using virtual spatial-temporal reference lines, detect speed limit violations, and stream telemetry data to a modern dark-themed interactive dashboard.

---

## 📌 Key Highlights & Features

- **Robust Multi-Object Tracking:** Leverages **YOLOv8** combined with **ByteTrack** for persistent vehicle ID retention across frame occlusions.
- **Mathematical Speed Estimation:** Calculates physical vehicle velocity via time-of-flight ($\Delta t$) across calibrated virtual line gates.
- **Real-Time Speed Violation Radar:** Dynamically flags speeding vehicles exceeding configured thresholds and logs infraction events instantly.
- **Minimalist Computer Vision Rendering:** Clean, non-intrusive bounding boxes with ID badges on video and detailed telemetry in the side panel.
- **Zero-Latency Telemetry Streaming:** Uses **Server-Sent Events (SSE)** to push real-time traffic statistics, FPS, and violation logs to the UI without page reloading.
- **Interactive Player Controls:** Full state-machine support for real-time video playback toggling (`Play` / `Pause` / `Reset`).
- **Modular & Production-Ready:** Structured with decoupled configuration, tracker logic, API routing, and single entry-point execution.

---

## 📐 Mathematical & Computer Vision Pipeline

```
   [ Raw Video Stream ] 
            │
            ▼
 ┌──────────────────────┐
 │ YOLOv8 Object Detect │ ──► Filters Classes: [Car, Bus, Truck, Motorcycle]
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ ByteTrack Associates │ ──► Assigns Unique Track ID & Updates Bounding Box Centroids
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Virtual Line Gate    │ ──► Entry Line ($Y_1$): Records $t_{start} = Frame_{in}$
 │ Passage Detector     │ ──► Exit Line ($Y_2$):  Records $t_{end} = Frame_{out}$
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Velocity Calculation │ ──► $\Delta t = rac{|Frame_{out} - Frame_{in}|}{FPS}$
 └──────────┬───────────┘     $V_{km/h} = \left(rac{d_{meters}}{\Delta t}
ight) 	imes 3.6$
            │
            ▼
 ┌──────────────────────┐
 │ Violation Evaluator  │ ──► If $V_{km/h} > V_{limit}$ ➔ Flag Infraction & Broadcast
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ FastAPI / SSE Engine │ ──► MJPEG Stream + Real-Time Telemetry Dashboard
 └──────────────────────┘
```

### Velocity Formula:
$$\Delta t = rac{|Frame_{entry} - Frame_{exit}|}{	ext{Video FPS}}$$

$$V_{	ext{vehicle}} = \left( rac{d_{	ext{calibrated}}}{\Delta t} 
ight) 	imes 3.6 \quad [	ext{km/h}]$$

---

## 📂 Project Architecture

```text
highway_radar/
│
├── app/
│   ├── __init__.py
│   ├── config.py         # Hardware setup, detection hyperparams & coordinate ratios
│   ├── tracker.py        # Core YOLOv8 inference, ByteTrack logic & drawing badges
│   └── api.py            # FastAPI router, MJPEG video generator, SSE telemetry & UI
│
├── uploads/              # Storage directory for uploaded surveillance footage
├── .gitignore            # Git exclusion rules
├── requirements.txt      # Pinned dependency requirements
├── main.py               # Uvicorn server launcher
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- NVIDIA GPU with CUDA support *(Optional, automatically falls back to CPU)*

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/Highway-Speed-Radar-AI.git
cd Highway-Speed-Radar-AI/highway_radar
```

### 3. Create & Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch Application
```bash
python main.py
```
Or start directly with Uvicorn:
```bash
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

Open your browser and navigate to: **`http://127.0.0.1:8000`**

---

## ⚙️ Configuration (`app/config.py`)

You can calibrate and customize detection parameters inside `app/config.py`:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SPEED_LIMIT_KMH` | `float` | `80.0` | Maximum permissible highway speed threshold. |
| `REAL_WORLD_DISTANCE_METERS` | `float` | `20.0` | Calibrated physical distance between Line 1 and Line 2. |
| `LINE_1_RATIO` | `float` | `0.58` | Vertical position of the entrance gate ($58\%$ of frame height). |
| `LINE_2_RATIO` | `float` | `0.82` | Vertical position of the calculation gate ($82\%$ of frame height). |
| `MODEL_PATH` | `str` | `"yolov8n.pt"` | Pretrained YOLOv8 checkpoint. |

---

## 🌐 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the interactive Tailwind CSS dark dashboard. |
| `GET` | `/api/v1/video-feed` | Streams MJPEG multi-part video frames with visual overlays. |
| `GET` | `/api/v1/stats-stream` | Server-Sent Events (SSE) stream broadcasting real-time metrics. |
| `POST` | `/api/v1/upload` | Uploads a new traffic video file for analysis. |
| `POST` | `/api/v1/video/toggle-pause` | Toggles streaming state between Play and Pause. |
| `POST | `/api/v1/video/reset` | Resets frame pointer, vehicle tracker cache, and violation logs. |

---

## 🛠️ Tech Stack & Libraries

- **Deep Learning / Vision:** `ultralytics (YOLOv8)`, `PyTorch`, `OpenCV (cv2)`, `ByteTrack`
- **Backend & Networking:** `FastAPI`, `Uvicorn`, `sse-starlette`, `python-multipart`
- **Frontend / Styling:** `HTML5`, `JavaScript (Vanilla ES6)`, `Tailwind CSS (CDN)`

---

## 👤 Author

- **Developer:** Yunus Emre Demirbozan
- **LinkedIn:** [linkedin.com/in/yunus-emre-demirbozan](https://linkedin.com/in/)
- **GitHub:** [@yunusemredemirbozan](https://github.com/)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
![Highway Radar Demo](assets/demo.png)
