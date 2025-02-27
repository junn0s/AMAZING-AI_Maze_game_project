#!/bin/bash
cd /home/ubuntu/maze-game

# Python 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# Gunicorn 설치
pip install gunicorn

echo "🎯 Python dependencies installed successfully!"
