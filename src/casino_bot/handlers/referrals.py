import urllib.parse

from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

import src.casino_bot.database.requests as req
from src.casino_bot.middleware.auth import AuthMiddleware

photo_id = 'AgACAgIAAxkBAAICmGqlPou2W08QqqHNiioUa220HwyXAAKiIGsbVV8oSREHCTaouHKHAQADAgADeQADPQQ'

router = Router(name='referrals')

router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

@router.message(F.text == '🔗 Referrals')
async def referrals(message: Message, session: AsyncSession):
    builder = InlineKeyboardBuilder()
    
    user_id = message.from_user.id if message.from_user else None
    if user_id:
        share_link = f'https://t.me/casinov2_robot?start={user_id}'
        full_invite_message = f"Play with me! 🎰 Use my link to join:\n{share_link}"
        encoded_text = urllib.parse.quote(full_invite_message)

        share_url = f"https://t.me/share/url?url={encoded_text}"
        
        builder.button(
            text='🎁 Invite & Earn',
            url=share_url
        )
        
        builder.button(
            text='Back to menu ⬅️',
            callback_data='back_to_menu'
        )
        builder.adjust(1)
    
    
        referrals = await req.get_referral(session, user_id)
        caption = f"""
Your unique invite link is ready! Share it and start building your player network right now.

<blockquote>🚀 <b>Coming Soon:</b>
The system is currently in accumulation mode, but we will be launching a massive bonus program very soon! You'll earn rewards and a percentage of every invited friend's activity. 

Build your team in advance to maximize your profit on release day!</blockquote>

🔗 <b>Your invite link:</b>
<code>{share_link}</code>

📊 <b>Friends invited:</b> {referrals}
"""
    
        await message.delete()
        await message.answer_photo(
        photo=photo_id,
        caption=caption,
        parse_mode='HTML',
        reply_markup=builder.as_markup()
        )
    else:
        await message.answer('Please register first.')