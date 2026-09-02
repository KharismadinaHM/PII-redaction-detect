# ──────────────────────────────────────────────
# PII Detection & Redaction System — Docker Image
# Multi-stage build: Python 3.9 + Tesseract OCR
# ──────────────────────────────────────────────

FROM python:3.9-slim AS base

# System dependencies: Tesseract OCR + required libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ind \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy language model during build
RUN python -m spacy download en_core_web_sm

# Copy application source code
COPY . .

# Create data directory for runtime artifacts
RUN mkdir -p /app/data

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck: verify Streamlit responds
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Run Streamlit in headless mode
ENTRYPOINT ["python", "-m", "streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
