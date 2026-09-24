
from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

import src.casino_bot.database.requests as req
import src.casino_bot.keyboards.inline as inl
from src.casino_bot.callback import AdminReceipt, Payments, Withdraw, WithdrawAdmin
from src.casino_bot.database.models import User
from src.casino_bot.fsm import PaymentFSM, WithDrawFSM
from src.casino_bot.middleware.auth import AuthMiddleware

router = Router(name='payments')

router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

PAYMENT_CONFIG = {
    'card_ua': {'requisites': '<code>UA148867676767</code>', 'rate': Decimal('44.50'), 'currency': '₴'},
    'card_eu': {'requisites': '<code>EU148867676767</code>', 'rate': Decimal('0.92'), 'currency': '€'},
}


@router.message(F.text == '💰 My Wallet')
async def f_gamanec(message: Message, user_in_db: User):
    text = f'''
✅<b>Status:</b> <i>Verified</i>
💰<b>Current Balance:</b> {user_in_db.balance}$

<i>Select an option 👇</i>
    '''
    await message.delete()
    await message.answer_photo(
        photo='AgACAgIAAxkBAAICjmqlPZ_OwrTM7sG09Sfyt9v6I2PYAAKfIGsbVV8oSUagi9ZU5gEIAQADAgADeQADPQQ',
        caption=text,
        parse_mode='HTML',
        reply_markup=inl.pay_withdraw
    )
    

@router.callback_query(Payments.filter(F.action == 'back_to_wallet'))
async def clb_back_to_wallet(callback: CallbackQuery, user_in_db: User):
    text = f'''
✅<b>Status:</b> <i>Verified</i>
💰<b>Current Balance:</b> {user_in_db.balance}$

<i>Select an option 👇</i>
    '''
    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo='AgACAgIAAxkBAAICA2qlK5PF1bOEyYUC99--_SAQjAL1AAISIGsbVV8oSR-zjHxBolI5AQADAgADeAADPQQ',
            caption=text, 
            parse_mode='HTML', 
            reply_markup=inl.pay_withdraw
        )
    await callback.answer()
    
    
@router.callback_query(Payments.filter(F.action == 'deposit'))
async def clb_pay(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = '''
💳 Select payment method:
    '''
    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=inl.choise_pay)
    await callback.answer()
    
    
@router.callback_query(Payments.filter(F.action == 'pay'))
async def clb_payments_fab(callback: CallbackQuery, callback_data: Payments, state: FSMContext):
    method = callback_data.method

    payments_config ={
        'card_ua': {'name': 'Card  🇺🇦', 'currency': 'UAH'},
        'card_eu': {'name': 'Europe Card 🇪🇺', 'currency': 'EUR'},
        'crypto': {'name': 'CryptoBot 🪙', 'currency': 'USDT'},
        'stars': {'name': 'Telegram Stars ⭐️', 'currency': 'XTR'}
    }
    
    config = payments_config.get(method)
    
    if not config:
        await callback.answer('Payment error!(', show_alert=True)
        return
    
    await state.update_data(pay_method=method)
    
    markup = None
    
    text = f'''
💳 <b>Method:</b> {config['name']}
'''
    if method == 'stars':
        markup = inl.pay_stars
        text += '⌨️ Enter deposit amount in Telegram Stars ⭐️'
    else:
        markup = inl.cancel_pay
        await state.set_state(PaymentFSM.waiting_sum)
        text += '⌨️ Enter deposit amount in USD($):\n\n<i>Min. amount: 1$</i>'
    
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()


@router.callback_query(Payments.filter(F.action == 'back'))
async def clb_back_fab(callback: CallbackQuery, user_in_db: User):
    text = f'''
✅<b>Status:</b> <i>Verified</i>
💰<b>Current Balance:</b> {user_in_db.balance}$

<i>Select an option 👇</i>
    '''
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=inl.pay_withdraw
        )
    await callback.answer()
    
    
