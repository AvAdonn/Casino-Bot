from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🎮 Play')],
    [KeyboardButton(text='💰 My Wallet'), 
     KeyboardButton(text='My Profile 🆔')],
    [KeyboardButton(text='🔗 Referrals'), 
     KeyboardButton(text='About Bot 🤖')]
], 
resize_keyboard=True,
input_field_placeholder="Your move..."
)

