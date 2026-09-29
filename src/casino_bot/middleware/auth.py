from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from src.casino_bot.database.requests import get_user

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        session = data['session']
        
        tg_user = data.get('event_from_user')
        if not tg_user:
            return
        
        tg_id = tg_user.id
        user = await get_user(session, tg_id)
        
        if user is None:
            if isinstance(event, Message) and event.text and event.text.startswith('/start'):
                data['user_in_db'] = None
                return await handler(event, data)
            
            if isinstance(event, (Message, CallbackQuery)):
                await event.answer('👤 Registration required!\n\nPress /start to continue.')
            
            return
        
        data['user_in_db'] = user
        
        return await handler(event, data)