from decimal import Decimal, InvalidOperation

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from time import sleep, time

import src.casino_bot.keyboards.inline as inl
import casino_bot.services.games_engine as g_eg
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
        await callback.answer('System error')
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
<b>Stake:</b> {amount}$ -> Win: {amount * 2}$
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
        await state.update_data(
            user_score=0,
            bot_score=0,
            rounds_total=count
        )
        
        if isinstance(callback.message, Message):
            await callback.message.answer('Чудово, твій кидок у тебе 30 секунд')
        await state.set_state(GameAmountFSM.waiting_dice)
    else:
        if isinstance(callback.message, Message):
            await callback.message.answer('⚠️Sorry... Error creating game')
    await callback.answer()


@router.callback_query(GameAmountFSM.waiting_amount)
async def fsm_waiting_amount(
    message: Message,
    state: FSMContext,
    user_in_db: User,
    session: AsyncSession
):
    data = await state.get_data()
    count = data.get('count')
    mode = data.get('mode')
    if not count or not mode:
        await message.delete()
        await message.answer('System error')
        return
    row_amount = message.text
    if not row_amount:
        await message.answer('❌ Please enter a valid whole number!')
        return
    try:
        row_amount = row_amount.replace(',', '.')
        amount = Decimal(row_amount)
        if amount < 0.5:
            raise ValueError
    except (ValueError, InvalidOperation):
        await message.answer('✍️ Enter the deposit amount!\n<i>Example: 15.50</i>', parse_mode='HTML')
        return
    
    await state.clear()
    
    text = f"""
🍀 <b>NEW GAME! Ready to Play!</b>
<blockquote><b>Game:</b> {mode}
<b>Stake:</b> {amount}$ -> Win: {amount * 2}$
<b>Best of:</b> {count} rounds               ㅤ</blockquote>
"""
    await message.delete()
    await message.answer(
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
        await state.update_data(
            user_score=0,
            bot_score=0,
            rounds_total=count
        )
        
        await message.answer('Чудово, твій кидок у тебе 30 секунд')
        await state.set_state(GameAmountFSM.waiting_dice)
    else:
        await message.answer('⚠️Sorry... Error creating game')
        return
    
    
@router.callback_query(F.data == 'other_amount')
async def clb_other_amount(callback: CallbackQuery, state: FSMContext, user_in_db: User):
    await state.set_state(GameAmountFSM.waiting_amount)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            f'Great, enter the bet amount💸\n<i>Available balance: {user_in_db.balance}$</i>',
            reply_markup=inl.cancel_amount,
            parse_mode='HTML'
        )
    
                    
@router.message(F.dice, GameAmountFSM.waiting_dice)
async def waiting_dice(message: Message, state: FSMContext, session: AsyncSession):
    await state.set_state(None)
    
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return 
    
    game = await g_eg.get_game(session, user_id)
    if game is None:
        await message.answer('⚙️Game not found... Please try again.')
        return
    
    if message.dice is None:
        return
    
    if message.dice.emoji != game.mode:
        await message.answer(f'Варто Кидати саме {game.mode}')
        await state.set_state(GameAmountFSM.waiting_dice)
        return
    user_amount = g_eg.calculate_score(game.mode, message.dice.value)

    
    data = await state.get_data()
    user_score = data.get('user_score', 0)
    bot_score = data.get('bot_score', 0)
    total_rounds = data.get('rounds_total', 1)
    current_round = data.get('current_round', 1)
    
    await asyncio.sleep(2.5)
    bot_msg = await message.answer_dice(emoji=game.mode)
    bot_dice = bot_msg.dice
    if bot_dice is None:
        await message.answer('⚙️Error determining the throw, please contact the administrator.')
        return
    bot_amount = g_eg.calculate_score(game.mode, bot_dice.value)
    
    await asyncio.sleep(3)
    
    user_score += user_amount
    bot_score += bot_amount
    round_text = f'''
Раунд {current_round}/{total_rounds} завершено!
🤖Бот-> {bot_amount} | {user_amount} <-user🙈
'''
    if current_round >= total_rounds:
        if user_score > bot_score:
            res_text = f'🏆 Ти переміг!\nРахунок: {user_score}:{bot_score}'
            status = 'win'
        elif user_score < bot_score:
            res_text = f'💀 Бот переміг!\nРахунок: {user_score}:{bot_score}'
            status = 'lose'
        else:
            res_text = f"🤝 Нічия!\nРахунок: {user_score}:{bot_score}"
            status = 'draw'
        
        await g_eg.ending_game(game, session, status, user_id)    
        await message.answer(f'{round_text}{res_text}')
        
        await state.clear()
    
    else:
        current_round += 1
        await state.update_data(
            user_score=user_score,
            bot_score=bot_score,
            current_round=current_round
        )
        await message.answer(f'{round_text}/n/nХагальний рахунок: 🤖bot: {bot_score} | {user_score} :user🙈')
        await state.set_state(GameAmountFSM.waiting_dice)
        
            
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
    
