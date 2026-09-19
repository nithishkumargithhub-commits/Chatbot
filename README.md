# 🌾 JeevanPath AI (जीवनपथ AI)

> **AI-Driven Voice Assistant for Livelihood Mapping & NSQF-Aligned Skilling Recommendations for SC Communities under PM-AJAY**  
> *Developed for Smart India Hackathon (SIH)*

---

## 📌 Overview

**JeevanPath AI** is an inclusive, voice-first intelligent assistant engineered to bridge digital and linguistic divides for beneficiaries under the **PM-AJAY (Pradhan Mantri Anusuchit Jaati Abhyuday Yojana)** initiative. 

Many eligible individuals—including rural artisans, youth, and wage workers from Scheduled Caste (SC) communities—face significant literacy and language barriers when navigating complex government skilling catalogs, qualification packs (NSQF), and livelihood welfare programs. JeevanPath AI solves this by providing a conversational, dialect-resilient, vernacular voice interface that accepts natural speech in native regional languages, automatically detects the language, maps skills and aspirations, and delivers tailored, actionable recommendations.

---

## 🏗️ System Architecture

The project is architected in phased, decoupled tiers to ensure ultra-low latency, modularity, and offline/hybrid operational capability:

```
                      +------------------------------------------+
                      |         Beneficiary / User UI            |
                      |    (React + Vite Web / Mobile App)       |
                      +------------------------------------------+
                                           |
                                  Audio Stream / Upload
                                  (WAV, WebM, M4A, OGG)
                                           v
+-----------------------------------------------------------------------------------+
|                           JeevanPath AI Backend (FastAPI)                         |
|                                                                                   |
|  +------------------------+     +-----------------------+     +----------------+  |
|  |     CORS Middleware    | --> |   Temp File Manager   | --> | Audio Validator|  |
|  | (Vite/React dev ports) |     |  (UUID isolation/auto |     | (MIME & Ext    |  |
|  +------------------------+     |     unlink cleanup)   |     |  safety checks)|  |
|                                 +-----------------------+     +----------------+  |
|                                             |                                     |
|                                             v                                     |
|                             +-------------------------------+                     |
|                             |    SpeechService Singleton    |                     |
|                             | (fastapi Depends() injection) |                     |
|                             +-------------------------------+                     |
|                                             |                                     |
|                                             v                                     |
|           +-------------------------------------------------------------+         |
|           |             faster-whisper Engine (CTranslate2)             |         |
|           |                                                             |         |
|           |  * Hardware: NVIDIA CUDA (float16) / CPU fallback (int8)    |         |
|           |  * Model: large-v3 (eager-loaded during FastAPI lifespan)    |         |
|           |  * VAD: Silero VAD (min_silence_duration_ms = 300ms)         |         |
|           |  * Zero-shot Auto Language Detection (threshold >= 0.5)      |         |
|           |  * Anti-Hallucination: condition_on_previous_text=False     |         |
|           |  * Temperature Staircase: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]     |         |
|           +-------------------------------------------------------------+         |
+-----------------------------------------------------------------------------------+
                                           |
                           Structured JSON Response
             { language, language_name, transcript, confidence, ... }
                                           |
                     +---------------------+---------------------+
                     |                                           |
                     v (Current: Phase 1)                        v (Roadmap: Phase 2)
        +-------------------------+                 +---------------------------+
        | Immediate UI Feedback & |                 |  Livelihood & NSQF Engine  |
        | Transcript Verification |                 |  (Skill mapping & Gemini/ |
        +-------------------------+                 |   LLM reasoning in-lang)  |
                                                    +---------------------------+
                                                                 |
                                                                 v
                                                    +---------------------------+
                                                    |  Multilingual Voice Output |
                                                    |  (TTS: Indic-TTS / gTTS)  |
                                                    +---------------------------+
```

---

## 🧩 Key Architectural Decisions & Safeguards

### 1. Zero-Manual-Language-Selection
Rural and vernacular users should not be forced to select their language from a complex dropdown. Speech is processed with `language=None`, allowing Whisper to detect the native tongue directly from phonemes.

### 2. High-Confidence Detection Threshold (`0.5`)
Standard Whisper implementations often commit to a language at low probability thresholds (e.g. 0.25), which causes Indian languages like Tamil or Telugu to be misclassified as English. JeevanPath AI enforces a `language_detection_threshold=0.5`.

### 3. Repetition & Hallucination Defense
- `condition_on_previous_text=False`: Breaks the feedback loop where an initial misrecognition or hallucination is fed as prior context into subsequent audio chunks.
- `compression_ratio_threshold=2.4`: Automatically flags repetitive token outputs and triggers temperature staircasing.
- `no_speech_threshold=0.6`: Discards non-verbal background noise and breathing sounds.

### 4. Tightened Voice Activity Detection (VAD)
Built-in Silero VAD is tuned to `min_silence_duration_ms=300` (down from 500ms) to ensure terminal consonants and brief vernacular words are not clipped.

### 5. High-Performance Hardware Acceleration
- **GPU Inference**: Uses `faster-whisper` (backed by CTranslate2) running in `float16` precision on NVIDIA GPUs (CUDA enabled), reducing latency by up to 4x compared to vanilla HuggingFace / OpenAI Whisper.
- **CPU Fallback**: Gracefully degrades to quantized `int8` on CPU environments without crashing.

