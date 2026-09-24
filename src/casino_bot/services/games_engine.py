from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.casino_bot.database.models import User
from src.casino_bot.database.models import Games

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