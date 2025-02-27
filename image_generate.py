import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI()

def generate_image(prompt: str, n: int = 1, size: str = "1024x1024") -> str:
    try:
        # 이미지 생성 요청
        response = client.images.generate(
            model = "dall-e-3",
            prompt = prompt,
            n=n,
            size=size
        )
        # 응답에서 첫 번째 이미지의 URL 추출
        image_url = response.data[0].url
        #image_url = response['data'][0]['url']
        return image_url
    except Exception as e:
        print("이미지 생성 중 오류 발생:", e)
        return ""
