import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from middleware import AlbumMiddleware
from dotenv import load_dotenv
from llm_send import llm_send

load_dotenv()

TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
USER_ID = os.getenv("USER_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AlbumMiddleware())


@dp.message(F.from_user.id == int(USER_ID))
async def handle_photo(message: Message,  album: list[Message]):
    await message.answer("⏳ Анализирую альбом...")

    # Отправляет сообщени в llm
    images_bytes = []
    for msg in album:
        if msg.photo:
            file = await bot.download(msg.photo[-1])
            images_bytes.append(file.read())
    try: 
        llm_resp = await llm_send(images_bytes)
    except Exception as e:
        await message.answer(f"❗ Ошибка при обработке изображения:\n{e}")
        return

    # Создаем кнопки подтверждения
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_post"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_post")
    )
    file_id = message.photo[-1].file_id
    await message.answer_photo(
        photo=file_id,
        caption=f"Это сообщение будет отправленно. Подтвердите.\n\n{llm_resp}",
        reply_markup=builder.as_markup()
    )

    # Публикация в группу
    # await bot.send_photo(
    #     chat_id=TARGET_CHAT_ID,
    #     photo=photo.file_id, # Переиспользуем file_id, чтобы не качать и грузить заново
    #     caption=caption
    # )
    
    # photo_id = message.photo[0].file_id
    # await message.answer_photo(photo = photo_id, caption="Это сообщение будет отправленно. Подтвердите")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())