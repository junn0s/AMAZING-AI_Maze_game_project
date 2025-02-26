from dotenv import load_dotenv
load_dotenv()

from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI  # 예시로 OpenAI지만, 실제론 GPT-4o-mini 사용
# GPT-4o-mini 모델을 쓰려면, 해당 모델에 맞는 LangChain LLM 래퍼를 사용해야 함

# 1. 사용자 입력
user_mood = input("분위기를 입력하세요 (예: 공포, 로맨틱 등): ")
user_location = input("장소를 입력하세요 (예: 폐교, 숲 속 등): ")

# --------------------------------------
# 2. 스토리 및 목표 생성
# --------------------------------------
story_prompt_template = """
당신은 창의적인 스토리텔러입니다.
다음 분위기와 장소를 기반으로 몰입감 있는 스토리를 짧게 만드세요.
스토리에는 '초반 상황'과 '최종 목표'를 포함해야 합니다.

분위기: {mood}
장소: {location}

출력 형식:
- story_intro: 스토리의 첫 부분 (상황 설명)
- objective: 스토리의 목표 (무엇을 해야 하는지)
"""

prompt_story = PromptTemplate(
    input_variables=["mood", "location"],
    template=story_prompt_template
)

# 실제론 GPT-4o-mini 모델 래퍼 사용
llm_story = OpenAI(temperature=0.7)
chain_story = LLMChain(llm=llm_story, prompt=prompt_story)

story_result = chain_story.run(mood=user_mood, location=user_location)
print("[스토리 및 목표 생성 결과]")
print(story_result)

# story_result를 파싱(예: JSON)하거나, 간단히 문자열 처리를 통해
# story_intro와 objective를 분리할 수 있도록(아래는 가정 예시)
# 실제로는 regex나 JSON parser 등을 이용 가능
# 예시는 단순 가정으로 표현:
story_intro = "파싱 결과에서 스토리 초반 내용"
story_objective = "파싱 결과에서 최종 목표"

# --------------------------------------
# 3. NPC 3명 생성
# --------------------------------------
npc_prompt_template = """
당신은 뛰어난 게임 기획자입니다.
아래의 스토리 정보를 바탕으로 서로 다른 특징과 말투를 가진 NPC를 3명 만들어 주세요.
각 NPC는 스토리 초반, 중반, 후반과 관련된 이야기를 각각 짤막하게 들려주고,
스토리와 관련된 3지선다 퀴즈 하나를 포함해야 합니다.

[스토리 정보]
{story_intro}
목표: {story_objective}

출력 예시(JSON 형식 권장):
[
  {{
    "name": "NPC1 이름",
    "speech_style": "NPC1 말투",
    "personality": "NPC1 성격/특징",
    "story_part": "초반 상황에 대한 짤막한 이야기",
    "quiz": {{
      "question": "3지선다 문제",
      "choices": ["1) ...", "2) ...", "3) ..."],
      "answer": "정답 번호"
    }}
  }},
  ... (NPC2, NPC3)
]
"""

prompt_npcs = PromptTemplate(
    input_variables=["story_intro", "story_objective"],
    template=npc_prompt_template
)

llm_npcs = OpenAI(temperature=0.7)
chain_npcs = LLMChain(llm=llm_npcs, prompt=prompt_npcs)

npc_result = chain_npcs.run(story_intro=story_intro, story_objective=story_objective)
print("[NPC 생성 결과]")
print(npc_result)

# npc_result를 JSON으로 파싱해 NPC들의 정보를 구조화해 관리
# 실제 구현에서는 json.loads() 등을 통해 파싱:
# npc_info = json.loads(npc_result)
# npc_info => [{ "name": ..., "speech_style": ..., "personality": ..., "story_part": ..., "quiz": {...}}, ...]

# --------------------------------------
# 4. 사용자 퀴즈 풀이
# --------------------------------------
# 간단 예시로 NPC 순서대로 퀴즈를 내고, 정답을 입력받아 비교:
# 실제론 각 NPC마다 초반/중반/후반에 맞추어 대화 흐름을 구성하거나
# LangChain의 ConversationChain 등을 사용해 대화를 확장할 수 있음.

# for i, npc in enumerate(npc_info):
#     print(f"\nNPC{i+1} - {npc['name']} (말투: {npc['speech_style']}, 특징: {npc['personality']})")
#     print(npc["story_part"])
#     print("퀴즈: ", npc["quiz"]["question"])
#     for choice in npc["quiz"]["choices"]:
#         print(choice)
#     user_answer = input("정답 번호를 입력하세요: ")
#     if user_answer == npc["quiz"]["answer"]:
#         print("정답입니다!")
#     else:
#         print("오답입니다...")

# --------------------------------------
# 5. 결말 생성
# --------------------------------------
# NPC로부터 모든 정보를 얻고, 사용자가 최종 목표 달성 여부에 따라
# 탈출 성공/실패 스토리를 생성해볼 수 있음.
conclusion_prompt_template = """
당신은 스토리 작가입니다.
아래 정보를 참고하여, 플레이어가 미로 탈출을 성공했다면 성공 스토리를,
실패했다면 실패 스토리를 요약하여 마무리 지어주세요.

[스토리 초반 정보]
{story_intro}

[최종 목표]
{story_objective}

[사용자 탈출 성공 여부]
{escape_result}  # "성공" 또는 "실패"라고 가정

출력 형식:
- 결말 스토리: 한 문단
"""

prompt_conclusion = PromptTemplate(
    input_variables=["story_intro", "story_objective", "escape_result"],
    template=conclusion_prompt_template
)

llm_conclusion = OpenAI(temperature=0.7)
chain_conclusion = LLMChain(llm=llm_conclusion, prompt=prompt_conclusion)

# 예시로 탈출 성공/실패 여부를 임의 설정
escape_result = "성공"  # 또는 "실패"

conclusion_result = chain_conclusion.run(
    story_intro=story_intro,
    story_objective=story_objective,
    escape_result=escape_result
)
print("[결말]")
print(conclusion_result)