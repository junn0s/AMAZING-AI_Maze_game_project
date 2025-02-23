from dotenv import load_dotenv
load_dotenv()

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
    """
    1) start 노드
    - 장소/분위기 정보를 바탕으로, 세계관/목표/NPC들을 JSON 형식으로 생성.
    - 그 내용을 state.story_data에 저장
    - 다음 노드: first_encounter_question
    """
    prompt = f"""
    당신은 텍스트 기반 미로 탐험 게임의 스토리 마스터입니다.
    플레이어가 미로의 장소로 '{state.setting}', 분위기로 '{state.atmosphere}'를 입력했습니다.

    이 설정을 기반으로 흥미로운 미로 탐험 스토리를 만들어 주세요.

    출력은 반드시 **순수 JSON** 형태여야 합니다. (추가 설명 X)
    예시:
    {{
      "world_description": "string",
      "objective": "string",
      "npcs": [
        {{"name": "string", "role": "string"}},
        ...
      ]
    }}
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
    obj = story_data.get("objective", "")
    state.message = (
        f"게임이 시작되었습니다!\n"
        f"장소: {state.setting}\n"
        f"분위기: {state.atmosphere}\n"
        f"미로 세계 설명: {desc}\n"
        f"당신의 목표: {obj}\n"
        "앞으로 나아가시겠습니까?"
    )
    return state


# ---------- [ 첫 번째 NPC: Question 노드 / Followup 노드 ] ----------

def first_encounter_question(state: MazeState) -> MazeState:
    """
    2) 첫 번째 NPC '질문' 노드
    - NPC가 객관식 퀴즈를 낸다.
    - 플레이어 답변을 state.player_answer에 저장
    - 다음 노드: first_encounter_followup
    """
    npc = state.story_data["npcs"][0]

    prompt_q = f"""
    당신은 미로 속에서 플레이어가 만나는 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    플레이어와 자연스러운 대화를 시작하며,
    현재 미로 세계관과 스토리라인과 관련된 객관식 퀴즈를 4지선다(A, B, C, D)로 내주세요.
    마지막에 "당신의 선택은?"이라고 물어보세요.
    """
    question_text = llm.invoke(prompt_q).content
    print(question_text)  # 화면에 출력

    # 플레이어 입력
    player_input = input("> ")
    state.player_answer = player_input.strip()
    state.step = "first_encounter_followup"
    # 메시지는 굳이 없어도 되지만, 깔끔히 정리
    state.message = f"(당신의 답변: {player_input})"
    return state

def first_encounter_followup(state: MazeState) -> MazeState:
    """
    3) 첫 번째 NPC '후속 대화' 노드
    - player_answer를 참조하여 후속 대화를 생성
    - 다음 노드: second_encounter_question
    """
    npc = state.story_data["npcs"][0]
    player_answer = state.player_answer

    prompt_follow = f"""
    당신은 NPC '{npc['name']}' 입니다.
    플레이어가 '{player_answer}' 라고 답했습니다.
    이 선택이 스토리와 어떻게 연관되는지, 앞으로의 진행에 어떤 영향을 줄 수 있는지
    자연스럽게 후속 대화를 이어가 주세요.
    """
    follow_text = llm.invoke(prompt_follow).content
    print(follow_text)

    # history 추가
    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "second_encounter_question"
    state.message = "첫 번째 NPC 대화가 완료되었습니다!"
    return state


# ---------- [ 두 번째 NPC: Question / Followup ] ----------

def second_encounter_question(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][1]

    prompt_q = f"""
    당신은 미로 속에서 플레이어가 만나는 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    두 번째 질문을 4지선다로 낸 뒤, 마지막에 "당신의 선택은?"이라고 물어보세요.
    """
    question_text = llm.invoke(prompt_q).content
    print(question_text)

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
    이 선택이 스토리 전개에 어떤 의미가 있는지,
    플레이어에게 어떤 힌트를 줄 수 있는지 자연스럽게 설명해 주세요.
    """
    follow_text = llm.invoke(prompt_follow).content
    print(follow_text)

    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "third_encounter_question"
    state.message = "두 번째 NPC 대화가 완료되었습니다!"
    return state


# ---------- [ 세 번째 NPC: Question / Followup ] ----------

def third_encounter_question(state: MazeState) -> MazeState:
    npc = state.story_data["npcs"][2]

    prompt_q = f"""
    당신은 미로 속에서 플레이어가 만나는 마지막 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    세 번째 질문(4지선다)과 함께, 마지막에는 "당신의 선택은?"라고 물어보세요.
    """
    question_text = llm.invoke(prompt_q).content
    print(question_text)

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
    플레이어가 '{player_answer}'라고 답했습니다.
    이 답변을 바탕으로, 미로의 깊은 비밀과 관련된 마지막 힌트를 주세요.
    """
    follow_text = llm.invoke(prompt_follow).content
    print(follow_text)

    state.history.append(f"플레이어: {player_answer}")
    state.history.append(f"{npc['name']}: {follow_text}")

    state.step = "final_choice_question"
    state.message = "세 번째 NPC 대화가 완료되었습니다!"
    return state

# ---------- [ 최종 선택: Question / Followup ] ----------

def final_choice_question(state: MazeState) -> MazeState:
    prompt = f"""
    미로의 마지막 장소에 도착했습니다.
    당신의 목표는 '{state.story_data.get('objective', '???')}' 입니다.

    이제 중요한 선택이 필요합니다.
    1) 미로에서 탈출하여 목표를 달성한다.
    2) 미로에 남아서 더 깊이 탐구한다.
    3) 다른 길을 찾아 또 다른 보물을 노린다.
    4) ??? (자유롭게 추가 가능)

    어떤 선택을 하시겠습니까? (1/2/3/4)
    """
    print(prompt)
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
    setting = input("미로의 장소를 입력하세요 (예: '으슥한 덩굴 미로'):\n> ")
    atmosphere = input("미로의 분위기를 입력하세요 (예: '해리포터 같은 어두운 판타지'):\n> ")

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

    # 마지막 end 노드 (결말)
    raw_data = game_runner.invoke(state)
    state = MazeState.model_validate(raw_data)
    print("\n[System Message] " + state.message)

if __name__ == "__main__":
    main()