@router.callback_query(Payments.filter(F.action == 'pay_stars'))
async def clb_pay_stars_fab(callback: CallbackQuery, callback_data: Payments, state: FSMContext):
    amount = callback_data.amount
    prices = [LabeledPrice(label='XTR', amount=amount)]
    
    if amount < 0:
        await callback.answer('Somethink wrong...', show_alert=True)
        return
    
    if amount == 0:
        await state.set_state(PaymentFSM.waiting_sum)
        if isinstance(callback.message, Message):
            text = '''
💳 <b>Method:</b> Telegram Stars ⭐️
⌨️ Enter deposit amount in Telegram Stars ⭐️:

<i>Min. amount: 1 </i>⭐️
'''
            
            await callback.message.edit_text(text, reply_markup=inl.cancel_pay, parse_mode='HTML')
            await callback.answer()
            return
    
    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer_invoice(
            title='Balance Top-Up',
            description='Purchasing 50⭐ for the game!',
            prices=prices,
            provider_token='',
            payload=f'deposit_stars_{amount}',
            currency='XTR'
        )
        await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)
    

@router.message(F.successful_payment)
async def f_successful_payment(message: Message, session: AsyncSession, user_in_db: User):
    payment_info = message.successful_payment
    if payment_info is None:
        return
    
    charge_id = payment_info.telegram_payment_charge_id
    total_stars = payment_info.total_amount 
    
    usd_bal = Decimal(str(total_stars * 2))
    
    await req.process_star_payment(
        session=session,
        tg_id=user_in_db.tg_id,
        pay_id=charge_id,
        stars_amount=total_stars,
        usd_amount=usd_bal
    )
    
    text = f'''
✅ <b>Payment Successful!</b>

<b>Converted:</b> {total_stars}⭐ ➔ ${usd_bal}
<i>Rate: 1⭐ = $0.018</i>

💰 <b>Current Balance:</b> ${user_in_db.balance}
'''
    
    await message.answer(text, parse_mode='HTML')
    

