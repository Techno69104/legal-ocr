#!/bin/bash

echo "Starting Render build with PyMuPDF fix..."

# Update system packages
apt-get update

# Install system dependencies from packages.txt
apt-get install -y \
    poppler-utils \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libfontconfig1 \
    libgl1-mesa-glx

# Upgrade pip and install wheel
pip install --upgrade pip wheel setuptools

# Install Python dependencies (use --no-cache-dir to save space)
pip install --no-cache-dir -r requirements.txt

# Alternative: Install pymupdf separately with pre-built wheel
# pip install --no-cache-dir --only-binary :all: pymupdf

echo "Build completed successfully!"
