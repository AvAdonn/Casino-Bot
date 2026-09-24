from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder  # noqa: F401

from src.casino_bot.callback import (
    AdminReceipt,
    GameMode,
    Payments,
    Withdraw,
    WithdrawAdmin,
    GameAmount,
    CountGame,
)

back_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Back to menu ⬅️', callback_data='back_to_menu')]
])

pay_withdraw = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text='Deposit 📥',
        callback_data=Payments(action='deposit').pack()
        ),
    InlineKeyboardButton(
        text='Cash out 📤',
        callback_data=Payments(action='withdraw').pack()
        )],
    [InlineKeyboardButton(text='Back to menu ⬅️', callback_data='back_to_menu')]
])

choise_pay = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text='Card UAH 🇺🇦',
        callback_data=Payments(action='pay', method='card_ua').pack()
    ),
    InlineKeyboardButton(
        text='Card EU 🇪🇺',
        callback_data=Payments(action='pay', method='card_eu').pack()
    )],
    [InlineKeyboardButton(
        text='CryptoBot 🤖',
        callback_data=Payments(action='pay', method='crypto').pack()
    ),
    InlineKeyboardButton(
        text='Stars ⭐️',
        callback_data=Payments(action='pay', method='stars').pack()
    )],
    [InlineKeyboardButton(
        text='Back ⬅️',
        callback_data=Payments(action='back_to_wallet').pack()
    )]
])

pay_stars = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text='50 ⭐️',
        callback_data=Payments(action='pay_stars', amount=50).pack()
    ),
    InlineKeyboardButton(
            text='500 ⭐️',
            callback_data=Payments(action='pay_stars', amount=500).pack()
        )],
    [InlineKeyboardButton(
            text='100 ⭐️',
            callback_data=Payments(action='pay_stars', amount=100).pack()
        ),
    InlineKeyboardButton(
            text='1000 ⭐️',
            callback_data=Payments(action='pay_stars', amount=1000).pack()
        )],
    [InlineKeyboardButton(
            text='200 ⭐️',
            callback_data=Payments(action='pay_stars', amount=200).pack()
        ),
    InlineKeyboardButton(
            text='2000 ⭐️',
            callback_data=Payments(action='pay_stars', amount=2000).pack()
        )],
    [InlineKeyboardButton(
            text='Other amount ✍️',
            callback_data=Payments(action='pay_stars').pack()
        )],
    [InlineKeyboardButton(
            text='Back ⬅️',
            callback_data=Payments(action='deposit').pack()
        )]
])

cancel_pay = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
            text='❌ Cancel',
            callback_data=Payments(action='deposit').pack()
        )]
])


def confirm_eu_ua(user_id: int, amount: str, pay_method: str) -> InlineKeyboardMarkup:
    approve_btn = InlineKeyboardButton(
        text='🟢Approve',
        callback_data=AdminReceipt(
            action='approve',
            user_id=user_id,
            usd_amount=amount,
            pay_method=pay_method
            ).pack()
    )
    reject_btn = InlineKeyboardButton(
        text='🔴Reject',
        callback_data=AdminReceipt(
            action='reject',
            user_id=user_id,
            usd_amount=amount,
            pay_method=pay_method
            ).pack()
    )
    
    return InlineKeyboardMarkup(inline_keyboard=[[approve_btn, reject_btn]])


withdraw = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text='Card UAH 🇺🇦',
        callback_data=Withdraw(action='withdraw', method='card_ua').pack()
        ),
     InlineKeyboardButton(
        text='Card EU 🇪🇺',
        callback_data=Withdraw(action='withdraw', method='card_eu').pack() 
    )],
    [InlineKeyboardButton(
        text='CryptoBot 🤖',
        callback_data=Withdraw(action='withdraw', method='crypto').pack()
    )],
    [InlineKeyboardButton(
        text='Back ⬅️',
        callback_data=Payments(action='back_to_wallet').pack()
    )]
])

cancel_withdraw = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
            text='❌ Cancel',
            callback_data=Payments(action='withdraw').pack()
        )]
])


withdraw_confirm = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text='🟢Confirm',
        callback_data=Withdraw(
            action='confirm'
        ).pack()
    ),
     InlineKeyboardButton(
         text='🔴Cancel',
         callback_data=Withdraw(
             action='cancel'
         ).pack()
     )]
])

def adm_withdraw_confirm(withdraw_id: int) -> InlineKeyboardMarkup:
    confirm = InlineKeyboardButton(
        text='🟢Approve',
        callback_data=WithdrawAdmin(
            action='confirm',
            withdraw_id=withdraw_id
        ).pack()
    )
    reject = InlineKeyboardButton(
        text='🔴Reject',
        callback_data=WithdrawAdmin(
            action='cancel',
            withdraw_id=withdraw_id
        ).pack()
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [confirm, reject]
        ]
    )
    
    
game = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text='🎲 Dice', 
        callback_data=GameMode(mode='🎲').pack()
        ),
    InlineKeyboardButton(
        text='🎯 Darts', 
        callback_data=GameMode(mode='🎯').pack()
        )],
    [InlineKeyboardButton(
        text='🏀 Basketball', 
        callback_data=GameMode(mode='🏀').pack()
        ),
    InlineKeyboardButton(
        text='⚽ Football', 
        callback_data=GameMode(mode='⚽️').pack()
        )],
    [InlineKeyboardButton(
        text='🎳 Bowling', 
        callback_data=GameMode(mode='🎳').pack()
        ),
    InlineKeyboardButton(
        text='🎰 Slots', 
        callback_data=GameMode(mode='🎰').pack()
        )],
    [InlineKeyboardButton(
        text='🔥 Grand Match', 
        callback_data=GameMode(mode='BigGame').pack()
        )],
    [InlineKeyboardButton(
        text='Back to menu ⬅️', 
        callback_data='back_to_menu'
        )],
    
])

count_game = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text='1️⃣ Round',
        callback_data=CountGame(count=1).pack()
    ),
    InlineKeyboardButton(
        text='3️⃣ Rounds',
        callback_data=CountGame(count=5).pack()
    )],
    [InlineKeyboardButton(
        text='🔟 Rounds',
        callback_data=CountGame(count=10).pack()
    )],
    [InlineKeyboardButton(
        text='Back ⬅️',
        callback_data='back_to_mode'
    )]
])

game_amount = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text='1 $',
        callback_data=GameAmount(amount=1).pack()
    ),
    InlineKeyboardButton(
        text='3 $',
        callback_data=GameAmount(amount=3).pack()
    )],
    [InlineKeyboardButton(
        text='5 $',
        callback_data=GameAmount(amount=5).pack()
    ),
    InlineKeyboardButton(
        text='10 $',
        callback_data=GameAmount(amount=10).pack()
    )],
    [InlineKeyboardButton(
        text='Other amount💸',
        callback_data='other_amount'
    )],
    [InlineKeyboardButton(
        text='Back ⬅️',
        callback_data='back_to_rounds'
    )],
])


cancel_amount = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
            text='❌ Cancel',
            callback_data='back_to_mode'
        )]
])