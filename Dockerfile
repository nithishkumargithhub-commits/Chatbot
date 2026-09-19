# JeevanPath AI — Production Dockerfile for Render / Cloud Deployment
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    DEVICE=cpu \
    WHISPER_MODEL_SIZE=base \
    COMPUTE_TYPE=int8

# Install system dependencies (ffmpeg is required for Whisper audio decoding)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only build (keeps image small, under 200MB vs 4GB for CUDA)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements from backend
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper base model at build time for instant container startup
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Copy backend codebase
COPY backend/ .

# Expose port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
