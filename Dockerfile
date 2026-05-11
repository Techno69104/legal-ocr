# Use Python 3.11 official image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    libjpeg-dev \
    zlib1g-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    flask==2.3.3 \
    gradio==3.50.2 \
    pdfplumber==0.10.4 \
    pdf2image==1.16.3 \
    gunicorn==21.2.0 \
    pytesseract==0.3.10 \
    opencv-python-headless==4.8.1.78 \
    numpy==1.24.3 \
    Werkzeug==2.3.0

# Copy application code
COPY app.py .

# Expose port
EXPOSE 10000

# Run the application
CMD ["gunicorn", "app:flask_app", "--bind", "0.0.0.0:10000", "--timeout", "300", "--workers", "1"]
