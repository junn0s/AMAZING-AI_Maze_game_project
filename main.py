# main.py

from fastapi import FastAPI
from pydantic import BaseModel
import uuid

from maze_game import MazeState

app = FastAPI()

# 전역에 {게임ID: MazeState} 형태로 저장
games = {}

# --- Request/Response 모델 ---
class StartRequest(BaseModel):
    setting: str
    atmosphere: str

class StartResponse(BaseModel):
    game_id: str
    lines: list[str]
    step: str

class NextRequest(BaseModel):
    game_id: str
    player_answer: str

class NextResponse(BaseModel):
    lines: list[str]
    step: str

# ----------------------------------
# 1) 게임 시작 API
# ----------------------------------
@app.post("/start_game", response_model=StartResponse)
def start_game(req: StartRequest):
    """
    1) 새 MazeState 생성
    2) story_graph 첫 번째 노드(start) 실행
    3) state.message를 줄바꿈 단위로 쪼개서 반환
    """
    # 1) 새 MazeState
    state = MazeState(setting=req.setting, atmosphere=req.atmosphere)

    # 2) 그래프 실행
    raw_data = game_runner.invoke(state)
    new_state = MazeState.model_validate(raw_data)

    # 3) UUID 발급 후 games에 저장
    game_id = str(uuid.uuid4())
    games[game_id] = new_state

    # 4) message를 줄바꿈 기준으로 split
    lines = new_state.message.split('\n') if new_state.message else []

    return StartResponse(
        game_id=game_id,
        lines=lines,
        step=new_state.step
    )

# ----------------------------------
# 2) 다음 단계 API
# ----------------------------------
@app.post("/next_step", response_model=NextResponse)
def next_step(req: NextRequest):
    """
    1) games에서 game_id로 MazeState 가져오기
    2) player_answer 설정
    3) 그래프 실행
    4) state.message를 줄바꿈 단위로 쪼개서 반환
    """
    state = games.get(req.game_id, None)
    if not state:
        # 에러 처리 (게임 세션 없을 때)
        return NextResponse(lines=["잘못된 game_id"], step="error")

    # 2) player_answer에 사용자 답변 저장
    state.player_answer = req.player_answer

    # 3) 그래프 실행
    raw_data = game_runner.invoke(state)
    updated_state = MazeState.model_validate(raw_data)
    games[req.game_id] = updated_state  # 업데이트

    # 4) message를 줄바꿈 기준으로 split
    lines = updated_state.message.split('\n') if updated_state.message else []

    return NextResponse(
        lines=lines,
        step=updated_state.step
    )
