# env 파일 읽기
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph
import json

# GPT 모델 로드
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# 대화 메모리 (이전 대화 저장)
memory = ConversationBufferMemory(memory_key="history", return_messages=True)

# 게임 상태 관리
class GameState:
    def __init__(self, setting, atmosphere):
        self.setting = setting  # 사용자가 입력한 장소
        self.atmosphere = atmosphere  # 사용자가 입력한 분위기
        self.step = "start"
        self.inventory = []
        self.history = []
        self.location = "미로 입구"
        self.story_data = None  # GPT가 생성한 스토리 데이터 저장


# 1. GPT를 사용해 세계관, 스토리, NPC 자동 생성
def generate_story(state):
    prompt = f"""
    당신은 텍스트 기반 미로 탐험 게임의 스토리 마스터입니다.
    플레이어가 미로의 장소로 '{state.setting}', 분위기로 '{state.atmosphere}'을(를) 입력했습니다.

    이 설정을 기반으로 흥미로운 미로 탐험 스토리를 만들어 주세요.
    - 미로의 세계관을 3~4문장으로 설명
    - 미로에서 플레이어가 찾아야 할 중요한 목표 (예: 마법의 보석, 고대 문서 등)
    - 최소 3명의 NPC를 만들고, 각 NPC의 역할을 설명 (NPC는 미로에 있는 안내자, 적대자, 함정을 줄 수도 있음)
    - 플레이어가 만날 NPC들의 순서를 정리

    JSON 형식으로 출력해주세요.
    """
    
    response = llm.invoke(prompt).content
    story_data = json.loads(response)
    state.story_data = story_data  # 스토리 저장

    return {
        "message": f"게임이 시작되었습니다! {story_data['world_description']}\n"
                   f"당신의 목표는 '{story_data['objective']}' 입니다.\n"
                   "앞으로 나아가시겠습니까?",
        "next": "first_encounter"
    }

# NPC와 대화하며 객관식 퀴즈를 진행하는 함수 (공통 로직)
def npc_conversation_with_quiz(state, npc):
    # 1. NPC의 초기 대화 및 퀴즈 출제 (객관식 4지선다)
    prompt_initial = f"""
    당신은 미로 속에서 플레이어가 만나는 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    플레이어와 자연스러운 대화를 시작하며, 현재 미로 세계관과 스토리라인과 관련된 객관식 퀴즈를 출제해 주세요.
    문제는 4개의 선택지(A, B, C, D)를 포함하고, 대화 형식으로 제시해 주세요.
    대화의 마지막에는 반드시 "당신의 선택은 무엇입니까?"라는 질문을 던지세요.
    """
    response_initial = llm.invoke(prompt_initial).content
    print(response_initial)
    # 플레이어 입력 받기
    player_input = input("> ")
    state.history.append(f"플레이어: {player_input}")
    
    # 2. NPC의 후속 대화: 플레이어의 선택에 따른 피드백 대화 생성
    prompt_followup = f"""
    당신은 NPC '{npc['name']}' 입니다.
    플레이어가 객관식 퀴즈에 대해 '{player_input}'라고 응답했습니다.
    이 선택이 스토리와 어떻게 연관되는지, 그리고 앞으로의 진행에 어떤 영향을 줄 수 있는지에 대해 자연스러운 대화 형식의 피드백을 작성해 주세요.
    """
    response_followup = llm.invoke(prompt_followup).content
    state.history.append(f"{npc['name']}: {response_followup}")
    
    # 두 대화 결과를 합쳐 반환 (출력 시 구분)
    combined_response = response_initial + "\n" + response_followup
    return combined_response

# 2. 동적으로 생성된 첫 번째 NPC (스토리 초반)
def first_encounter(state):
    npc = state.story_data["npcs"][0]  # 첫 번째 NPC 데이터
    conversation = npc_conversation_with_quiz(state, npc)
    return {"message": conversation, "next": "second_encounter"}

# 3. 두 번째 NPC (스토리 중반)
def second_encounter(state):
    npc = state.story_data["npcs"][1]  # 두 번째 NPC 데이터
    conversation = npc_conversation_with_quiz(state, npc)
    return {"message": conversation, "next": "third_encounter"}

