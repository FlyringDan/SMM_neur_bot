import os
from openai import AsyncOpenAI
import base64

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(
    base_url='http://127.0.0.1:11434/v1',
    api_key=OPENAI_API_KEY
)

def bytes_to_base64_url(image_bytes: bytes) -> str:
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded}"

async def llm_send(images: list, user_text: str | None = None):
    prompt = """
## Роль

Ты - SMM-менеджер, который создёт посты, в группу, которую ведёт один человек.

## Задача

Тебе будут приходить картинки, на основе которых тебе нужно будет создать пост для группы.

Просто пиши текст поста, не нужно писать что-то вроде "Вот пост для группы" или "Вот текст поста".
"""
    if user_text:
        prompt += f"\n\nДополнительные пожелания пользователя:\n{user_text}"

    content = [{"type": "text", "text": prompt}]

    # Массив с сообщениями
    for img_bytes in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": bytes_to_base64_url(img_bytes)}
        })

    # Отпраляем запрос в llm
    response = await client.chat.completions.create(
        model="qwen2.5vl:latest", 
        messages=[{"role": "user", "content": content}],
        extra_body={
            "options": {
                "num_ctx": 16384
            }
        }
    )

    return response.choices[0].message.content
