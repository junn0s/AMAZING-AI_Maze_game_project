from dotenv import load_dotenv
load_dotenv()

import json
from typing import List, Optional
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

# -------------------------
# 1) Pydantic 모델 정의
# -------------------------
class MazeState(BaseModel):
    setting: str
    atmosphere: str

    step: str = "start"
    message: str = ""
    next: str = ""

    inventory: List[str] = Field(default_factory=list)
    history: List[str] = Field(default_factory=list)
    location: str = "미로 입구"
    story_data: Optional[dict] = None

    # NPC 질문 시 플레이어의 최신 선택
    player_answer: str = ""

# -------------------------
# 2) GPT 모델 설정
# -------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",   
    temperature=0.7
)
memory = ConversationBufferMemory(return_messages=True)

# -------------------------
# 3) 노드 함수들
# -------------------------

def generate_story(state: MazeState) -> MazeState:
    prompt = f"""
    게임 개요: 사용자가 설정한 장소와 분위기 기반으로 AI가 미로와 스토리를 생성하며, 목적은 미로 탈출. NPC와의 상호작용이 중요한 요소.
    플레이어가 미로의 장소로 '{state.setting}', 분위기로 '{state.atmosphere}'를 입력했습니다.

    무조건 위 게임 개요와 사용자가 입력한 설정을 바탕으로 방탈출게임 느낌의 스토리와 세계관을 만들어줘
    셰계관을 만들고 아래 예시와 똑같이 JSON으로 출력해야 해. 그리고 삼중 백틱(```)이나 다른 코드 블록 문법은 절대 사용하지 마.
    예시 :
    {{
        "world_description": "너가 생성한 세계관 및 스토리 전체 내용",
        "objective": "미로탈출 게임의 세계관 기반 궁극적 목표, 플레이어한테 게임 관리자가 설명하듯이 존댓말로 해줘",
        "story_details": {{
            "background": 스토리의 시작을 소설의 첫 부분 처럼 존댓말로 작성",
            "intro": "스토리 초반부 상황 설명을 게임 관리자가 플레이어한테 소설의 첫 부분에서 이야기하듯이 존댓말로 작성",
            "middle": "스토리 중반부 상황 설명을 게임 관리자가 플레이어한테 소설처럼 이야기하듯이 존댓말로 작성",
            "final": "스토리 후반부 상황 설명을 게임 관리자가 플레이어한테 소설처럼 이야기하듯이 존댓말로 작성",
            "result": "스토리 결말을 소설처럼 이야기하듯이 존댓말로 작성"
        }},
        "npcs": [
            {{"name": "NPC 이름", "role": "NPC 역할", "personality": "특징 및 말투"}}
            // 추가 NPC 정보
        ]
    }}

    위 예시를 무조건 지켜.
    """
    response = llm.invoke(prompt).content
    try:
        story_data = json.loads(response)
    except json.JSONDecodeError:
        print("LLM이 JSON 형식으로 응답하지 않았습니다. (재시도/처리 필요)")
        print(response)
        raise ValueError("Invalid JSON from LLM response")

    state.story_data = story_data
    state.step = "first_encounter_question"

    # 첫 장면 안내
    background = story_data.get("story_details", {}).get("background", "")
    obj = story_data.get("objective", "")
    state.message = background + "\n" + obj + "\n" + "행운을 빕니다!\n"
    return state


# ---------- [ 첫 번째 NPC: Question 노드 / Followup 노드 ] ----------

def first_encounter_question(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][0]
    intro_story = state.story_data.get("story_details", {}).get("intro", "")
    full_story = state.story_data.get("world_description", "")

    prompt_q = f"""
    당신은 이 미로 속에서 플레이어가 만나는 첫 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    당신의 말투는 : {npc.get('personality')} 입니다.
    먼저 {full_story} 내용을 기반으로 {intro_story}를 플레이어에게 소설 책 처럼 설명해주고, 이어서
    해당 세계관과 이어지며 정답이 객관적으로 확실한 3지선다 퀴즈를 1개 내주세요
    """
    question_text = llm.invoke(prompt_q).content
    state.message = question_text
    state.step = "first_encounter_followup"
    return state

def first_encounter_followup(state: MazeState) -> MazeState:
    player_input = input("> ")
    state.player_answer = player_input.strip()

    npc = state.story_data["npcs"][0]
    player_answer = state.player_answer
    full_story = state.story_data.get("world_description", "")
    message = state.message

    prompt_follow = f"""
    당신은 NPC '{npc['name']}' 입니다. 당신의 말투는 : {npc.get('personality')} 입니다.
    플레이어가 '{player_answer}' 라고 답했습니다.
    이 선택이 {message}에서의 퀴즈 정답이면 정답이라고 말하고, {full_story} 와 관련되게 미로 진행에 필요한 힌트를 하나 주고 대화를 끝내 주세요.
    선택이 틀리면 틀렸다고 말하고 힌트를 주지 마세요.
    """
    follow_text = llm.invoke(prompt_follow).content

    # history 추가
    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "second_encounter_question"
    state.message = follow_text
    return state


# ---------- [ 두 번째 NPC: Question / Followup ] ----------

