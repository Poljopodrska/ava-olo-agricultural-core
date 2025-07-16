#!/bin/bash
# Emergency startup script for AWS App Runner debugging
echo "🚀 START.SH: Beginning startup sequence..."
echo "📍 Current directory: $(pwd)"
echo "📁 Files in directory: $(ls -la)"
echo "🐍 Python version: $(python3 --version)"
echo "📦 Pip packages: $(pip list)"
echo "🚀 Starting emergency API..."
python3 api_gateway_emergency.py