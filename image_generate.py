import os
import openai
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_image(prompt: str, n: int = 1, size: str = "1024x1024") -> str:
    try:
        # 이미지 생성 요청
        response = openai.Image.create(
            prompt=prompt,
            n=n,
            size=size
        )
        # 응답에서 첫 번째 이미지의 URL 추출
        image_url = response['data'][0]['url']
        return image_url
    except Exception as e:
        print("이미지 생성 중 오류 발생:", e)
        return ""
