import asyncio
from decimal import Decimal, InvalidOperation
from time import sleep, time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

import casino_bot.services.games_engine as g_eg
import src.casino_bot.keyboards.inline as inl
from src.casino_bot.callback import CountGame, GameAgain, GameAmount, GameMode
from src.casino_bot.database.models import User, Games
from src.casino_bot.fsm import GameAmountFSM
from src.casino_bot.middleware.auth import AuthMiddleware

photo_id='AgACAgIAAxkBAAIF1WqtQNHY1PvACofZz9SUTbor7TelAAJnLWsb8TNwST4GAxskLKOCAQADAgADeQADPQQ'

router = Router(name='game')

router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

@router.message(F.text == '🎮 Play')
async def f_play(message: Message):
    text = '''
<b>⚔️ Welcome to the main stage.</b>
100% transparent and powered by Telegram. Just you and your luck.

Choose a game 👇
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
    
    if game_mode == 'BigGame':
        await state.update_data(count=3)
    
        text = """
🔥 <b>Grand Match!</b>
This mode features 3 fixed rounds: 🎲, 🎯, and 🏀

<i>Select your bet amount to start 👇</i>
"""
        keyboard = inl.get_amount_keyboard(game_mode)
        
    else:
        text = """
⚔️ <b>How many wins to take the match?</b>

<i>Choose the number of rounds 👇</i>
"""
        keyboard = inl.count_game
    
    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer(
            text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    await callback.answer()
    
    
@router.callback_query(CountGame.filter())
async def count_game(
    callback: CallbackQuery,
    callback_data: CountGame,
    state: FSMContext
):
    count = callback_data.count
    data = await state.get_data()
    mode = data.get('mode')
    await state.update_data(count=count)
    if not mode:
        await callback.answer('Sorry, somethink went wrong', show_alert=True)
        return
    
    text = '''
🎯 <b>Great!</b> Time to place your bets.

<i>Select an amount below 👇</i>
'''
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text,
            reply_markup=inl.get_amount_keyboard(mode=mode),
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
Stake: <b>{amount}$ -> Win: {amount * 2}$</b>
<b>Best of: {count} rounds</b>               ㅤ</blockquote>
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
        new_mode = g_eg.get_biggame_emoji(mode, 1)
        
        if isinstance(callback.message, Message):
            await callback.message.answer(f'⏳ <b>Your turn!</b>You have 30 seconds to send <code>{new_mode}</code>', parse_mode='HTML')
        await state.set_state(GameAmountFSM.waiting_dice)
    else:
        if isinstance(callback.message, Message):
            await callback.message.answer('⚠️Sorry... Error creating game')
    await callback.answer()


@router.message(GameAmountFSM.waiting_amount)
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
Stake: <b>{amount}$ -> Win: {amount * 2}$</b>
<b>Best of: {count} rounds</b>               ㅤ</blockquote>
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
        new_mode = g_eg.get_biggame_emoji(mode, 1)
        
        await message.answer(f'⏳ <b>Your turn!</b>\nYou have 30 seconds to send {new_mode}', parse_mode='HTML')
        await state.set_state(GameAmountFSM.waiting_dice)
    else:
        await message.answer('⚠️Sorry... Error creating game')
        return
    
    
@router.callback_query(F.data == 'other_amount')
async def clb_other_amount(callback: CallbackQuery, state: FSMContext, user_in_db: User):
    await state.set_state(GameAmountFSM.waiting_amount)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            f'<b>Great!</b> Enter the bet amount💸\n<i>Available balance: {user_in_db.balance}$</i>',
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

    data = await state.get_data()
    user_score = data.get('user_score', 0)
    bot_score = data.get('bot_score', 0)
    total_rounds = data.get('rounds_total', 1)
    current_round = data.get('current_round', 1)

    expected = game.mode if game.mode != 'BigGame' else g_eg.get_biggame_emoji(game.mode, current_round)
    
    expected_emoji = expected.replace('\ufe0f', '')
    received = message.dice.emoji.replace('\ufe0f', '')
    
    if received != expected_emoji:
        await message.answer(f'⚙️Please roll the exact emoji-> <code>{expected_emoji}</code>', parse_mode='HTML')
        print(expected_emoji)
        await state.set_state(GameAmountFSM.waiting_dice)
        return
    user_amount = g_eg.calculate_score(expected_emoji, message.dice.value)

    
    await asyncio.sleep(2.5)
    bot_msg = await message.answer_dice(emoji=expected_emoji)
    bot_dice = bot_msg.dice
    if bot_dice is None:
        await message.answer('⚙️Error determining the throw, please contact the administrator.')
        return
    bot_amount = g_eg.calculate_score(expected_emoji, bot_dice.value)
    
    await asyncio.sleep(3)
    
    user_score += user_amount
    bot_score += bot_amount
    stat_block = f'''
