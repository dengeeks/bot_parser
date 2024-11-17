from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile, InputMediaPhoto
from aiogram.utils.media_group import MediaGroupBuilder

from config import MEDIA_PATH
from const import START_MESSAGE
from keyboards.start import back_to_menu_keyboard, start_menu_keyboard
from services.togis import run_parse_2gis
from services.validate_links import check_is_links_valid
from services.yandex import run_yandex_parser

router = Router()
# паттерны для валидации
pattern_2gis = r"^https?://(www\.)?2gis\.ru(/.*)?$"
pattern_yandex = r"^https?://(www\.)?yandex(\.ru|\.com)?(/.*)?$"


# Определяем состояния
class ParseStates(StatesGroup):
    waiting_for_yandex_links = State()
    waiting_for_2gis_links = State()


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(call: types.CallbackQuery):
    # вернутся в меню
    photo_path = MEDIA_PATH + "DALL·E 2024-11-16 22.47.15 - A dynamic and visually engaging animation showing the concept of parsing Yandex and 2GIS organizations. The scene includes abstract representations of.webp"

    photo = FSInputFile(photo_path)

    media = InputMediaPhoto(media = photo, caption = START_MESSAGE)

    await call.message.edit_media(
        media = media,
        parse_mode = 'HTML',
        reply_markup = await start_menu_keyboard()
    )


@router.callback_query(F.data.startswith('parse_'))
async def callback_handler(call: types.CallbackQuery, state: FSMContext):
    """ принимаем ссылки для парсинга """
    source = call.data.split("_")[1]
    print(source)

    current_state = await state.get_state()
    if current_state in [ParseStates.waiting_for_yandex_links, ParseStates.waiting_for_2gis_links]:
        # Если пользователь уже в состоянии ввода ссылок, не обрабатываем новые нажатия
        await call.answer("Вы уже в процессе парсинга. Пожалуйста, завершите текущий процесс.")
        return

    if source == "yandex":
        await call.message.answer("🔎 Введите ссылки для парсинга с Яндекса:")
        await state.set_state(ParseStates.waiting_for_yandex_links)  # Устанавливаем состояние
    elif source == "2gis":
        await call.message.answer("🗺️ Введите ссылки для парсинга с 2ГИС:")
        await state.set_state(ParseStates.waiting_for_2gis_links)  # Устанавливаем состояние

    return None


# Обработка ссылок для Яндекс и 2гис
@router.message(ParseStates.waiting_for_yandex_links)
async def yandex_links_handler(message: types.Message, state: FSMContext):
    links = message.text.split("\n")

    # проверка ссылки на валидность
    all_correct, links = await check_is_links_valid(links, pattern = pattern_yandex)

    if not all_correct:
        await state.clear()
        return message.answer(
            text = links,
            parse_mode = 'HTML',
            reply_markup = await back_to_menu_keyboard()
        )

    files = await run_yandex_parser(links, message.from_user.id)

    await message.answer('Парсинг успешно завершен !!!')
    media_group = MediaGroupBuilder()
    if files:
        for media in files:
            media_group.add_document(media)
        await message.answer_media_group(media = media_group.build())

    # Завершаем состояние
    await state.clear()


@router.message(ParseStates.waiting_for_2gis_links)
async def gis_links_handler(message: types.Message, state: FSMContext):
    links = message.text.split("\n")

    # проверка ссылки на валидность
    all_correct, links = await check_is_links_valid(links, pattern = pattern_2gis)

    if not all_correct:
        await state.clear()
        return message.answer(
            text = links,
            parse_mode = 'HTML',
            reply_markup = await back_to_menu_keyboard()
        )

    files = await run_parse_2gis(links,message.from_user.id)

    await message.answer('Парсинг успешно завершен !!!')
    media_group = MediaGroupBuilder()
    if files:
        for media in files:
            media_group.add_document(media)
        await message.answer_media_group(media = media_group.build())


    # Завершаем состояние
    await state.clear()
