from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'))
    role: Mapped[str] = mapped_column(String, default='user')
    referral_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.tg_id', ondelete='SET NULL'), nullable=True, index=True)
    win: Mapped[int] = mapped_column(Integer, default=0)
    lose: Mapped[int] = mapped_column(Integer, default=0)
    total_played: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'))
    
    def __repr__(self) -> str:
        return f'<User(tg_id={self.tg_id}, balance={self.balance})>'
    
class Transaction(Base):
    __tablename__ = 'transactions'
    
    
    tg_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.tg_id', ondelete='CASCADE'))
    payment_method: Mapped[str] = mapped_column(String, default=None)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'))
    pay_id: Mapped[str] = mapped_column(String, default=None, primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    
    user = relationship('User', backref='transactions')
    
class WithDraw(Base):
    __tablename__ = 'withdraw'
    
    withdraw_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 
    tg_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.tg_id', ondelete='CASCADE'))
    withdraw_method: Mapped[str] = mapped_column(String, default=None)
    withdraw_details: Mapped[int] = mapped_column(BigInteger, default=0)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'))
    status: Mapped[str] = mapped_column(String, default='pending')
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    
    user = relationship('User', backref='withdraw')    
    

class Games(Base):
    __tablename__ = 'games'
    
    game_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.tg_id', ondelete='SET NULL'), nullable=True)
    mode: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    rounds: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default='pending')
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    
    user = relationship('User', backref='games')

