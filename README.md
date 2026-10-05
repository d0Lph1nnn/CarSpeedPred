# ⚡ Highway AI Speed Radar & Violation Tracking System

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)](https://github.com/ultralytics/ultralytics)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

![Highway Radar Demo](assets/demo.png)

**🌐 Language / Dil:** [🇬🇧 English](#english) | [🇹🇷 Türkçe](#türkçe)

---

<a id="english"></a>

# 🇬🇧 English

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

```text
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
 │ Virtual Line Gate    │ ──► Entry Line (Y1): Records t_start = Frame_in
 │ Passage Detector     │ ──► Exit Line  (Y2): Records t_end   = Frame_out
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Velocity Calculation │ ──► Δt = |Frame_out - Frame_in| / FPS
 └──────────┬───────────┘     V (km/h) = (d_meters / Δt) × 3.6
            │
            ▼
 ┌──────────────────────┐
 │ Violation Evaluator  │ ──► If V > V_limit ➔ Flag Infraction & Broadcast
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ FastAPI / SSE Engine │ ──► MJPEG Stream + Real-Time Telemetry Dashboard
 └──────────────────────┘
```

### Velocity Formula

$$\Delta t = \frac{|Frame_{entry} - Frame_{exit}|}{\text{Video FPS}}$$

$$V_{\text{vehicle}} = \left( \frac{d_{\text{calibrated}}}{\Delta t} \right) \times 3.6 \quad [\text{km/h}]$$

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
git clone https://github.com/d0Lph1nnn/CarSpeedPred.git
cd CarSpeedPred/highway_radar
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
| `POST` | `/api/v1/video/reset` | Resets frame pointer, vehicle tracker cache, and violation logs. |

---

## 🛠️ Tech Stack & Libraries

- **Deep Learning / Vision:** `ultralytics (YOLOv8)`, `PyTorch`, `OpenCV (cv2)`, `ByteTrack`
- **Backend & Networking:** `FastAPI`, `Uvicorn`, `sse-starlette`, `python-multipart`
- **Frontend / Styling:** `HTML5`, `JavaScript (Vanilla ES6)`, `Tailwind CSS (CDN)`

---

## 👤 Author

- **Developer:** Yunus Emre Demirbozan
- **LinkedIn:** [linkedin.com/in/yunus-emre-demirbozan](https://linkedin.com/in/yunus-emre-demirbozan)
- **GitHub:** [@d0Lph1nnn](https://github.com/d0Lph1nnn)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

[⬆ Back to top / Başa dön](#-highway-ai-speed-radar--violation-tracking-system)

---

<a id="türkçe"></a>

# 🇹🇷 Türkçe

Araçları tespit eden, kalıcı çoklu nesne takip kimlikleri atayan, sanal uzamsal-zamansal referans çizgileri üzerinden gerçek zamanlı hız ($km/h$) hesaplayan, hız sınırı ihlallerini belirleyen ve telemetri verilerini modern, koyu temalı etkileşimli bir panele aktaran; yüksek performanslı, gerçek zamanlı bir bilgisayarlı görü ve akıllı ulaşım sistemi (ITS) hattı.

---

## 📌 Öne Çıkan Özellikler

- **Sağlam Çoklu Nesne Takibi:** Karelerdeki örtüşmelere (occlusion) rağmen araç kimliklerini korumak için **YOLOv8** ve **ByteTrack** birlikte kullanılır.
- **Matematiksel Hız Tahmini:** Kalibre edilmiş sanal çizgi kapıları arasındaki geçiş süresi ($\Delta t$) üzerinden aracın fiziksel hızını hesaplar.
- **Gerçek Zamanlı Hız İhlali Radarı:** Tanımlı sınırı aşan araçları dinamik olarak işaretler ve ihlal olaylarını anında kaydeder.
- **Minimalist Görüntü Çizimi:** Videoda kimlik etiketli sade sınırlayıcı kutular, yan panelde ise ayrıntılı telemetri gösterilir.
- **Gecikmesiz Telemetri Akışı:** Trafik istatistiklerini, FPS değerini ve ihlal kayıtlarını sayfa yenilemeden arayüze iletmek için **Server-Sent Events (SSE)** kullanır.
- **Etkileşimli Oynatıcı Kontrolleri:** Gerçek zamanlı video oynatmayı değiştirmek için tam durum makinesi desteği (`Oynat` / `Duraklat` / `Sıfırla`).
- **Modüler ve Üretime Hazır:** Ayrıştırılmış yapılandırma, takip mantığı, API yönlendirme ve tek giriş noktalı çalıştırma ile yapılandırılmıştır.

---

## 📐 Matematiksel ve Bilgisayarlı Görü Hattı

```text
   [ Ham Video Akışı ]
            │
            ▼
 ┌──────────────────────┐
 │ YOLOv8 Nesne Tespiti │ ──► Sınıf Filtresi: [Araba, Otobüs, Kamyon, Motosiklet]
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ ByteTrack Eşleştirme │ ──► Benzersiz Takip Kimliği Atar & Kutu Merkezlerini Günceller
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Sanal Çizgi Kapısı   │ ──► Giriş Çizgisi (Y1): t_başlangıç = Kare_giriş
 │ Geçiş Dedektörü      │ ──► Çıkış Çizgisi (Y2): t_bitiş     = Kare_çıkış
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Hız Hesaplama        │ ──► Δt = |Kare_çıkış - Kare_giriş| / FPS
 └──────────┬───────────┘     V (km/sa) = (d_metre / Δt) × 3.6
            │
            ▼
 ┌──────────────────────┐
 │ İhlal Değerlendirici │ ──► V > V_sınır ise ➔ İhlali İşaretle & Yayınla
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ FastAPI / SSE Motoru │ ──► MJPEG Akışı + Gerçek Zamanlı Telemetri Paneli
 └──────────────────────┘
```

### Hız Formülü

$$\Delta t = \frac{|Kare_{giriş} - Kare_{çıkış}|}{\text{Video FPS}}$$

$$V_{\text{araç}} = \left( \frac{d_{\text{kalibre}}}{\Delta t} \right) \times 3.6 \quad [\text{km/sa}]$$

---

## 📂 Proje Mimarisi

```text
highway_radar/
│
├── app/
│   ├── __init__.py
│   ├── config.py         # Donanım ayarı, tespit hiperparametreleri ve koordinat oranları
│   ├── tracker.py        # Çekirdek YOLOv8 çıkarımı, ByteTrack mantığı ve kimlik etiketi çizimi
│   └── api.py            # FastAPI yönlendirici, MJPEG video üreteci, SSE telemetri ve arayüz
│
├── uploads/              # Yüklenen gözetim görüntülerinin saklandığı dizin
├── .gitignore            # Git hariç tutma kuralları
├── requirements.txt      # Sabitlenmiş bağımlılık listesi
├── main.py               # Uvicorn sunucu başlatıcısı
└── README.md             # Proje dokümantasyonu
```

---

## 🚀 Başlarken

### 1. Gereksinimler

- Python 3.10 veya üzeri
- CUDA destekli NVIDIA GPU *(İsteğe bağlı, yoksa otomatik olarak CPU'ya geçer)*

### 2. Depoyu Klonlayın

```bash
git clone https://github.com/d0Lph1nnn/CarSpeedPred.git
cd CarSpeedPred/highway_radar
```

### 3. Sanal Ortam Oluşturun ve Etkinleştirin

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 5. Uygulamayı Başlatın

```bash
python main.py
```

Veya doğrudan Uvicorn ile başlatın:

```bash
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

Tarayıcınızı açıp şu adrese gidin: **`http://127.0.0.1:8000`**

---

## ⚙️ Yapılandırma (`app/config.py`)

Tespit parametrelerini `app/config.py` içinde kalibre edip özelleştirebilirsiniz:

| Parametre | Tür | Varsayılan | Açıklama |
| :--- | :--- | :--- | :--- |
| `SPEED_LIMIT_KMH` | `float` | `80.0` | İzin verilen azami otoyol hız sınırı. |
| `REAL_WORLD_DISTANCE_METERS` | `float` | `20.0` | 1. ve 2. çizgi arasındaki kalibre edilmiş gerçek mesafe. |
| `LINE_1_RATIO` | `float` | `0.58` | Giriş kapısının dikey konumu (kare yüksekliğinin $58\%$'i). |
| `LINE_2_RATIO` | `float` | `0.82` | Hesaplama kapısının dikey konumu (kare yüksekliğinin $82\%$'si). |
| `MODEL_PATH` | `str` | `"yolov8n.pt"` | Önceden eğitilmiş YOLOv8 model dosyası. |

---

## 🌐 API Referansı

| Metot | Uç Nokta | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/` | Etkileşimli Tailwind CSS koyu temalı paneli sunar. |
| `GET` | `/api/v1/video-feed` | Görsel katmanlı MJPEG çok parçalı video karelerini akıtır. |
| `GET` | `/api/v1/stats-stream` | Gerçek zamanlı metrikleri yayınlayan Server-Sent Events (SSE) akışı. |
| `POST` | `/api/v1/upload` | Analiz için yeni bir trafik videosu yükler. |
| `POST` | `/api/v1/video/toggle-pause` | Akış durumunu Oynat ve Duraklat arasında değiştirir. |
| `POST` | `/api/v1/video/reset` | Kare işaretçisini, araç takip önbelleğini ve ihlal kayıtlarını sıfırlar. |

---

## 🛠️ Teknoloji Yığını ve Kütüphaneler

- **Derin Öğrenme / Görü:** `ultralytics (YOLOv8)`, `PyTorch`, `OpenCV (cv2)`, `ByteTrack`
- **Arka Uç ve Ağ:** `FastAPI`, `Uvicorn`, `sse-starlette`, `python-multipart`
- **Ön Yüz / Stil:** `HTML5`, `JavaScript (Vanilla ES6)`, `Tailwind CSS (CDN)`

---

## 👤 Geliştirici

- **Geliştirici:** Yunus Emre Demirbozan
- **LinkedIn:** [linkedin.com/in/yunus-emre-demirbozan](https://linkedin.com/in/yunus-emre-demirbozan)
- **GitHub:** [@d0Lph1nnn](https://github.com/d0Lph1nnn)

---

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Ayrıntılar için [LICENSE](LICENSE) dosyasına bakınız.

[⬆ Back to top / Başa dön](#-highway-ai-speed-radar--violation-tracking-system)
