import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
# from openai import AsyncOpenAI
from dotenv import load_dotenv 

load_dotenv()

API_KEY = os.getenv("API_KEY")
TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
USER_ID = os.getenv("USER_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
# client = AsyncOpenAI(api_key="ВАШ_OPENAI_API_KEY")

def send_to_llm(pict_arr: list, text: str):
    pass

@dp.message(F.photo, F.from_user.id == int(USER_ID))
async def handle_photo(message: types.Message):
    caption = message.caption
    pictures = message.photo

    # 3. Публикация в группу
    # await bot.send_photo(
    #     chat_id=TARGET_CHAT_ID,
    #     photo=photo.file_id, # Переиспользуем file_id, чтобы не качать и грузить заново
    #     caption=caption
    # )
    photo_id = message.photo[0].file_id
    await message.answer_photo(photo = photo_id, caption="Это сообщение будет отправленно. Подтвердите")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())