---

## 📂 Project Structure

```text
SIH/
├── README.md                 # Project documentation & architectural guide
└── backend/
    ├── config.py             # Single source of truth (models, devices, languages, thresholds)
    ├── main.py               # FastAPI application entry point, lifecycle & CORS setup
    ├── requirements.txt      # Python package dependencies
    ├── temp_audio/           # Ephemeral storage for audio file transcription
    ├── routes/
    │   ├── __init__.py
    │   └── voice.py          # Voice processing router (/api/voice/transcribe)
    └── services/
        ├── __init__.py
        └── speech.py         # SpeechService singleton, faster-whisper configuration
```

---

## 🌐 Supported Languages (Current & Reserved)

| ISO Code | Language | Current Status |
| :--- | :--- | :--- |
| `ta` | Tamil (தமிழ்) | ✅ Active (Phase 1) |
| `te` | Telugu (తెలుగు) | ✅ Active (Phase 1) |
| `hi` | Hindi (हिन्दी) | ✅ Active (Phase 1) |
| `en` | English | ✅ Active (Phase 1) |
| `kn` | Kannada (ಕನ್ನಡ) | ✅ Active (Phase 1) |
| `ml` | Malayalam (മലയാളം) | ✅ Active (Phase 1) |
| `mr` | Marathi (मराठी) | ⏳ Reserved (Phase 2) |
| `gu` | Gujarati (ગુજરાતી) | ⏳ Reserved (Phase 2) |
| `bn` | Bengali (বাংলা) | ⏳ Reserved (Phase 2) |
| `pa` | Punjabi (ਪੰਜਾਬੀ) | ⏳ Reserved (Phase 2) |
| `or` | Odia (ଓଡ଼ିଆ) | ⏳ Reserved (Phase 2) |

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** (Python 3.11/3.12 recommended)
- **CUDA Toolkit** & **cuDNN** (if running on NVIDIA GPU; PyTorch CUDA `torch==2.11.0+cu128` or compatible)
- **FFmpeg / Libav** installed and available in system `PATH` (required for audio decoding)

### 1. Backend Setup

Navigate into the backend directory:
```bash
cd backend
```

Create and activate a virtual environment:
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install backend requirements:
```bash
pip install -r requirements.txt
```

> **⚠️ Critical Note on PyTorch & CUDA:**  
> Do **NOT** run `pip install torch` directly from standard PyPI if you have a CUDA setup, as it will overwrite CUDA-accelerated PyTorch with a CPU-only build. Ensure PyTorch is pre-installed with CUDA support.

### 2. Running the Server

Start the FastAPI application with Uvicorn:
```bash
uvicorn main:app --reload --port 8000
```

Once running:
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 API Reference

### 1. Health Check
`GET /health`

**Response (`200 OK`)**:
```json
{
  "status": "ok",
  "service": "JeevanPath AI",
  "version": "0.1.0",
  "model": "large-v3",
  "device": "cuda",
  "compute_type": "float16"
}
```

---

### 2. Speech-to-Text with Language Detection
`POST /api/voice/transcribe`

Accepts an audio file via `multipart/form-data` recorded directly from the browser or microphone.

**Form Parameters:**
- `audio`: Audio binary file (`WAV`, `WebM`, `M4A`, `OGG`, `MP3`, `MP4`, `AAC`, `FLAC`). Max size: **25 MB**.

**Response (`200 OK`)**:
```json
{
  "language": "ta",
  "language_name": "Tamil",
  "transcript": "நான் தையல் வேலை செய்கிறேன், எனக்கு தையல் பயிற்சி மற்றும் கடன் உதவி வேண்டும்.",
  "confidence": 0.9421
}
```

**Status Codes:**
- `200 OK`: Successful transcription and language identification.
- `400 Bad Request`: Empty or missing audio file.
- `413 Request Entity Too Large`: File exceeds 25 MB limit.
- `415 Unsupported Media Type`: Non-audio or unsupported media container.
- `503 Service Unavailable`: Whisper model still loading or GPU unavailable.

---

## 🗺️ Roadmap & Planned Phases

- [x] **Phase 1: Robust Indic Voice Ingestion**
  - High-accuracy regional speech transcription (`faster-whisper large-v3`).
  - Native language detection without user intervention.
  - Ephemeral file handling with strict memory safeguards.
- [ ] **Phase 2: Conversational Intelligence & NSQF Alignment**
  - Dialect-aware conversational engine (Gemini API / Indic-LLM).
  - NSQF (National Skills Qualification Framework) qualification pack mapping.
  - PM-AJAY welfare scheme and skill cluster eligibility matching.
  - Multilingual Text-to-Speech (TTS) voice generation.
- [ ] **Phase 3: Community Deployment & Low-Bandwidth Mode**
  - Offline-capable Edge/PWA voice agent.
  - WhatsApp & IVR integration for non-smartphone users.
  - Interactive livelihood roadmap dashboard for counselors and beneficiaries.

---

## 📜 License & Acknowledgments
Built with ❤️ for **Smart India Hackathon (SIH)**.  
Aims to advance digital inclusion, economic empowerment, and skill development for underprivileged communities under **PM-AJAY**.
