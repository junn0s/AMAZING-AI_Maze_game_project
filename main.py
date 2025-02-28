from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from llm_langchain import MazeState, advance_game
from image_generate import generate_image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 경우 특정 도메인만 허용하도록 수정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

game_state: Optional[MazeState] = None

# --- Request/Response 모델 ---
class MazeResponse(BaseModel):
    width: int
    height: int
    maze: List[List[int]]
    userPos: List[int]
    npcCnt: int
    npcPos: List[List[int]]
    exitPos: List[int]



class MazeRequest(BaseModel):
    loc : List[int]

class StartRequest(BaseModel):
    name : str
    location: str
    mood: str

class StartResponse(BaseModel):
    worldDescription: str
    image: str

class NpcQuizResponse(BaseModel):
    quiz : str
    option1 : str
    option2 : str
    option3 : str

class NpcQuizResultRequest(BaseModel):
    answer: str

class NpcQuizResultResponse(BaseModel):
    answerDescription: str
    result: int

class EndGameResponse(BaseModel):
    finishDescription : str



# ----------------------------------
# 0) 미로 출력
# ----------------------------------

@app.get("/maze", response_model=MazeResponse)
def get_maze():
    return MazeResponse(
        width = 11,
        height =  11,
        maze = [
            [1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1],
            [1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1],
            [1, 2, 0, 0, 1, 0, 2, 1, 0, 1, 1],
            [1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
            [1, 1, 0, 0, 0, 3, 0, 0, 0, 0, 1],
            [1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1],
            [1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1],
            [1, 0, 0, 0, 1, 0, 1, 0, 0, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ],
        userPos = [5,5],
        npcCnt = 3,
        npcPos = [
            [3, 1],
            [3, 6],
            [9, 9]
        ],
        exitPos = [0, 6]
    )


@app.post("/maze_mod", response_model=MazeResponse)
def post_maze(req: MazeRequest):
    # 기존 미로 데이터 정의 (예시)
    maze_data = {
        "width": 11,
        "height": 11,
        "maze": [
            [1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1],
            [1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1],
            [1, 2, 0, 0, 1, 0, 2, 1, 0, 1, 1],
            [1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
            [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1],
            [1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1],
            [1, 0, 0, 0, 1, 0, 1, 0, 0, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ],
        "userPos": [5, 5],
        "npcCnt": 3,
        "npcPos": [
            [3, 1],
            [3, 6],
            [9, 9]
        ],
        "exitPos": [0, 6]
    }

    # 클라이언트로부터 입력받은 좌표 (예: [행, 열])
    input_coord = req.loc

    # NPC 좌표 리스트에서 입력 좌표와 일치하는 좌표 제거
    new_npcPos = [npc for npc in maze_data["npcPos"] if npc != input_coord]
    maze_data["npcPos"] = new_npcPos
    maze_data["npcCnt"] = len(new_npcPos)

    # 사용자 좌표도 업데이트 (원하는 대로 설정 가능)
    maze_data["userPos"] = input_coord

    # 미로의 input_coord 위치에 값을 3으로 설정
    row, col = input_coord
    maze_data["maze"][row][col] = 3

    return MazeResponse(**maze_data)



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
        step="start",
        quiz = "",
        option1 = "",
        option2 = "",
        option3 = ""
    )

    game_state = advance_game(game_state)

    image_prompt = (
        f"The location is {req.location} and the mood is {req.mood}. Create a pixel-style image related to this location and mood."
    )
    image_url = generate_image(image_prompt, size="1024x1024")


    return StartResponse(
        worldDescription = game_state.message,
        image = image_url
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
    return NpcQuizResponse(
        quiz = game_state.quiz,
        option1 = game_state.option1,
        option2 = game_state.option2,
        option3 = game_state.option3

    )

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

