from aiogram.filters.callback_data import CallbackData


class Payments(CallbackData, prefix='pay'):
    action: str
    method: str = 'None'
    amount: int = 0
    
class AdminReceipt(CallbackData, prefix='admin_rec'):
    action: str
    usd_amount: str
    user_id: int
    pay_method: str
    
class Withdraw(CallbackData, prefix='withdraw'):
    action: str
    method: str = 'None'
    amount: int = 0
    
class WithdrawAdmin(CallbackData, prefix='withdraw_admin'):
    action: str
    withdraw_id: int = 0
    
class GameMode(CallbackData, prefix='game_mode'):
    mode: str
    
class CountGame(CallbackData, prefix='count_game'):
    count: int

class GameAmount(CallbackData, prefix='amount'):
    amount: int | None 
    
class GameAgain(CallbackData, prefix='again'):
    amount: str
    mode: str
    rounds: int
    