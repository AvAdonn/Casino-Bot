from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

import src.casino_bot.keyboards.inline as inl
import src.casino_bot.services.games_engine as g_eg
from src.casino_bot.callback import CountGame, GameAmount, GameMode
from src.casino_bot.database.models import User
from src.casino_bot.fsm import GameAmountFSM
from src.casino_bot.middleware.auth import AuthMiddleware


photo_id='AgACAgIAAxkBAAIF1WqtQNHY1PvACofZz9SUTbor7TelAAJnLWsb8TNwST4GAxskLKOCAQADAgADeQADPQQ'

router = Router(name='game')

router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

@router.message(F.text == '🎮 Play')
async def f_play(message: Message):
    text = '''
Welcome to the main stage. ⚔️

100% transparent and provably fair. All outcomes are generated directly by Telegram's native engine, so the only thing that matters here is your luck. 

Choose a mode to start 👇
'''
    await message.delete()
    await message.answer_photo(
        photo=photo_id,
        caption=text,
        parse_mode='HTML',
        reply_markup=inl.game
    )
    

@router.callback_query(GameMode.filter())
async def game_mode(
    callback: CallbackQuery,
    callback_data: GameMode,
    state: FSMContext 
):
    game_mode = callback_data.mode
    await state.update_data(mode=game_mode)
    
    text = """
⚔️ <b>How many wins to take the match?</b>

Choose the number of rounds or enter your own 👇
"""
    
    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer(
            text,
            parse_mode='HTML',
            reply_markup=inl.count_game
        )
    await callback.answer()
    
    
@router.callback_query(CountGame.filter())
async def count_game(
    callback: CallbackQuery,
    callback_data: CountGame,
    state: FSMContext
):
    count = callback_data.count
    await state.update_data(count=count)
    
    text = '''
🎯 <b>Great!</b> Time to place your bets.

Select an amount below 👇
'''
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text,
            reply_markup=inl.game_amount,
            parse_mode='HTML'
        )
    await callback.answer()        


@router.callback_query(GameAmount.filter())
async def game_amount(
    callback: CallbackQuery,
    callback_data: GameAmount,
    state: FSMContext,
    user_in_db: User,
    session: AsyncSession
):
    data = await state.get_data()
    count = data.get('count')
    mode = data.get('mode')
    row_amount = callback_data.amount
    
    await state.clear()
    
    if not count or not mode:
        await callback.answer('System eroor')
        return
    
    if not row_amount:
        await callback.answer('Amount error!❌')
        return
    
    amount = Decimal(row_amount)  
    
    if user_in_db.balance < amount:
        await callback.answer('You dont have a moneeey💰')
        return
    
    text = f"""
🍀 <b>NEW GAME! Ready to Play!</b>
<blockquote><b>Game:</b> {mode}
<b>Stake:</b> {amount}$
<b>Best of:</b> {count} rounds               ㅤ</blockquote>
"""
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text=text,
            parse_mode='HTML',
        )
        
    success = await g_eg.start_game(
        session,
        mode,
        amount,
        count,
        user_in_db
    )
    
    if success:
        await 
    else:
        if isinstance(callback.message, Message):
            await callback.message.answer('⚠️Sorry... Error creating game')
    
    

@router.callback_query(F.data == 'other_amount')
async def clb_other_amount(callback: CallbackQuery, state: FSMContext, user_in_db: User):
    await state.set_state(GameAmountFSM.waiting_amount)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            f'Great, enter the bet amount💸\n<i>Available balance: {user_in_db.balance}$</i>',
            reply_markup=inl.cancel_amount,
            parse_mode='HTML'
        )
    
                    
            
@router.callback_query(F.data == 'back_to_mode')
async def clb_back_to_mode(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = '''
Welcome to the main stage. ⚔️

100% transparent and provably fair. All outcomes are generated directly by Telegram's native engine, so the only thing that matters here is your luck. 

Choose a mode to start 👇
'''
    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo_id,
            caption=text,
            parse_mode='HTML',
            reply_markup=inl.game
        )
    await callback.answer()
    
@router.callback_query(F.data == 'back_to_rounds')
async def clb_back_rounds(callback: CallbackQuery):
    text = """
⚔️ <b>How many wins to take the match?</b>

Choose the number of rounds or enter your own 👇
"""
    
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=inl.count_game
        )
    await callback.answer()
    
