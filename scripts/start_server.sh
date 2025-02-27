#!/bin/bash
cd /home/ubuntu/maze-game

# 환경 변수 설정
set -o allexport
source .env
set +o allexport

# # 기존 .env 삭제 후 다시 생성
# rm -f .env
# echo "OPENAI_API_KEY=${OPENAI_API_KEY}" > .env
# echo "TAVILY_API_KEY=${TAVILY_API_KEY}" >> .env

source venv/bin/activate

# 기존 Gunicorn 프로세스 종료
pkill -f "gunicorn"

# Gunicorn을 사용해 애플리케이션 실행
nohup gunicorn -w 4 -b 0.0.0.0:8000 --chdir /home/ubuntu/maze-game -k uvicorn.workers.UvicornWorker main:app > server.log 2>&1 &

echo "🚀 Maze Game Server started successfully!"
