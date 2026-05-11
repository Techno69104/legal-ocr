#!/bin/bash

echo "Installing system dependencies..."
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils

echo "Installing Python packages..."
pip install --upgrade pip
pip install --no-cache-dir flask gradio pdfplumber pdf2image pillow gunicorn opencv-python-headless numpy pytesseract

echo "Build complete!"