@router.message(PaymentFSM.waiting_sum)
async def fsm_waiting_sum(message: Message, state: FSMContext, ):
    data = await state.get_data()
    
    pay_method = data.get('pay_method')
    
    if not pay_method:
        await message.answer('Payment error, try again, please...')
        await state.clear()
        return
    
    pay_sum = message.text    
    amount = 0
    
    if not pay_sum:
        await message.answer('❌ Please enter a valid whole number!')
        return
        
    if pay_method == 'stars':
        try:
            amount = int(pay_sum.strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            await message.answer('❌ Please enter a valid whole number!')
            return 
    else:
        try:
            pay_sum = pay_sum.replace(',', '.')
            amount = Decimal(pay_sum)
            if amount < 1:
                raise ValueError
        except (ValueError, InvalidOperation):
            await message.answer('✍️ Enter the deposit amount!\n<i>Example: 15.50</i>', parse_mode='HTML')
            return
        
    if pay_method == 'stars':
        prices = [LabeledPrice(label='XTR', amount=int(amount))]
        
        await state.clear()
        await message.answer('🧾 Invoice created! Please complete your payment below 👇')
        await message.answer_invoice(
            title='Balance Top-Up',
            description=f'Purchasing {amount}⭐ for the game!',
            prices=prices,
            provider_token='',
            payload=f'deposit_stars_{amount}',
            currency='XTR'
        )
    
    elif pay_method == 'crypto':
        await state.clear()
        await message.answer('⚙️ This feature is currently unavailable.')
    
    elif pay_method == 'card_ua' or pay_method == 'card_eu':
        
        config = PAYMENT_CONFIG[pay_method]
        
        local_amount = amount * config['rate']
        
        
        text = f'''
🧾 <b>Invoice Created!</b>

💳 <b>Method:</b> <i>{pay_method}</i>
💵 <b>Amount Due:</b> ${amount} ➔ {local_amount} {config['currency']}
🏦 <b>Details:</b> <code>{config['requisites']}</code>

⚠️ <i>Important: Please send a screenshot of your payment receipt in this chat!</i>
'''
        await state.update_data(
            fiat_amount=str(local_amount),
            usd_amount= str(amount),
            currency=config['currency'],
            pay_method=pay_method
            )
        await state.set_state(PaymentFSM.waiting_receipt)
        await message.answer(text, parse_mode='HTML')
        
        
@router.message(PaymentFSM.waiting_receipt, F.photo)
async def fsm_waiting_receipt(message: Message, state: FSMContext, bot: Bot, group_id: int):
    data = await state.get_data()
    
    fiat_amount=data.get('fiat_amount')
    usd_amount=data.get('usd_amount')
    currency=data.get('currency')
    pay_method=data.get('pay_method')
    
    file_id = message.photo[-1].file_id if message.photo else None
    user_id = message.from_user.id if message.from_user else 'Nope'
     
    if not file_id:
        await message.answer('❌ Error receiving the file. Please try again!')
        return
    
    if not usd_amount:
        await message.answer('❌ Amount error. If the transfer was successful, please contact support.')
        await state.clear()
        return    
    
    if user_id == 'Nope':
        await message.answer('❌ User ID is missing.')
        return
    
    pay_method = pay_method or 'Unknown'
    caption_text = (
    f"🧾 <b>New Deposit Request!</b>\n\n"
    f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
    f"💵 <b>To Credit:</b> ${usd_amount}\n"
    f"💳 <b>Receipt Amount:</b> {fiat_amount} {currency}\n\n"
    f"👇 <b>Select an action:</b>"
)
    
    keyboard = inl.confirm_eu_ua(user_id, amount=str(usd_amount), pay_method=pay_method)
    
    
    await bot.send_photo(
        chat_id=group_id,
        photo=file_id,
        caption=caption_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    await state.clear()
    await message.answer('⏳ Your payment is being processed. Please wait for the funds to be credited.')
    
    
@router.callback_query(AdminReceipt.filter(F.action == 'approve'))
async def clb_approve_pm(callback: CallbackQuery, callback_data: AdminReceipt, session: AsyncSession, bot: Bot):
    admin_id = callback.from_user.id
    admin = await req.get_user(session, admin_id)
    if admin is None or admin.role != 'admin':
        await callback.answer(
            '⛔ You do not have permission to perform this action',
            show_alert=True 
            )
        return

    
    usd_amount = callback_data.usd_amount
    user_id = callback_data.user_id
    pay_method = callback_data.pay_method
    
    pay_id, is_success = await req.process_ua_eu_payment(
        session,
        user_id,
        Decimal(usd_amount),    
        pay_method
    )
    
    admin = callback.from_user.username if callback.from_user else 'Unknown'
    
    
    if is_success:
        if isinstance(callback.message, Message):
            await callback.message.edit_caption(
                caption = f'✅ Transaction approved by @{admin}',
                reply_markup=None
                )
        
        try:
            text = f'✅ <b>Payment Successful!</b>\n\n🆔 Transaction ID: <tg-spoiler>{pay_id}</tg-spoiler>'
            chat_id = callback_data.user_id
            await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
        except Exception as e:  # noqa: BLE001
            print(f'Помилка надсилання повідомлення->{e}')
            
        await callback.answer()
        

@router.callback_query(AdminReceipt.filter(F.action == 'reject'))
async def clb_reject_pm(callback: CallbackQuery, callback_data: AdminReceipt, bot: Bot):
    user_id = callback_data.user_id
    
    if isinstance(callback.message, Message):
        admin = callback.from_user.username if callback.message else 'Відсутній'
        caption = f'❌ Transaction rejected by @{admin}'
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=None
        )
        
    try:
        text = '❌ <b>Your payment was rejected.</b>\nIf you believe this is a mistake, please contact support.'
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode='HTML'
        )
    except Exception as e:  # noqa: BLE001
        print(f'Помилка надсилання->{e}')
        
    await callback.answer()
    

##################################################################################################################

'''    
@router.message(F.photo)
async def photo_id(message: Message):
    photo_id = message.photo[-1].file_id if message.photo else None
    
    await message.reply(
        f'<code>{photo_id}</code>',
        parse_mode='HTML'
    )
'''
    
@router.message(Command('admin'))
async def admin_lst(message: Message, session: AsyncSession, user_in_db: User):
    user_in_db.role = 'admin'
    await session.commit()
    
    await message.answer('⚠️Your role: admin')

