#!/bin/bash
cd /home/ubuntu/maze-game

sudo chown -R ubuntu:ubuntu /home/ubuntu/maze-game
sudo chmod -R 775 /home/ubuntu/maze-game

# 새로운 가상환경 생성
python3 -m venv venv

# 권한 수정 (ubuntu 계정이 접근 가능하도록 설정)
sudo chown -R ubuntu:ubuntu venv

# 가상환경 활성화
source venv/bin/activate

# 기존 .env 삭제 후 다시 생성
rm -f .env
echo "OPENAI_API_KEY=$(aws s3 cp s3://codedeploy-mello/.env - | grep OPENAI_API_KEY | cut -d '=' -f2)" >> .env
echo "TAVILY_API_KEY=$(aws s3 cp s3://codedeploy-mello/.env - | grep TAVILY_API_KEY | cut -d '=' -f2)" >> .env

# .env 파일 로드
export $(grep -v '^#' .env | xargs)

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# Gunicorn 설치
pip install gunicorn

echo "🎯 Python dependencies installed successfully!"
