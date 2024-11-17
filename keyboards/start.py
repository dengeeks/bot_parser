from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)


async def start_menu_keyboard():
    # стартовая клавиатура
    start_yandex = InlineKeyboardButton(
        text = 'YANDEX 🟡🔴⚪',
        callback_data = 'parse_yandex'
    )
    start_2gis = InlineKeyboardButton(
        text = '2GIS 🟢⚪',
        callback_data = 'parse_2gis'
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard = [
            [start_yandex, start_2gis],
        ]
    )
    return markup


async def back_to_menu_keyboard():
    # вернуться назад
    back_to_menu = InlineKeyboardButton(
        text = 'Вернутся в меню ◀️',
        callback_data = 'back_to_menu'
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard = [
            [back_to_menu],
        ]
    )
    return markup
