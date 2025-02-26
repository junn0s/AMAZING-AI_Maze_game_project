from dotenv import load_dotenv
load_dotenv()

import time
import json
from typing import List, Optional

# (Deprecation 경고를 없애려면):
# from langchain_community.chat_models import ChatOpenAI
# from langchain_community.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

from langgraph.graph import StateGraph

# pydantic (2.x 기준)
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
    model="gpt-4o-mini",   # 실제 OpenAI 모델을 쓰려면 "gpt-3.5-turbo" 등 사용
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
    셰계관을 만들고 아래 예시처럼 JSON으로 출력해야 해.
    조건 : 출력은 반드시 순수 JSON 형태여야 하고, 삼중 백틱(```)이나 다른 코드 블록 문법은 절대 사용하지 마.
    예시 :
    {{
        "world_description": "세계관 및 스토리 전체 설명!!, 실제 플레이어한테 게임 관리자가 설명하듯이 해줘.존댓말로 해줘",
        "objective": "미로탈출 게임의 세계관 기반 궁극적 목표, 이것도 플레이어한테 게임 관리자가 설명하듯이 존댓말로 해줘",
        "story_details": {{
            "intro": "게임 시작 시의 스토리와 상황 설명을 게임 관리자가 플레이어한테 소설의 첫 부분에서 이야기하듯이 존댓말로 작성, ",
            "middle": "게임 진행 중 발생하는 주요 사건 및 전개를 게임 관리자가 플레이어한테 소설의 첫 부분에서 이야기하듯이 존댓말로 작성",
            "final": "게임 결말에 이르는 과정과 결말의 분위기를 게임 관리자가 플레이어한테 소설의 첫 부분에서 이야기하듯이 존댓말로 작성"
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
    desc = story_data.get("world_description", "")
    overview = story_data.get("story_details", {}).get("intro", "")
    obj = story_data.get("objective", "")

    print(overview)
    time.sleep(1)
    print(obj)
    print("행운을 빕니다!\n")

    return state


# ---------- [ 첫 번째 NPC: Question 노드 / Followup 노드 ] ----------

def first_encounter_question(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][0]
    intro_story = state.story_data.get("story_details", {}).get("intro", "")

    prompt_q = f"""
    당신은 이 미로 속에서 플레이어가 만나는 첫 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    - 말투: {npc.get('personality')}
    플레이어와 자연스러운 대화를 해당 말투로 시작하되, 방금까지의 {intro_story}와 유사한 스토리를 처음에 무조건 언급하며 이어가세요.
    그리고 게임 진행과는 관계없지만 분위기는 관계있는 3지선다 질문을 1개 내줘
    퀴즈 내용은 흥미로워야 해
    """
    question_text = llm.invoke(prompt_q).content
    print(question_text)  # 화면에 출력
    time.sleep(1)

    # 플레이어 입력
    player_input = input("> ")
    state.player_answer = player_input.strip()
    state.step = "first_encounter_followup"
    # 메시지는 굳이 없어도 되지만, 깔끔히 정리
    state.message = f"(답변: {player_input})"
    return state

def first_encounter_followup(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][0]
    player_answer = state.player_answer

    prompt_follow = f"""
    당신은 NPC '{npc['name']}' 입니다.
    플레이어가 '{player_answer}' 라고 답했습니다.
    이 선택이 정답이면 정답이라고 말하고, 미로 진행에 필요한 힌트를 하나 주고 대화를 끝내 주세요.
    선택이 틀리면 틀렸다고 말하고 힌트를 주지 마. 말투는 해당 npc 말투 그대로 해줘
    """
    follow_text = llm.invoke(prompt_follow).content
    print(follow_text)
    time.sleep(1)

    # history 추가
    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "second_encounter_question"
    state.message = "첫 번째 NPC 대화가 완료되었습니다!"
    return state


# ---------- [ 두 번째 NPC: Question / Followup ] ----------

def second_encounter_question(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][1]
    middle_story = state.story_data.get("story_details", {}).get("middle", "")

    prompt_q = f"""
    당신은 이 미로 속에서 플레이어가 만나는 두번째 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    - 말투: {npc.get('personality')}
    플레이어와 자연스러운 대화를 해당 말투로 시작하되, 방금까지의 {middle_story}와 유사한 스토리를 처음에 무조건 언급하며 이어가세요.
    그리고 게임 진행과는 관계없지만 분위기는 관계있는 3지선다 질문을 1개 내줘
    퀴즈 내용은 흥미로워야 해
    """
    question_text = llm.invoke(prompt_q).content
    print(question_text)
    time.sleep(1)

    player_input = input("> ")
    state.player_answer = player_input.strip()
    state.step = "second_encounter_followup"
    state.message = f"(당신의 답변: {player_input})"
    return state

def second_encounter_followup(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][1]
    player_answer = state.player_answer

    prompt_follow = f"""
    당신은 NPC '{npc['name']}' 입니다.
    플레이어가 '{player_answer}' 라고 답했습니다.
    이 선택이 정답이면 정답이라고 말하고, 미로 진행에 필요한 힌트를 하나 주고 대화를 끝내 주세요.
    선택이 틀리면 틀렸다고 말하고 힌트를 주지 마. 말투는 해당 npc 말투 그대로 해줘
    """
    follow_text = llm.invoke(prompt_follow).content
    print(follow_text)
    time.sleep(1)

    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "third_encounter_question"
    state.message = "두 번째 NPC 대화가 완료되었습니다!"
    return state


# ---------- [ 세 번째 NPC: Question / Followup ] ----------

def third_encounter_question(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][2]
    final_story = state.story_data.get("story_details", {}).get("final", "")
    prompt_q = f"""
    당신은 이 미로 속에서 플레이어가 만나는 두번째 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    - 말투: {npc.get('personality')}
    플레이어와 자연스러운 대화를 해당 말투로 시작하되, 방금까지의 {final_story}와 유사한 스토리를 처음에 무조건 언급하며 이어가세요.
    그리고 게임 진행과는 관계없지만 분위기는 관계있는 3지선다 질문을 1개 내줘
    퀴즈 내용은 흥미로워야 해
    """
    question_text = llm.invoke(prompt_q).content
    print(question_text)
    time.sleep(1)

    player_input = input("> ")
    state.player_answer = player_input.strip()
    state.step = "third_encounter_followup"
    state.message = f"(당신의 답변: {player_input})"
    return state

def third_encounter_followup(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][2]
    player_answer = state.player_answer

    prompt_follow = f"""
    당신은 NPC '{npc['name']}' 입니다.
    플레이어가 '{player_answer}' 라고 답했습니다.
    이 선택이 정답이면 정답이라고 말하고, 미로 진행에 필요한 힌트를 하나 주고 대화를 끝내 주세요.
    선택이 틀리면 틀렸다고 말하고 힌트를 주지 마. 말투는 해당 npc 말투 그대로 해줘
    """
    follow_text = llm.invoke(prompt_follow).content
    print(follow_text)
    time.sleep(1)

    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "final_choice_question"
    state.message = "세 번째 NPC 대화가 완료되었습니다!"
    return state

# ---------- [ 최종 선택: Question / Followup ] ----------

def final_choice_question(state: MazeState) -> MazeState:
    prompt = f"""
    미로의 마지막 장소에 도착했습니다.
    이제 중요한 선택이 필요합니다.
    1) 미로에서 탈출하여 목표를 달성한다.
    2) 미로에 남아서 더 깊이 탐구한다.


    어떤 선택을 하시겠습니까? (1/2/)
    """
    print(prompt)
    time.sleep(1)
    player_input = input("> ")
    state.player_answer = player_input.strip()
    state.step = "final_choice_followup"
    state.message = f"(당신의 최종 선택: {player_input})"
    return state

def final_choice_followup(state: MazeState) -> MazeState:
    player_answer = state.player_answer
    prompt_follow = f"""
    당신은 게임의 내레이터 역할입니다.
    플레이어가 '{player_answer}'를 선택했습니다.
    이 선택이 미로 탈출에 어떤 영향을 미치고, 스토리가 어떻게 마무리될지
    자연스럽게 설명해 주세요.
    """
    response_follow = llm.invoke(prompt_follow).content
    print(response_follow)
    time.sleep(1)

    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"내레이터: {response_follow}")

    state.step = "end"
    state.message = "최종 선택에 대한 내레이터의 대화가 끝났습니다."
    return state

# ---------- [ 결말 ] ----------
def end_game(state: MazeState) -> MazeState:
    """
    'end' 노드
    - 플레이어의 선택/역사에 따라 결말을 출력
    - 여기서는 '탈출'이라는 단어가 들어있는지 여부로 분기
    """
    if any("탈출" in h for h in state.history):
        ending = f"당신은 '{state.story_data.get('objective','???')}'을(를) 손에 넣고 미로를 빠져나왔습니다.\n" \
                 "현실로 돌아왔지만, 미로의 기억은 서서히 희미해집니다.\n" \
                 "가끔 꿈속에서 이곳의 환영이 떠오릅니다..."
    else:
        ending = f"당신은 미로에 남아 '{state.story_data.get('objective','???')}'의 비밀을 더 파고들기 시작했습니다.\n" \
                 "아직 밝혀지지 않은 무언가가, 이 미로 어딘가에서 당신을 기다립니다...\n" \
                 "이제 당신은 이곳의 일부가 되었습니다."

    print("\n--- 결말 ---")
    print(ending)
    time.sleep(1)

    state.message = "게임이 종료되었습니다. 감사합니다!"
    return state

# -------------------------
# 4) 그래프 구성
# -------------------------
story_graph = StateGraph(MazeState)

story_graph.add_node("start", generate_story)

story_graph.add_node("first_encounter_question", first_encounter_question)
story_graph.add_node("first_encounter_followup", first_encounter_followup)

story_graph.add_node("second_encounter_question", second_encounter_question)
story_graph.add_node("second_encounter_followup", second_encounter_followup)

story_graph.add_node("third_encounter_question", third_encounter_question)
story_graph.add_node("third_encounter_followup", third_encounter_followup)

story_graph.add_node("final_choice_question", final_choice_question)
story_graph.add_node("final_choice_followup", final_choice_followup)

story_graph.add_node("end", end_game)

story_graph.set_entry_point("start")

# 흐름 연결
story_graph.add_edge("start", "first_encounter_question")
story_graph.add_edge("first_encounter_question", "first_encounter_followup")
story_graph.add_edge("first_encounter_followup", "second_encounter_question")
story_graph.add_edge("second_encounter_question", "second_encounter_followup")
story_graph.add_edge("second_encounter_followup", "third_encounter_question")
story_graph.add_edge("third_encounter_question", "third_encounter_followup")
story_graph.add_edge("third_encounter_followup", "final_choice_question")
story_graph.add_edge("final_choice_question", "final_choice_followup")
story_graph.add_edge("final_choice_followup", "end")

game_runner = story_graph.compile()

# -------------------------
# 5) 실제 실행 흐름
# -------------------------
def main():
    setting = input("미로의 장소를 입력하세요 (예: '고대 성 지하 동굴'):\n> ")
    atmosphere = input("미로의 분위기를 입력하세요 (예: '어둡고 신비로움'):\n> ")

    # Pydantic 모델 생성
    state = MazeState(setting=setting, atmosphere=atmosphere)

    while True:
        # AddableValuesDict → MazeState 변환
        raw_data = game_runner.invoke(state)
        state = MazeState.model_validate(raw_data)

        # 'end' 단계면 종료
        if state.step == "end":
            break

        # 메시지 출력(필요 시)
        if state.message:
            print("\n[System Message] " + state.message)
            time.sleep(1)

    # 마지막 end 노드 (결말)
    raw_data = game_runner.invoke(state)
    state = MazeState.model_validate(raw_data)
    print("\n[System Message] " + state.message)

if __name__ == "__main__":
    main()