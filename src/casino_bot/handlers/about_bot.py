import urllib.parse

from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.casino_bot.middleware.auth import AuthMiddleware

router = Router(name='about_bot')

router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

photo_id = 'AgACAgIAAxkBAAICmmqlPuiKIgvh8CvDvbe1bzcx9yWoAAKjIGsbVV8oSZrBP8q6NCInAQADAgADeQADPQQ'
terms_of_service = 'https://telegra.ph/Terms-of-ServiceLast-Updated-September-16-2026-09-16'

@router.message(F.text == 'About Bot 🤖')
async def about_bot(
    message: Message
):
    builder = InlineKeyboardBuilder()    
    builder.button(
        text='📄 Terms of Service',
        url=terms_of_service
    )
    
    user_id = message.from_user.id if message.from_user else None
    if user_id:
        full_invite_message = f"Play with me! 🎰 Use my link to join:\nhttps://t.me/casinov2_robot?start={user_id}"
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
    builder.adjust(2)
    
    text = '''
🎲 <b>Gaming Hub</b> — your space for fair gaming.

We built this platform for those who value transparent mechanics and seamless performance. No hidden algorithms—just you, math, and your luck.

<blockquote><b>👨‍💻 Customer Support</b>
While game results are calculated instantly, financial transactions (withdrawals) are manually reviewed to ensure your security.

Contact Admin: @if_hello

<b>Support Guidelines:</b>
• Get straight to the point: include your <code>ID</code> and describe the issue.
• We will NEVER ask for your passwords or SMS codes.
• Withdrawal requests are processed in the order they are received.</blockquote>
'''    
    await message.delete()
    await message.answer_photo(
        photo=photo_id,
        caption=text,
        reply_markup=builder.as_markup(),
        parse_mode='HTML'
    )