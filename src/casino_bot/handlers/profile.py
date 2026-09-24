from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

import src.casino_bot.database.requests as req
import src.casino_bot.keyboards.inline as inl
from src.casino_bot.database.models import User
from src.casino_bot.middleware.auth import AuthMiddleware

router = Router(name='profile')
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())
    
@router.message(F.text == 'My Profile 🆔')
async def f_profile(message: Message, user_in_db: User, session: AsyncSession):
    user_id = message.from_user.id if message.from_user else 0
    refferal = await req.get_referral(session, user_in_db.tg_id)
    
    win_rate = await req.rate_check(session, user_id)
    
    text = f'''
👤 <b>{user_in_db.role.upper()}</b> | <code>{user_in_db.tg_id}</code>

💰 <b>Balance:</b> ${user_in_db.balance}
👥 <b>Referrals:</b> {refferal}.
📈 <b>WinRate:</b> {win_rate}%

<blockquote>🎮 <b>Total Played:</b> {user_in_db.total_played}$               ㅤ
🟢 <b>Win:</b> {user_in_db.win}  •  🔴 <b>Loss:</b> {user_in_db.lose}</blockquote>
'''
    await message.delete()
    await message.answer_photo(
        photo='AgACAgIAAxkBAAICjGqlPXUleDd55xDtHoSSDnBDzh2mAAKdIGsbVV8oSSERRl6lY5xiAQADAgADeQADPQQ',
        caption=text, 
        parse_mode='HTML', 
        reply_markup=inl.back_menu
    )
    