##################################################################################################################


@router.callback_query(Payments.filter(F.action == 'withdraw'))
async def clb_prewithdraw(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = '''
💳 Select withdraw method:
    '''
    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=inl.withdraw)
        
    await callback.answer()
    
@router.callback_query(Withdraw.filter(F.action == 'withdraw'))
async def clb_withdraw(callback: CallbackQuery, callback_data: Withdraw, state: FSMContext, user_in_db: User):
    method = callback_data.method
    
    withdraw_config ={
        'card_ua': {'name': 'Card  🇺🇦', 'currency': 'UAH'},
        'card_eu': {'name': 'Europe Card 🇪🇺', 'currency': 'EUR'},
        'crypto': {'name': 'CryptoBot 🪙', 'currency': 'USDT'},
    }
    
    config = withdraw_config.get(method)
    if not config:
        await callback.answer('Withdraw config error!', show_alert=True)
        return
    
    await state.update_data(method=method)
    
    await state.set_state(WithDrawFSM.waiting_sum)
    text = f'''
💳 <b>Method:</b> {config['name']}
💰 <b>Balance:</b> {user_in_db.balance}$
⌨️ Enter withdraw amount in USD($):

<i>Min. amount: 1$</i>
'''
    
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text, 
            reply_markup=inl.cancel_withdraw, 
            parse_mode='HTML'
        )
    await callback.answer()
    
    
@router.message(WithDrawFSM.waiting_sum)
async def withdraw_waiting_sum(message: Message, state: FSMContext, user_in_db: User):
    data = await state.get_data()
    method = data.get('method')
    
    withdraw_sum = message.text 
    amount = 0
    
    if not withdraw_sum:
        await message.answer('❌ Please enter a valid whole number!', reply_markup=inl.cancel_withdraw)
        return
    
    try:
        withdraw_sum = withdraw_sum.replace(',', '.')
        amount = Decimal(withdraw_sum)
        if amount < 1:
            raise ValueError
    except (ValueError, InvalidOperation):
        await message.answer('✍️ Enter the deposit amount!\n<i>Example: 15.50</i>', parse_mode='HTML', reply_markup=inl.cancel_withdraw)
        return
    
    if method == 'crypto':
        await state.clear()
        await message.answer('⚙️ This feature is currently unavailable.')
        return
    
    if user_in_db.balance < amount:
        await message.answer('❌ Insufficient funds.', reply_markup=inl.cancel_withdraw)
        return    
    
    await state.update_data(
        amount=str(amount),
    )
    await state.set_state(WithDrawFSM.waiting_card)
    await message.answer('💳 Enter your payout card number:', reply_markup=inl.cancel_withdraw)
    

@router.message(WithDrawFSM.waiting_card)
async def withdraw_waiting_card(message: Message, state: FSMContext):
    data = await state.get_data()
    
    method = data.get('method')
    amount = data.get('amount')

    if not method:
        await message.answer('method')
        return

    config = {
        'card_ua': 'Card UA🇺🇦',
        'card_eu': 'CARD EU🇪🇺'
    }
    
    card = message.text
    if not card:
        await message.answer('❌ Please enter a valid card number!', reply_markup=inl.cancel_withdraw)
        return 
    
    card = card.replace(' ', '')
    text = f'''
📝 <b>Withdrawal Request</b>

💳 <b>Method:</b> {config.get(method)}
💵 <b>Amount:</b> ${amount}
🏦 <b>Card:</b> <tg-spoiler>{card}</tg-spoiler>

👇<i>Please confirm your withdrawal below</i>
'''
    
    try: 
        if not card.isdigit() or len(card) != 16:
            raise ValueError
        else:
            await state.update_data(card=card)
            await state.set_state(WithDrawFSM.confirm)
            await message.answer(text, reply_markup=inl.withdraw_confirm, parse_mode='HTML')
    except ValueError:
        await message.answer('❌ Please enter a valid card number!!', reply_markup=inl.cancel_withdraw)
        return 
    

