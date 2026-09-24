from aiogram import Router

from . import (
    about_bot,
    basic,
    games,
    payments,
    profile,
    referrals,
)


def get_routers() -> list[Router]:
    return [
        basic.router,
        profile.router,
        payments.router,
        about_bot.router,
        referrals.router,
        games.router,
    ]