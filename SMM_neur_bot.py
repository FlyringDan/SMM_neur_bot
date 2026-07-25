import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InputMediaPhoto, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from middleware import AlbumMiddleware
from dotenv import load_dotenv
from llm_send import llm_send

load_dotenv()

TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")
USER_ID = os.getenv("USER_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if TG_CHANNEL_ID:
    try:
        TG_CHANNEL_ID = int(TG_CHANNEL_ID)
    except Exception:
        pass

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AlbumMiddleware())
pending_posts: dict[tuple[int, int], dict[str, object]] = {}


@dp.callback_query(F.data == "publish_post")
async def publish_post(callback_query: CallbackQuery):
    pending = pending_posts.pop((callback_query.message.chat.id, callback_query.message.message_id), None)
    if not pending:
        await callback_query.answer("⚠️ Нет данных для публикации", show_alert=True)
        return

    await callback_query.answer("⏳ Публикую...")

    try:
        target_chat_id = TG_CHANNEL_ID or callback_query.message.chat.id
        media_group = []
        caption_text = pending["llm_resp"]
        for index, file_id in enumerate(pending["file_ids"]):
            media_group.append(
                InputMediaPhoto(
                    media=file_id,
                    caption=caption_text if index == 0 else None,
                )
            )

        await bot.send_media_group(chat_id=target_chat_id, media=media_group)
        chat_id = callback_query.message.chat.id
        await callback_query.message.delete()
        await bot.send_message(
            chat_id=chat_id,
            text=f"✅ Это сообщение было отправлено {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await bot.send_media_group(
            chat_id=chat_id,
            media=[
                InputMediaPhoto(
                    media=file_id,
                    caption=caption_text if index == 0 else None,
                )
                for index, file_id in enumerate(pending["file_ids"])
            ],
        )
    except Exception as e:
        await callback_query.message.answer(f"❗ Ошибка при публикации:\n{e}")


@dp.callback_query(F.data == "cancel_post")
async def cancel_post(callback_query: CallbackQuery):
    pending_posts.pop((callback_query.message.chat.id, callback_query.message.message_id), None)
    await callback_query.answer("❌ Отменено")
    await callback_query.message.edit_text("❌ Публикация отменена")


@dp.message(F.from_user.id == int(USER_ID))
async def handle_photo(message: Message, album: list[Message] | None = None):
    album = album or [message]
    photo_messages = [msg for msg in album if msg.photo]
    if not photo_messages:
        await message.answer("❗ Отправьте фотографию или альбом фотографий")
        return

    await message.answer("⏳ Анализирую фотографии...")

    # Отправляет сообщени в llm
    images_bytes = []
    for msg in album:
        if msg.photo:
            file = await bot.download(msg.photo[-1])
            images_bytes.append(file.read())
    user_text = next(
        (msg.caption or msg.text for msg in album if msg.caption or msg.text),
        None,
    )
    try: 
        llm_resp = await llm_send(images_bytes, user_text)
    except Exception as e:
        await message.answer(f"❗ Ошибка при обработке изображения:\n{e}")
        return

    # Создаем кнопки подтверждения
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_post"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_post")
    )

    media_group = []
    for msg in photo_messages:
        file_id = msg.photo[-1].file_id
        media_group.append(
            InputMediaPhoto(
                media=file_id,
                caption=None,
            )
        )

    confirmation_message = await message.answer(
        f"Это сообщение будет отправленно. Подтвердите.\n\n{llm_resp}",
        reply_markup=builder.as_markup(),
    )
    pending_posts[(confirmation_message.chat.id, confirmation_message.message_id)] = {
        "file_ids": [msg.photo[-1].file_id for msg in photo_messages],
        "llm_resp": llm_resp,
    }


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())