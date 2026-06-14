from openai import OpenAI
import base64

client = OpenAI(
    base_url='http://127.0.0.1:11434/v1',
    api_key='ollama' # Ключ обязателен для инициализации библиотеки, но его значение не проверяется
)

def bytes_to_base64_url(image_bytes: bytes) -> str:
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded}"

async def llm_send(images: list):
    content = [{"type": "text", "text": "Придумай подпись для телеграм канала на основе этих картинок."}]

    # Массив с сообщениями
    for img_bytes in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": bytes_to_base64_url(img_bytes)}
        })

    # Отпраляем запрос в llm
    response = await client.chat.completions.create(
        model="llava", 
        messages=[{"role": "user", "content": content}]
    )

    return response.choices[0].message.content
