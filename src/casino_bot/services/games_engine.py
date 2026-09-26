from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.casino_bot.database.models import User
from src.casino_bot.database.models import Games
from sqlalchemy import select

bowling_score = {
    1: 0,
    2: 1,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
}

win_set = {1, 22, 43, 64}

async def start_game(
    session: AsyncSession,
    mode: str,
    amount: Decimal,
    count: int,
    user: User,
) -> bool:
    try:
        if user.balance < amount:
            return False
        
        user.balance -= amount
        
        new_game = Games(
            tg_id=user.tg_id,
            mode=mode,
            amount=amount,
            rounds=count
        )
        session.add(new_game)
        
        await session.commit()
        return True
    
    except Exception as e:
        print(f'System error -> {e}')
        await session.rollback()
        return False
    
async def get_game(
    session: AsyncSession,
    user_id: int | None
) -> Games | None:
    if not user_id:
        return None
    try:
        game = await session.scalar(select(
            Games).where(
                Games.status == 'pending', Games.tg_id == user_id).order_by(
                    Games.game_id.desc()))
        return game
    except Exception as e:
        print(f'Some error -> {e}')
        return
    
def calculate_score(emoji: str, dice_value: int) -> int:
    if emoji in ('🏀', '⚽️'):
        return 1 if dice_value in (4, 5) else 0
    elif emoji == '🎳':
        return bowling_score.get(dice_value, 0)
    elif emoji == '🎯':
        return (dice_value - 1)
    elif emoji == '🎰':
        return 1 if dice_value in win_set else 0
    elif emoji == '🎲':
        return dice_value
    else:
        return 0


async def ending_game(
    game: Games,
    session: AsyncSession,    
    status: str,
    tg_id: int
) -> bool:
    try:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return False
        
        match status:
            case 'win':
                user.win += 1
                user.balance += game.amount * 2
                game.status = 'won'
            case 'lose':
                user.lose += 1
                game.status = 'lost'
            case 'draw':
                user.balance += game.amount
                game.status = 'draw'
            
        await session.commit()    
        return True
            
    except Exception as e:
        await session.rollback()
        print(f'Sys. error -> {e}')
        return False