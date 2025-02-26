from dotenv import load_dotenv
load_dotenv()

import os
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

# 사용자 및 게임 상태 모델 정의
class GameState(BaseModel):
    job: str
    name: str
    place: str
    atmosphere: str
    story: dict = Field(default_factory=dict)
    goal: str = ""
    npcs: list = Field(default_factory=list)
    inventory: list = Field(default_factory=list)
    final_result: str = ""

# LLM 설정 (모델과 온도는 필요에 따라 조정)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

# 1. 스토리 생성 체인
story_prompt = PromptTemplate.from_template(
    "사용자의 직업은 {job}, 이름은 {name}, 원하는 장소는 {place}, 원하는 분위기는 {atmosphere}입니다. "
    "이 정보를 바탕으로 미로 탈출을 목표로 하는 스토리를 초반, 중반, 후반으로 나누어 "
    "순수 JSON 형식으로 출력해 주세요.\n"
    "예시: {{ \"beginning\": \"초반 내용\", \"middle\": \"중반 내용\", \"end\": \"후반 내용\" }}"
)
story_chain = LLMChain(llm=llm, prompt=story_prompt, output_key="story")

# 2. 목표 생성 체인
goal_prompt = PromptTemplate.from_template(
    "사용자 정보와 스토리 {story}를 참고하여, 플레이어가 미로를 탈출하기 위한 목표를 생성해 주세요."
)
goal_chain = LLMChain(llm=llm, prompt=goal_prompt, output_key="goal")

# 3. NPC 생성 체인 (3명의 NPC 생성)
npc_prompt = PromptTemplate.from_template(
    "스토리 {story}와 목표 {goal}를 기반으로, 말투와 특징이 모두 다른 NPC 3명을 순수 JSON 형식으로 생성해 주세요. "
    "각 NPC는 'name', 'style', 'description' 키를 포함해야 합니다.\n"
    "예시: {{ \"npcs\": [ {{ \"name\": \"NPC1\", \"style\": \"친절한\", \"description\": \"설명1\" }}, "
    "         {{ \"name\": \"NPC2\", \"style\": \"냉정한\", \"description\": \"설명2\" }}, "
    "         {{ \"name\": \"NPC3\", \"style\": \"유머러스한\", \"description\": \"설명3\" }} ] }}"
)
npc_chain = LLMChain(llm=llm, prompt=npc_prompt, output_key="npcs")

# 4. NPC 대화/퀴즈 체인 (각 NPC별 진행)
quiz_prompt = PromptTemplate.from_template(
    "NPC {npc_name} (특징: {style})로서, 스토리 초반: {beginning}, 중반: {middle}, 후반: {end} 내용을 "
    "자연스럽게 설명한 뒤, 아래와 같이 관련 퀴즈를 출제해 주세요.\n\n"
    "예시:\n"
    "퀴즈: '나는 작가들의 친구이자, 때로는 악몽이기도 해. 내 앞에서는 누구도 거짓을 말할 수 없지. "
    "나를 가진 사람은 이야기를 남기고, 잃은 사람은 길을 잃지. 나는 무엇일까?'\n\n"
    "선택지:\n"
    "1️⃣ 펜\n"
    "2️⃣ 거울\n"
    "3️⃣ 촛불\n"
    "정답은 1️⃣ (펜) 입니다.\n\n"
    "출력은 순수 JSON 형식으로 해주세요. 예시: {{ \"quiz\": \"문제 텍스트\", \"options\": [\"펜\", \"거울\", \"촛불\"], \"answer\": \"펜\" }}"
)
quiz_chain = LLMChain(llm=llm, prompt=quiz_prompt, output_key="quiz")

# 5. 정답 평가 및 아이템 지급 체인
feedback_prompt = PromptTemplate.from_template(
    "플레이어의 정답은 {player_answer}입니다. 정답은 {correct_answer} 입니다. "
    "정답이면 '맞았습니다'와 함께 아이템 '특별한 열쇠'를 지급하는 메시지를, 틀리면 '틀렸습니다'라는 메시지를 출력해 주세요."
)
feedback_chain = LLMChain(llm=llm, prompt=feedback_prompt, output_key="feedback")

# 6. 최종 결말 체인
final_prompt = PromptTemplate.from_template(
    "플레이어가 미로 출구에 도착했습니다. 지금까지의 진행 상태와 아이템 {inventory}를 고려하여 최종 결말을 출력해 주세요."
)
final_chain = LLMChain(llm=llm, prompt=final_prompt, output_key="final_result")

# --- 게임 진행 흐름 ---
def run_game():
    # 1. 사용자 입력 받기
    job = input("직업을 입력하세요: ")
    name = input("이름을 입력하세요: ")
    place = input("원하는 장소를 입력하세요: ")
    atmosphere = input("원하는 분위기를 입력하세요: ")

    state = GameState(job=job, name=name, place=place, atmosphere=atmosphere)

    # 2. 스토리 생성
    story_output = story_chain.invoke({
        "job": state.job,
        "name": state.name,
        "place": state.place,
        "atmosphere": state.atmosphere
    })
    # 출력값이 JSON 문자열이라면 파싱
    story_str = story_output["story"]
    try:
        parsed_story = json.loads(story_str)
        state.story = parsed_story
    except Exception as e:
        print("스토리 출력 파싱 중 에러 발생:", e)
        state.story = {}

    # 3. 목표 생성
    goal_output = goal_chain.invoke({"story": state.story})
    state.goal = goal_output["goal"]

    # 4. NPC 생성 (출력이 JSON 문자열로 나온다면 파싱)
    npc_output = npc_chain.invoke({"story": state.story, "goal": state.goal})
    npc_str = npc_output["npcs"]
    try:
        parsed_npc = json.loads(npc_str)
        # parsed_npc가 딕셔너리 형태로 나온 경우, 예시에서처럼 {"npcs": [...]}
        state.npcs = parsed_npc.get("npcs", [])
    except Exception as e:
        print("NPC 출력 파싱 중 에러 발생:", e)
        state.npcs = []

    # 5. 각 NPC와 대화/퀴즈 진행
    for npc in state.npcs:
        print(f"\n--- NPC: {npc['name']} (특징: {npc['style']}) ---")
        quiz_output = quiz_chain.invoke({
            "npc_name": npc["name"],
            "style": npc["style"],
            "beginning": state.story.get("beginning", ""),
            "middle": state.story.get("middle", ""),
            "end": state.story.get("end", "")
        })
        quiz_data_str = quiz_output["quiz"]
        try:
            quiz_data = json.loads(quiz_data_str)
        except Exception as e:
            print("퀴즈 출력 파싱 중 에러 발생:", e)
            continue

        print("퀴즈:", quiz_data["quiz"])
        print("선택지:", quiz_data["options"])
        player_answer = input("당신의 선택: ")
        feedback_output = feedback_chain.invoke({
            "player_answer": player_answer,
            "correct_answer": quiz_data["answer"]
        })
        print(feedback_output["feedback"])
        # 정답 시 아이템 지급
        if player_answer.strip() == quiz_data["answer"]:
            state.inventory.append("특별한 열쇠")

    # 7. 최종 결말 출력
    final_output = final_chain.invoke({"inventory": state.inventory})
    state.final_result = final_output["final_result"]
    print("\n--- 최종 결말 ---")
    print(state.final_result)

if __name__ == "__main__":
    run_game()