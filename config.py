# файл конфиг бота

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config

storage = MemoryStorage()
TOKEN = config('TOKEN')
bot = Bot(token = TOKEN)
dp = Dispatcher()

# MEDIA
MEDIA_PATH = './media/'