<blockquote>┏Bot: {bot_amount}🤖
┗You: {user_amount}👤                    ㅤ</blockquote>
''' 
    if current_round >= total_rounds:
        if user_score > bot_score:
            res_text = f'🏆 <b>You won!</b> Score: 🤖<b>{bot_score}</b> vs <b>{user_score}</b>👤'
            status = 'win'
        elif user_score < bot_score:
            res_text = f'💀 <b>Bot won!</b> Score: 🤖<b>{bot_score}</b> vs <b>{user_score}</b>👤'
            status = 'lose'
        else:
            res_text = f'🤝 <b>Draw!</b> Score: 🤖<b>{bot_score}</b> vs <b>{user_score}</b>👸'
            status = 'draw'
        
        final_text = f'''
🏁 <b>So Cooool! Match complete!</b>\n{stat_block}\n{res_text}        
'''
        await g_eg.ending_game(game, session, status, user_id)    
        await message.answer(
            f'{final_text}',
            reply_markup=inl.play_again(
                mode=expected_emoji,
                amount=str(game.amount),
                rounds=total_rounds,
                game=game
            ),
            parse_mode='HTML'
        )
        
        await state.clear()
    
    else:
        current_round += 1
        
        next_emoji = game.mode if game.mode != 'BigGame' else g_eg.get_biggame_emoji(game.mode, current_round)
        next_emoji = next_emoji.replace('\ufe0f', '')
        round_text = f'''
🏁 <b>Round {current_round - 1}/{total_rounds} complete!</b>\n
➡️ You have 30 seconds to send <code>{next_emoji}</code>
<blockquote>┏Bot: {bot_amount}🤖
┗You: {user_amount}👤                    ㅤ</blockquote>
''' 
        await state.update_data(
            user_score=user_score,
            bot_score=bot_score,
            current_round=current_round
        )
        await message.answer(round_text, parse_mode='HTML')
        await state.set_state(GameAmountFSM.waiting_dice)


@router.callback_query(GameAgain.filter())
async def clb_play_again(
    callback: CallbackQuery,
    callback_data: GameAgain,
    state: FSMContext,
    session: AsyncSession,
    user_in_db: User
):
    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(reply_markup=None)
    
    mode = callback_data.mode
    amount = callback_data.amount
    total_rounds = callback_data.rounds
    
    amount = Decimal(amount)
    
    await state.clear()
  
    if user_in_db.balance < Decimal(amount):
        await callback.answer('⚠️Insufficient funds!', show_alert=True)
        return
  
    success = await g_eg.start_game(
        session, 
        mode, 
        Decimal(amount), 
        total_rounds, 
        user_in_db
    )

    if success:
        await state.update_data(
            mode=mode,
            rounds_total=total_rounds,
            user_score=0,
            bot_score=0,
            count=total_rounds,
            current_round=1
        )
    
        expected_emoji = mode if mode != 'BigGame' else g_eg.get_biggame_emoji(mode, 1)

        text_1 = f"""
🍀 <b>NEW GAME! Ready to Play!</b>
<blockquote><b>Game:</b> {mode}
Stake: <b>{amount}$ -> Win: {amount * 2}$</b>
<b>Best of: {total_rounds} rounds</b>               ㅤ</blockquote>
"""
        text_2 = f'⏳ <b>Your turn!</b>\nYou have 30 seconds to send <code>{expected_emoji}</code>'
        if isinstance(callback.message, Message):
            await callback.message.edit_text(text_1, parse_mode='HTML')
            await callback.message.answer(text_2, parse_mode='HTML')
                  
        await state.set_state(GameAmountFSM.waiting_dice)
    else:
        await callback.answer('Sorry... Somethink went wron\'gg\'')

    await callback.answer()        


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
    
