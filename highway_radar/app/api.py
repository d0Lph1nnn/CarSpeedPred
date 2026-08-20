import os
import cv2
import asyncio
import json
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from app.config import UPLOAD_DIR
from app.tracker import SpeedTracker

app = FastAPI(title="Highway AI Speed Radar")

# Global State
global_state = {
    "is_paused": False,
    "reset_requested": False,
    "video_path": None,
    "stats": {
        "total_vehicles": 0,
        "avg_speed": 0.0,
        "violation_count": 0,
        "fps": 0,
        "recent_records": []
    }
}

html_dashboard = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Highway AI Speed Radar</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f172a; color: #f8fafc; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid #334155; }
    </style>
</head>
<body class="min-h-screen p-4 flex flex-col items-center">
    <!-- Header -->
    <header class="w-full max-w-6xl flex justify-between items-center py-4 mb-6 border-b border-slate-700">
        <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            Highway AI Speed Radar
        </h1>
        <div class="flex gap-4 items-center">
            <span id="fps-badge" class="px-3 py-1 text-sm font-semibold rounded-full bg-slate-800 text-slate-300 border border-slate-600">FPS: --</span>
            <input type="file" id="video-upload" accept="video/*" class="hidden">
            <button onclick="document.getElementById('video-upload').click()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded text-sm font-medium transition">
                Upload Video
            </button>
        </div>
    </header>

    <main class="w-full max-w-6xl flex flex-col lg:flex-row gap-6">
        <!-- Left: Video & Controls -->
        <div class="flex-1 flex flex-col gap-4">
            <div class="relative w-full aspect-video bg-black rounded-lg overflow-hidden border border-slate-700 shadow-2xl">
                <img id="video-feed" src="/api/v1/video-feed" alt="Video Feed" class="w-full h-full object-contain">
                <div id="pause-overlay" class="hidden absolute inset-0 bg-black/50 flex items-center justify-center">
                    <span class="text-4xl text-white opacity-75">PAUSED</span>
                </div>
            </div>
            <div class="flex justify-center gap-4">
                <button onclick="togglePause()" id="pause-btn" class="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded font-semibold transition">
                    Durdur
                </button>
                <button onclick="resetVideo()" class="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded font-semibold transition text-rose-400 hover:text-rose-300">
                    Sıfırla
                </button>
            </div>
        </div>

        <!-- Right: Metrics & Logs -->
        <div class="w-full lg:w-80 flex flex-col gap-4">
            <!-- Metrics Cards -->
            <div class="glass-panel p-4 rounded-lg flex flex-col gap-1">
                <span class="text-sm text-slate-400">Total Vehicles</span>
                <span id="stat-total" class="text-3xl font-bold text-blue-400">0</span>
            </div>
            <div class="glass-panel p-4 rounded-lg flex flex-col gap-1">
                <span class="text-sm text-slate-400">Avg Speed (km/h)</span>
                <span id="stat-avg" class="text-3xl font-bold text-emerald-400">0.0</span>
            </div>
            <div class="glass-panel p-4 rounded-lg flex flex-col gap-1 border-l-4 border-rose-500">
                <span class="text-sm text-slate-400">Violations</span>
                <span id="stat-violations" class="text-3xl font-bold text-rose-500">0</span>
            </div>
            
            <!-- Logs -->
            <div class="glass-panel rounded-lg flex flex-col flex-1 min-h-[300px]">
                <div class="p-3 border-b border-slate-700 bg-slate-800/50">
                    <h3 class="text-sm font-semibold text-slate-300 uppercase tracking-wider">Canlı Radar Akışı</h3>
                </div>
                <div id="log-container" class="p-3 flex-1 overflow-y-auto flex flex-col gap-2">
                    <!-- Logs go here -->
                </div>
            </div>
        </div>
    </main>

    <script>
        const videoUpload = document.getElementById('video-upload');
        const pauseBtn = document.getElementById('pause-btn');
        const pauseOverlay = document.getElementById('pause-overlay');
        const videoFeed = document.getElementById('video-feed');
        
        let isPaused = false;

        videoUpload.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                await fetch('/api/v1/upload', { method: 'POST', body: formData });
                videoFeed.src = "/api/v1/video-feed?" + new Date().getTime();
                isPaused = false;
                updatePauseUI();
            } catch (err) {
                console.error("Upload failed", err);
            }
        });

        async function togglePause() {
            const res = await fetch('/api/v1/video/toggle-pause', { method: 'POST' });
            const data = await res.json();
            isPaused = data.is_paused;
            updatePauseUI();
        }
        
        function updatePauseUI() {
            if (isPaused) {
                pauseBtn.textContent = 'Devam Et';
                pauseOverlay.classList.remove('hidden');
            } else {
                pauseBtn.textContent = 'Durdur';
                pauseOverlay.classList.add('hidden');
            }
        }

        async function resetVideo() {
            await fetch('/api/v1/video/reset', { method: 'POST' });
            isPaused = false;
            updatePauseUI();
        }

        const evtSource = new EventSource("/api/v1/stats-stream");
        evtSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            document.getElementById('fps-badge').textContent = `FPS: ${data.fps}`;
            document.getElementById('stat-total').textContent = data.total_vehicles;
            document.getElementById('stat-avg').textContent = data.avg_speed.toFixed(1);
            document.getElementById('stat-violations').textContent = data.violation_count;
            
            const logContainer = document.getElementById('log-container');
            logContainer.innerHTML = '';
            data.recent_records.forEach(r => {
                const el = document.createElement('div');
                if (r.is_violation) {
                    el.className = "text-xs p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-200 mb-2";
                    el.innerHTML = `<div class="flex justify-between text-slate-400 mb-1"><span>${r.timestamp}</span></div><span class="font-bold">Araç #${r.track_id}</span> -> <span class="font-bold text-rose-400">${r.speed.toFixed(1)} km/h</span> ile geçti (HIZ İHLALİ!)`;
                } else {
                    el.className = "text-xs p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-200 mb-2";
                    el.innerHTML = `<div class="flex justify-between text-slate-400 mb-1"><span>${r.timestamp}</span></div><span class="font-bold">Araç #${r.track_id}</span> -> <span class="font-bold text-emerald-400">${r.speed.toFixed(1)} km/h</span> ile geçti (Normal)`;
                }
                logContainer.appendChild(el);
            });
        };
    </script>
