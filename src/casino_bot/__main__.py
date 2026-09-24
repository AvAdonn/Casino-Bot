import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from typing import Final

from src.casino_bot.handlers import get_routers

from src.casino_bot.database.engine import engine
from src.casino_bot.database.models import Base

from src.casino_bot.middleware.basic_mid import BDSession, ClearState

base_words = ['🎮 Play', '💰 My Wallet', 'My Profile 🆔', '🔗 Referrals', 'About Bot 🤖']

async def main() -> None:
    load_dotenv()
    token = os.getenv('TOKEN')
    if token is None:
        raise ValueError('Token error')
    
    try:
        GROUP_ID: Final[int] = int(os.environ['GROUP_ID'])
    except KeyError:
        raise ValueError('Відсутній ключ')
    except ValueError:
        raise ValueError('Помилка конвертації в "int"')

    
    bot = Bot(token)
    dp = Dispatcher()
    dp['group_id'] = GROUP_ID
    
    dp.update.middleware(BDSession())
    dp.message.middleware(ClearState(cancel_words=base_words))
    
    dp.include_routers(*get_routers())
    
    dp.startup.register(starting)
    dp.shutdown.register(stopped)
    await dp.start_polling(bot)

    
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print('Таблиці успішно створені')

async def starting(dispatcher: Dispatcher) -> None:
    print('Bot starting...')
    await init_db()
    
async def stopped(
    dispatcher: Dispatcher
) -> None:
    print('Bot stopped.')
    
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        print('Stopped by me.')