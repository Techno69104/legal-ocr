#!/bin/bash

echo "=== Starting build with Python 3.11 ==="

# Use Python 3.11 explicitly
export PYTHON_VERSION=3.11.9

# Install system packages
apt-get update
apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    libjpeg-dev \
    zlib1g-dev \
    libgl1-mesa-glx

# Upgrade pip
pip install --upgrade pip wheel setuptools

# Install Python packages (no compilation needed)
pip install --no-cache-dir --prefer-binary \
    flask==2.3.3 \
    gradio==3.50.2 \
    pdfplumber==0.10.4 \
    pdf2image==1.16.3 \
    gunicorn==21.2.0 \
    pytesseract==0.3.10 \
    opencv-python-headless==4.8.1.78 \
    numpy==1.24.3 \
    Werkzeug==2.3.0

echo "=== Build completed successfully ==="
