import asyncio
from typing import Any, Awaitable, Callable, Dict, List
from aiogram import BaseMiddleware
from aiogram.types import Message

class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: float = 0.1):
        self.latency = latency
        self.album_cache = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Если у сообщения нет media_group_id, это одиночное фото
        if not event.media_group_id:
            return await handler(event, data)

        total_before = len(self.album_cache.get(event.media_group_id, []))
        self.album_cache.setdefault(event.media_group_id, []).append(event)
        
        # Ждем короткое время, пока Telegram доставит все части альбома
        await asyncio.sleep(self.latency)
        
        total_after = len(self.album_cache[event.media_group_id])

        # Если количество сообщений перестало расти, значит альбом собран полностью
        if total_before + 1 == total_after:
            album = self.album_cache.pop(event.media_group_id)
            data["album"] = album
            return await handler(event, data)
