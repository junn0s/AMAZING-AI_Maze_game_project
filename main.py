from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from maze_game import MazeState, advance_game

app = FastAPI()

game_state: Optional[MazeState] = None

# --- Request/Response 모델 ---
class StartRequest(BaseModel):
    name : str
    location: str
    mood: str

class StartResponse(BaseModel):
    worldDescription: str

class NpcQuizResponse(BaseModel):
    QuizDescription: str

class NpcQuizResultRequest(BaseModel):
    answer: str

class NpcQuizResultResponse(BaseModel):
    answerDescription: str
    result: int

class EndGameResponse(BaseModel):
    finishDescription : str


# ----------------------------------
# 1) 게임 시작 API
# ----------------------------------
@app.post("/world", response_model=StartResponse)
def start_game(req: StartRequest):
    # 1) 새 MazeState
    global game_state
    # num은 필수 int 필드이므로 0 등 초기값을 지정
    game_state = MazeState(
        name=req.name,
        setting=req.location,
        atmosphere=req.mood,
        num="0",
        step="start"
    )

    game_state = advance_game(game_state)

    return StartResponse(
        worldDescription = game_state.message
    )


# ----------------------------------
# 2) NPC 퀴즈 요청 API
# ----------------------------------
@app.get("/npc_quiz", response_model=NpcQuizResponse)
def get_npc_quiz():
    global game_state
    if game_state is None:
        raise HTTPException(status_code=400, detail="게임이 시작되지 않았습니다.")
    
    valid_quiz_steps = [
        "first_encounter_question",
        "second_encounter_question",
        "third_encounter_question"
    ]

    if game_state.step not in valid_quiz_steps:
        raise HTTPException(
            status_code=400,
            detail=f"현재 {game_state.step} 단계에서는 새 퀴즈를 받을 수 없습니다."
        )

    # NPC 퀴즈 단계로 진행
    game_state = advance_game(game_state)

    # game_state.message가 NPC의 퀴즈 텍스트
    return NpcQuizResponse(QuizDescription=game_state.message)

# ----------------------------------
# 3) NPC 퀴즈 정답 제출 API
# ----------------------------------
@app.post("/npc_quiz_result", response_model=NpcQuizResultResponse)
def post_npc_quiz_result(req: NpcQuizResultRequest):
    global game_state
    if game_state is None:
        raise HTTPException(status_code=400, detail="게임이 시작되지 않았습니다.")

    valid_followup_steps = [
        "first_encounter_followup",
        "second_encounter_followup",
        "third_encounter_followup"
    ]
    if game_state.step not in valid_followup_steps:
        raise HTTPException(
            status_code=400,
            detail=f"현재 {game_state.step} 단계에서는 퀴즈 답변을 제출할 수 없습니다."
        )

    # 정답 체크
    game_state = advance_game(game_state, req.answer)
    return NpcQuizResultResponse(
        answerDescription=game_state.message,
        result=game_state.num
    )

# ----------------------------------
# 4) 게임 결말 API
# ----------------------------------
@app.get("/end_game", response_model=EndGameResponse)
def end_game():
    global game_state
    game_state = advance_game(game_state)
    return EndGameResponse(
        finishDescription = game_state.message
    )