def second_encounter_question(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][1]
    middle_story = state.story_data.get("story_details", {}).get("middle", "")
    history = state.history
    full_story = state.story_data.get("world_description", "")

    prompt_q = f"""
    당신은 이 미로 속에서 플레이어가 만나는 두번째 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    당신의 말투는 : {npc.get('personality')} 입니다.
    당신이 전에 냈던 퀴즈와 대답이 {history}에 들어 있습니다.
    먼저 {history}에서 플레이어가 선택한 내용을 언급하며, 
    {full_story} 내용을 기반으로 {middle_story}를 플레이어에게 소설 책 처럼 설명해주고, 이어서
    해당 세계관과 이어지며 정답이 객관적으로 확실한 3지선다 퀴즈를 1개 내주세요
    """
    question_text = llm.invoke(prompt_q).content
    state.step = "second_encounter_followup"
    state.message = question_text
    return state

def second_encounter_followup(state: MazeState) -> MazeState:
    player_input = input("> ")
    state.player_answer = player_input.strip()

    npc = state.story_data["npcs"][1]
    player_answer = state.player_answer
    full_story = state.story_data.get("world_description", "")
    message = state.message

    prompt_follow = f"""
    당신은 NPC '{npc['name']}' 입니다. 당신의 말투는 : {npc.get('personality')} 입니다.
    플레이어가 '{player_answer}' 라고 답했습니다.
    이 선택이 {message}에서의 퀴즈 정답이면 정답이라고 말하고, {full_story} 와 관련되게 미로 진행에 필요한 힌트를 하나 주고 대화를 끝내 주세요.
    선택이 틀리면 틀렸다고 말하고 힌트를 주지 마세요.
    """
    follow_text = llm.invoke(prompt_follow).content
    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "third_encounter_question"
    state.message = follow_text
    return state


# ---------- [ 세 번째 NPC: Question / Followup ] ----------

def third_encounter_question(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][2]
    final_story = state.story_data.get("story_details", {}).get("final", "")
    history = state.history
    full_story = state.story_data.get("world_description", "")

    prompt_q = f"""
    당신은 이 미로 속에서 플레이어가 만나는 마지막 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    당신의 말투는 : {npc.get('personality')} 입니다.
    당신이 전에 냈던 퀴즈와 대답이 {history}에 들어 있습니다.
    먼저 {history}에서 플레이어가 선택한 내용을 언급하며, 
    {full_story} 내용을 기반으로 {final_story}를 플레이어에게 소설 책 처럼 설명해주고, 이어서
    해당 세계관과 이어지며 정답이 객관적으로 확실한 3지선다 퀴즈를 1개 내주세요
    """
    question_text = llm.invoke(prompt_q).content
    state.step = "third_encounter_followup"
    state.message = question_text
    return state

def third_encounter_followup(state: MazeState) -> MazeState:
    player_input = input("> ")
    state.player_answer = player_input.strip()

    npc = state.story_data["npcs"][2]
    player_answer = state.player_answer
    full_story = state.story_data.get("world_description", "")
    message = state.message

    prompt_follow = f"""
    당신은 NPC '{npc['name']}' 입니다. 당신의 말투는 : {npc.get('personality')} 입니다.
    플레이어가 '{player_answer}' 라고 답했습니다.
    이 선택이 {message}에서의 퀴즈 정답이면 정답이라고 말하고, {full_story} 와 관련되게 미로 진행에 마지막으로 필요한 힌트를 하나 주고 대화를 끝내 주세요.
    선택이 틀리면 틀렸다고 말하고 힌트를 주지 마세요.
    """
    follow_text = llm.invoke(prompt_follow).content
    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "final_choice_question"
    state.message = follow_text
    return state


# ---------- [ 결말 ] ----------
def end_game(state: MazeState) -> MazeState:
    result_story = state.story_data.get("story_details", {}).get("result", "")
    full_story = state.story_data.get("world_description", "")
    history = state.history

    prompt = f"""
    미로의 마지막 장소에 도착했습니다.
    스토리의 최종 결말인 {result_story}를 플레이어에게 설명하고,
    이 {history} 중 플레이어의 선택들로 인해 스토리 최종 결말이 나왔다는 점도 같이 소설의 마지막 처럼 설명해주세요
    참고로 {result_story}는 {full_story}에서 벗어난 내용이 아니어야 합니다.
    """
    result_text = llm.invoke(prompt).content
    state.message = result_text
    return state

# -------------------------
# 4) 실행
# -------------------------
def main():
    setting = input("미로의 장소를 입력하세요 (예: '스위스 산골짜기'):\n> ")
    atmosphere = input("미로의 분위기를 입력하세요 (예: '묘하고 신비로움'):\n> ")

    # Pydantic 모델 생성
    state = MazeState(setting=setting, atmosphere=atmosphere)

    state = generate_story(state)
    print(state.message, flush=True)
    state = first_encounter_question(state)
    print(state.message, flush=True)
    state = first_encounter_followup(state)
    print(state.message, flush=True)
    state = second_encounter_question(state)
    print(state.message, flush=True)
    state = second_encounter_followup(state)
    print(state.message, flush=True)
    state = third_encounter_question(state)
    print(state.message, flush=True)
    state = third_encounter_followup(state)
    print(state.message, flush=True)
    state = end_game(state)
    print(state.message, flush=True)


if __name__ == "__main__":
    main()
