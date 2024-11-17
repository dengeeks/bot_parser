from aiogram import Router, types
from aiogram.filters import Command

from config import MEDIA_PATH, bot
from const import START_MESSAGE
from keyboards.start import start_menu_keyboard
router = Router()


@router.message(Command('start'))
async def start(message: types.Message):
    # стартовое фото
    photo = types.FSInputFile(
        MEDIA_PATH +
        "DALL·E 2024-11-16 22.47.15 - A dynamic and visually engaging animation showing the concept of parsing Yandex and 2GIS organizations. The scene includes abstract representations of.webp"
    )

    await bot.send_photo(
        chat_id = message.from_user.id,
        photo = photo,
        caption = START_MESSAGE,
        parse_mode = 'HTML',
        reply_markup = await start_menu_keyboard()
    )
