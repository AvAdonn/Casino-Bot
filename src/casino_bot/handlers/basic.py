from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

import src.casino_bot.database.requests as req
import src.casino_bot.keyboards as kb

router = Router(name='basic')

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, session: AsyncSession):
    args = command.args
    referral_id = None
    
    user_id = message.from_user.id if message.from_user else 0
    
    if args and args.isdigit():
        parsed_id = int(args)
        if parsed_id != user_id:
            referral_id = parsed_id
        else:
            print('Спроба саморефералки')
    
    name = message.from_user.first_name if message.from_user else 'Гість'
    
    user_in_db = await req.get_user(session, user_id)
    text = f'''
🎰 <b>Welcome to Gaming Hub, {name}!</b>

<blockquote>⚡️ <b>Your space for fair play, thrill, and fast wins.</b>
Test your luck, spin the wheel, and grab your first big payout today!</blockquote>

🔥 <b>What awaits you:</b>
• Transparent mechanics and provably fair algorithms
• Instant deposits and fast withdrawals (Card / Crypto)
• 24/7 Customer support

<blockquote>📌 <b>Navigation:</b>
/start — restart the bot and open the main menu
/help — contact our support team</blockquote>

<i>Choose an action below and make your first spin! Good luck! 🍀</i>
    '''
    
    if user_in_db is None:
        await req.add_user(session, user_id, referral_id)
        await message.answer(
            text,
            parse_mode='HTML'
        )
        await message.answer(
            f'Welcome, {name}! 🎲 Your account has been created. Ready to try your luck?', 
            reply_markup=kb.main_menu
        )
    else:
        await message.answer(
            text,
            parse_mode='HTML'
        )
        await message.answer(
            f'Hi, {name}! ⚡️ Welcome to the system. Your wallet is ready to go.',
            reply_markup=kb.main_menu
        )
        
        
    
@router.message(Command('help'))
async def cmd_help(message: Message):
    text = '👽 Developer | support: @if_hello'
    await message.answer(
        text
    )
    
    
@router.callback_query(F.data == 'back_to_menu')
async def clb_back_to_menu(callback: CallbackQuery):
    text = '''
🎰 <b>Main Menu</b>

You're back on the main screen. Choose an action below 👇

<blockquote>💡 <b>Tip:</b> Check your "Profile" to track your stats and game history.</blockquote>
'''
    
    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer(
            text,
            parse_mode='HTML'
        )
    await callback.answer()
    