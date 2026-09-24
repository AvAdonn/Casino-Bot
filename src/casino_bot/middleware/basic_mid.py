from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from src.casino_bot.database.engine import async_session
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

class BDSession(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session() as session:
            data['session'] = session
            return await handler(event, data)
        
class ClearState(BaseMiddleware):
    def __init__(
        self,
        cancel_words: list[str],
    ):
        self.cancel_words = cancel_words
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        state: FSMContext | None = data.get('state')
        
        if isinstance(event, Message) and event.text in self.cancel_words:
            if state:
                await state.clear()
                print('Стан скинуто')
        
        return await handler(event, data)        
        