@router.callback_query(Withdraw.filter(F.action == 'confirm'))
async def clb_confirm_withdraw(
    callback: CallbackQuery, 
    state: FSMContext, 
    user_in_db: User, 
    session: AsyncSession,
    bot: Bot,
    group_id: int
):
    data = await state.get_data()
    
    method = data.get('method')
    amount = data.get('amount')
    card = data.get('card')

    if method is None or amount is None or card is None:
        await callback.answer('❌ Missing withdrawal data.', show_alert=True)
        return

    await state.clear()
    tg_id = user_in_db.tg_id
    
    withdraw_id, result = await req.create_withdraw(
        tg_id,
        method,
        card,
        amount,
        session
    )
    
    if result == False and isinstance(callback.message, Message):
        await callback.message.edit_text('❌ Error submitting request. Please tap /start and try again.')
        await callback.answer()
        await state.clear()
        return
    
    keyboard = inl.adm_withdraw_confirm(withdraw_id=withdraw_id)
    text = f'''
⚠️ <b>New Withdrawal Request:</b> #{withdraw_id}

💳 <b>Method:</b> {method}
💵 <b>Amount:</b> ${amount}
🏦 <b>Card:</b> <tg-spoiler>{card}</tg-spoiler>

👇 <i>Select action:</i>
'''

    if result == True:
        await bot.send_message(
            chat_id=group_id,
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        await state.clear()
        if isinstance(callback.message, Message):
            raw_text = callback.message.html_text
            clean_text = raw_text.split('👇')[0].strip()
            await callback.message.edit_text(f'{clean_text}', reply_markup=None, parse_mode='HTML')
            await callback.message.answer('⏳ Your withdrawal request is being processed.')
            
    
    await callback.answer()


@router.callback_query(Withdraw.filter(F.action == 'cancel'))
async def clb_cancel_withdraw(callback: CallbackQuery, state: FSMContext):
    text = '🚫 Withdrawal cancelled.'
    if isinstance(callback.message, Message):
        await state.clear()
        await callback.message.edit_text(text)
    await callback.answer()
    
    
@router.callback_query(WithdrawAdmin.filter(F.action.in_({'confirm', 'cancel'})))
async def clb_withdrawadmin_conf(
    callback: CallbackQuery, 
    callback_data: WithdrawAdmin,
    session: AsyncSession,
    bot: Bot,
):
    admin_id = callback.from_user.id
    admin = await req.get_user(session, admin_id)
    if admin is None or admin.role != 'admin':
        await callback.answer(
            '⛔ You do not have permission to perform this action',
            show_alert=True 
            )
        return
    
    
    status = (callback_data.action == 'confirm')
    withdraw_id = callback_data.withdraw_id
    
    user_id, result = await req.adminwithdraw(session, withdraw_id, status)

    if not result:
        await callback.answer("❌ Action failed or request already processed!", show_alert=True)
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                f"{callback.message.text}\n\n⚠️ <b>Status:</b> Processing Error",
                reply_markup=None,
                parse_mode='HTML'
            )
        return
    
    if status:
        admin_status = "✅ <b>Processed Successfully</b>"
        user_notify_text = '✅ <b>Withdrawal Approved!</b>\nPlease expect the funds to arrive within 1-2 hours.'
    else:
        admin_status = "❌ <b>Rejected</b>"
        user_notify_text = '❌ <b>Withdrawal Rejected.</b>\nFunds have been returned to your balance. If you believe this is an error, please contact support.'
    
    if isinstance(callback.message, Message):
        raw_text = callback.message.html_text
        clean_text = raw_text.split('👇')[0].strip()
        
        admin = callback.from_user.username or callback.from_user.id
        await callback.message.edit_text(
            f"{clean_text}\n\n {admin_status} @{admin}",
            reply_markup=None,
            parse_mode='HTML'
        )
     
    if user_id:   
        try:
            await bot.send_message(
                chat_id=user_id,
                text = user_notify_text,
                parse_mode='HTML'
            )
        except Exception as e:  # noqa: BLE001
            print(f'Failed to notify user {user_id}: {e}')
    await callback.answer()