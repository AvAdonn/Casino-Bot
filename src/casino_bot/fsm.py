from aiogram.fsm.state import State, StatesGroup

class PaymentFSM(StatesGroup):
    waiting_sum = State()
    waiting_receipt = State()
    
    waiting_card = State()
    
class WithDrawFSM(StatesGroup):
    waiting_sum = State()
    waiting_card = State()
    confirm = State()
    
class GameAmountFSM(StatesGroup):
    waiting_amount = State()
    waiting_dice = State()