# 4. 세 번째 NPC (스토리 후반)
def third_encounter(state):
    npc = state.story_data["npcs"][2]  # 세 번째 NPC 데이터
    # 이 NPC는 후속 대화에서 플레이어에게 중요한 결정을 유도하는 대사를 포함합니다.
    prompt_initial = f"""
    당신은 미로 속에서 플레이어가 만나는 마지막 NPC '{npc['name']}' (역할: {npc['role']}) 입니다.
    지금까지의 스토리와 미로 세계관을 종합하여, 플레이어에게 중요한 결정을 내리도록 유도하는 객관식 퀴즈(4지선다)를 포함한 대화를 시작해 주세요.
    대화의 마지막에는 "당신의 선택은 무엇입니까?"라는 질문을 반드시 던지세요.
    """
    response_initial = llm.invoke(prompt_initial).content
    print(response_initial)
    player_input = input("> ")
    state.history.append(f"플레이어: {player_input}")
    
    prompt_followup = f"""
    당신은 NPC '{npc['name']}' 입니다.
    플레이어가 '{player_input}'라고 응답했습니다.
    이 선택이 미로 탈출 혹은 미로의 비밀 탐구와 어떻게 연결되는지에 대해 자연스러운 대화 형식의 피드백을 작성해 주세요.
    """
    response_followup = llm.invoke(prompt_followup).content
    state.history.append(f"{npc['name']}: {response_followup}")
    
    conversation = response_initial + "\n" + response_followup
    return {"message": conversation, "next": "final_choice"}

# 5. 최종 선택 (출구 또는 미로에 남기)
def final_choice(state):
    prompt = f"""
    미로의 마지막 장소에 도착했습니다. 플레이어는 이제 '{state.story_data['objective']}'을(를) 손에 넣을 수 있습니다.
    
    하지만 이 순간, 중요한 선택이 필요합니다.
    1. '{state.story_data['objective']}'을(를) 가지고 미로에서 탈출한다.
    2. 미로에 남아 이곳의 진실을 더 깊이 탐구한다.
    
    이 선택에 대해 객관식 퀴즈 형식의 질문과 4개의 선택지를 포함하여 플레이어에게 대화 형식으로 제시해 주세요.
    """
    response = llm.invoke(prompt).content
    print(response)
    player_input = input("> ")
    state.history.append(f"플레이어: {player_input}")
    
    # 플레이어의 선택에 따른 후속 피드백 생성
    prompt_followup = f"""
    당신은 게임의 내레이터 역할을 맡은 NPC입니다.
    플레이어가 '{player_input}'라고 선택했습니다.
    이 선택이 미로 탈출에 미치는 영향을 스토리와 연계하여 자연스러운 대화 형식으로 설명해 주세요.
    """
    response_followup = llm.invoke(prompt_followup).content
    state.history.append(f"내레이터: {response_followup}")
    
    combined_response = response + "\n" + response_followup
    return {"message": combined_response, "next": "end"}

# 6. 결말 (플레이어의 선택에 따라 다름)
def end_game(state):
    if any("탈출" in entry for entry in state.history):
        ending = f"당신은 '{state.story_data['objective']}'을(를) 손에 넣고 미로를 빠져나왔습니다.\n"\
                 f"그러나 현실에 돌아온 후, 미로의 기억은 희미해져 갑니다...\n"\
                 "가끔 꿈속에서 미로의 목소리가 들려옵니다."
    else:
        ending = f"당신은 '{state.story_data['objective']}'을(를) 뒤로 하고 미로에 남았습니다.\n"\
                 f"여기에는 아직 밝혀지지 않은 더 깊은 비밀이 숨어 있을 것입니다...\n"\
                 "이제 당신은 이 미로의 일부가 되었습니다."
    return {"message": ending, "next": None}

# LangGraph를 활용한 스토리 그래프 구축
story_graph = StateGraph(GameState)

story_graph.add_node("start", generate_story)
story_graph.add_node("first_encounter", first_encounter)
story_graph.add_node("second_encounter", second_encounter)
story_graph.add_node("third_encounter", third_encounter)
story_graph.add_node("final_choice", final_choice)
story_graph.add_node("end", end_game)

# 연결 설정 (스토리 진행 흐름)
story_graph.set_entry_point("start")
story_graph.add_edge("start", "first_encounter")
story_graph.add_edge("first_encounter", "second_encounter")
story_graph.add_edge("second_encounter", "third_encounter")
story_graph.add_edge("third_encounter", "final_choice")
story_graph.add_edge("final_choice", "end")

# 게임 실행
setting = input("미로의 장소를 입력하세요 (예: '으슥한 덩굴 미로'):\n> ")
atmosphere = input("미로의 분위기를 입력하세요 (예: '해리포터 같은 어두운 판타지'):\n> ")

state = GameState(setting, atmosphere)
game_runner = story_graph.compile()

while state.step != "end":
    result = game_runner.invoke(state)
    print("\n" + result["message"])
    # 플레이어의 입력은 각 노드 내에서 이미 처리되고, state.history에 기록됩니다.
    state.step = result["next"]

# 마지막 결말 출력
final = game_runner.invoke(state)
print("\n" + final["message"])