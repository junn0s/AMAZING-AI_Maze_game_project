#!/bin/bash
cd /home/ubuntu/maze-game

# 환경 변수 설정
export OPENAI_API_KEY=${OPENAI_API_KEY}
export TAVILY_API_KEY=${TAVILY_API_KEY}

source venv/bin/activate

# 기존 Gunicorn 프로세스 종료
pkill -f "gunicorn"

# Gunicorn을 사용해 애플리케이션 실행
nohup gunicorn -w 4 -b 0.0.0.0:8000 --chdir /home/ubuntu/maze-game -k uvicorn.workers.UvicornWorker main:app > server.log 2>&1 &

echo "🚀 Maze Game Server started successfully!"