</body>
</html>
"""

@app.get("/")
async def get_dashboard():
    return HTMLResponse(content=html_dashboard)

@app.post("/api/v1/upload")
async def upload_video(file: UploadFile = File(...)):
    global_state["is_paused"] = False
    global_state["reset_requested"] = True
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    global_state["video_path"] = file_path
    return {"message": "Video uploaded successfully", "filename": file.filename}

@app.post("/api/v1/video/toggle-pause")
async def toggle_pause():
    global_state["is_paused"] = not global_state["is_paused"]
    return {"is_paused": global_state["is_paused"]}

@app.post("/api/v1/video/reset")
async def reset_video():
    global_state["reset_requested"] = True
    global_state["is_paused"] = False
    return {"message": "Reset requested"}

async def generate_video_frames():
    cap = None
    tracker = None
    frame_idx = 0
    import time
    
    while True:
        if global_state["video_path"] is None:
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, "Lutfen bir video yukleyin", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            await asyncio.sleep(1)
            continue
            
        if global_state["reset_requested"]:
            if cap is not None:
                cap.release()
            cap = cv2.VideoCapture(global_state["video_path"])
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps == 0 or np.isnan(fps):
                fps = 30.0
            tracker = SpeedTracker(fps)
            frame_idx = 0
            
            global_state["stats"] = {
                "total_vehicles": 0,
                "avg_speed": 0.0,
                "violation_count": 0,
                "fps": 0,
                "recent_records": []
            }
            global_state["reset_requested"] = False
            
        if global_state["is_paused"]:
            await asyncio.sleep(0.1)
            continue
            
        if cap is not None and cap.isOpened():
            start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                global_state["reset_requested"] = True
                continue
                
            frame_idx += 1
            
            # Run tracking in a separate thread to not block asyncio loop
            frame, active_ids = await asyncio.to_thread(tracker.process_frame, frame, frame_idx)
            
            # Update metrics
            speeds = list(tracker.vehicle_speeds.values())
            global_state["stats"]["total_vehicles"] = len(tracker.vehicle_entry_frames)
            if speeds:
                global_state["stats"]["avg_speed"] = sum(speeds) / len(speeds)
            
            violation_count = sum(1 for r in tracker.records if r["is_violation"])
            global_state["stats"]["violation_count"] = violation_count
            
            # Get last 15 records to display in UI
            global_state["stats"]["recent_records"] = list(reversed(tracker.records[-15:]))
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            process_time = time.time() - start_time
            if process_time > 0:
                global_state["stats"]["fps"] = int(1.0 / process_time)
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
            # Basic sleep to prevent burning 100% CPU on fast processing
            await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(1)

@app.get("/api/v1/video-feed")
async def video_feed():
    return StreamingResponse(generate_video_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

async def generate_stats():
    while True:
        yield json.dumps(global_state["stats"])
        await asyncio.sleep(0.5)

@app.get("/api/v1/stats-stream")
async def stats_stream():
    return EventSourceResponse(generate_stats())
