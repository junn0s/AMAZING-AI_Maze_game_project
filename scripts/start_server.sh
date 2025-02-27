#!/bin/bash
cd /home/ubuntu/maze-game
source venv/bin/activate

# 기존 Gunicorn 프로세스 종료
pkill -f "gunicorn"

# Gunicorn을 사용해 애플리케이션 실행
nohup gunicorn -w 4 -b 0.0.0.0:8000 maze:main > server.log 2>&1 &

echo "🚀 Maze Game Server started successfully!"
