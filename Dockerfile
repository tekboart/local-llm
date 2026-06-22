FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System dependencies required by your stack
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libmagic1 \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade packaging tools (important for Python 3.13 compatibility)
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
# (no-cache to keep image size reasonable)
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Streamlit config
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]