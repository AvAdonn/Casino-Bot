import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.casino_bot.database.models import Transaction, User, WithDraw


async def get_user(
    session: AsyncSession, 
    tg_id: int
) -> User | None:
    if not tg_id:
        return None
    
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    
    return user


async def add_user(
    session: AsyncSession, 
    tg_id: int,
    referral_id: int | None
) -> None:
    
    
    new_user = insert(User).values(tg_id = tg_id, referral_id=referral_id)
    new_user = new_user.on_conflict_do_nothing(index_elements=['tg_id'])
    
    await session.execute(new_user)
    await session.commit()
    
    
async def process_star_payment(
    session: AsyncSession,
    tg_id: int,
    pay_id: str,
    stars_amount: int,
    usd_amount: Decimal
) -> None:
    try:
        user = await get_user(session, tg_id)
        if not user:
            return
        
        new_payment = Transaction(
            tg_id=tg_id,
            payment_method='stars',
            amount=stars_amount,
            pay_id=pay_id
        )
        
        session.add(new_payment)
        
        user.balance += usd_amount
            
        await session.commit()
    except Exception as e:
        print(f'Помилка нарахування -> {e}')
        await session.rollback()
        
    
async def process_ua_eu_payment(
    session: AsyncSession,
    tg_id: int,
    usd_amount: Decimal,
    pay_method: str,
) -> tuple[str, bool]: 
    
    pay_id = f'{pay_method}_{tg_id}_{uuid.uuid4().hex[:8]}'
    try:
        user = await get_user(session, tg_id)
        if not user:
            return '', False
        
        new_payment = Transaction(
            tg_id=tg_id,
            amount=usd_amount,
            pay_id=pay_id,
            payment_method=pay_method,
        )
        session.add(new_payment)
        
        user.balance += usd_amount
        await session.commit()
        
        return pay_id, True 
    
    except Exception as e:
        await session.rollback()
        print(f'Помилка проведення платежу {e}')
        return '', False
    
async def create_withdraw(
    tg_id: int,
    method: str,
    card: int,
    amount: str,
    session: AsyncSession
) -> tuple[int, bool]:
    
    dec_amount = Decimal(amount)
    
    try: 
        user =  await get_user(session, tg_id)
        if not user:
            return 0, False
        
        if user.balance < dec_amount:
            return 0, False
        
        new_withdraw = WithDraw(
            tg_id=tg_id,
            withdraw_method=method,
            withdraw_details=card,
            amount=dec_amount
        )
        session.add(new_withdraw)
            
        user.balance -= dec_amount
        await session.commit()
        
        return new_withdraw.withdraw_id, True
        
    except Exception:
        await session.rollback()
        return 0, False
    

async def adminwithdraw(
    session: AsyncSession,
    withdraw_id: int,
    admin_res: bool
) -> tuple[int, bool]:
    
    try:
        withdraw = await session.scalar(
            select(WithDraw).where(WithDraw.withdraw_id == withdraw_id)
        )
        
        if withdraw is None:
            return 0, False
        if withdraw.status != 'pending':
            return 0, False
        
        if not admin_res:
            user = await session.scalar(
                select(User).where(User.tg_id == withdraw.tg_id)
            )
            if not user:
                raise ValueError(f'Юзер {user}-відсутній при обробці заявки: {withdraw_id}')
            
            user.balance += withdraw.amount
            withdraw.status = 'rejected'
        else:
            withdraw.status = 'success'
            
        await session.commit()
        return withdraw.tg_id, True
        
    except Exception as e:
        print(f'Помилка виконання: {e}')
        await session.rollback()
        return 0, False
    

async def get_referral(
    session: AsyncSession,
    tg_id: int
    ) -> int:
    

    stmt = select(func.count(User.tg_id)).where(User.referral_id == tg_id)
        
    referral = await session.scalar(stmt)
        
    return referral or 0 

        
async def rate_check(
    session: AsyncSession,
    tg_id: int
) -> float | str:
    try:
        user = await get_user(session, tg_id)
        
        if not user:
            return 0

        
        total_games = user.lose + user.lose
        if total_games == 0:
            return 0
        
        rate = (user.win / total_games) * 100
        return round(rate, 2)
     
    except Exception as e:
        print(f'System error -> {e}')
        return 'Unknown'
    
async def add_game(
    session: AsyncSession,
    tg_id: int,
    mode: str,
    status: str,
    amounts: str,
    
) -> None:
    pass