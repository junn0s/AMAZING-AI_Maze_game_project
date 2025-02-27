#!/bin/bash
cd /home/ubuntu/maze-game

# 새로운 가상환경 생성
python3 -m venv venv

# 권한 수정 (ubuntu 계정이 접근 가능하도록 설정)
sudo chown -R ubuntu:ubuntu venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# Gunicorn 설치
pip install gunicorn

echo "🎯 Python dependencies installed successfully!"
