import asyncio
import io
import re
from datetime import datetime

import pandas as pd
from aiogram.types import BufferedInputFile
from loguru import logger
from playwright.async_api import async_playwright, Playwright

from config import bot


class AsyncYandexParse:
    current_datetime = datetime.now()

    def __init__(self, playwright: Playwright):
        self.firefox = playwright.firefox
        self.files = []

    async def create_page(self):
        try:

            context = await self.browser.new_context(
                locale = "ru-RU"
            )
            page = await context.new_page()
            await page.route(
                re.compile(
                    r"(avatars\.mds\.yandex\.net|frontend\.vh\.yandex\.ru|core-renderer-tiles\.maps\.yandex\.net|.*\.(jpg|png|svg|avif|webp|mp4|webm))"
                ),
                lambda route: route.abort()
            )
            return page

        except Exception as new_page_error:
            logger.error(f'ошибка при открытии новой страницы : {new_page_error}')
            return None

    async def parse(self, links, chat_id):
        self.browser = await self.firefox.launch(
            headless = True,
            args = [
                '--no-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-plugins',
                '--single-process',

            ]
        )
        count = 0
        count_links = len(links)
        for link in links:
            count += 1
            mess_id = await bot.send_message(
                chat_id = chat_id,
                text = f"Начался процесс парсинга...\n\nСейчас собираются все организации по ссылке\n{link}\n\nВыполняется - {count}/{count_links}"
            )
            page = await self.create_page()
            if page is None:
                continue

            data = []
            try:
                # открытие ссылки
                try:
                    await page.goto(link, timeout = 60000)
                    await asyncio.sleep(15)
                except Exception as page_error:
                    logger.error(f'Ошибка при отправке запроса на ссылку {link}/ {page_error}')
                    continue

                # закрытие куков
                try:
                    button = await page.query_selector(
                        "//button[@class='close-button _color_white _size_medium _offset_small']"
                    )
                    if button:
                        await button.click()
                        await asyncio.sleep(0.5)
                except:
                    ...

                # скролл
                try:
                    last_height = await page.evaluate("document.querySelector('.scroll__container').scrollHeight")
                    same_height = 0
                    while same_height < 30:
                        await page.evaluate(
                            "document.querySelector('.scroll__container').scrollBy(0,2000);"
                        )
                        await asyncio.sleep(1)
                        new_height = await page.evaluate(
                            "document.querySelector('.scroll__container').scrollHeight"
                        )
                        if new_height == last_height:
                            same_height += 1
                        else:
                            same_height = 0
                            last_height = new_height
                except Exception as scroll_error:
                    logger.error(f'Ошибка при скролинге страницы: {scroll_error}')

                # извлечение всех организаций
                try:
                    businesses = await page.query_selector_all(
                        "//ul[@class='search-list-view__list']//li[@class='search-snippet-view']//a[@class='link-overlay']"
                    )
                    businesses = [f"https://yandex.com{await i.get_attribute('href')}" for i in businesses if i]
                except Exception as businesses_error:
                    # если ошибка пропускаем
                    logger.error(f'Ошибка при получении всех организаций: {businesses_error}')
                    continue

                # если нет организаций, пропускаем
                if not businesses:
                    continue

                try:
                    request = await page.query_selector("//span[@class='input__context']/input")
                    request = await request.get_attribute('value')
                except Exception as e:
                    print(e)
                    request = None

                await page.close()
                # детали организации
                processed_businesses = 0
                total_businesses = len(businesses)

                for i in businesses:
                    page = await self.create_page()
                    if page is None:
                        continue

                    try:
                        await page.goto(i, timeout = 60000, wait_until = 'domcontentloaded')
                    except Exception as detail_page_error:
                        try:
                            await page.close()
                            page = await self.create_page()
                        except:
                            logger.error(f'Ошибка при открытии деталей орг-ии: {detail_page_error}')
                            continue
                        # continue

                    # await asyncio.sleep(0.5)

                    try:
                        # title_organization_element = await page.query_selector(
                        #     ".card-title-view__title-link"
                        # )
                        title_organization_element = await page.query_selector(
                            "//h1[@class='orgpage-header-view__header']"
                        )
                        ORGANIZATION_TITLE = await title_organization_element.text_content()
                    except:
                        ORGANIZATION_TITLE = ''

                    try:
                        # address_element = await page.query_selector(
                        #     "//div[@class='business-contacts-view__address-link']"
                        # )
                        address_element = await page.query_selector(
                            "//a[@class='business-contacts-view__address-link']"
                        )
                        ADDRESS = await address_element.text_content()
                    except:
                        ADDRESS = ''

                    WORKING_TIME = []
                    try:
                        working_time_button = await page.query_selector(
                            "//div[@class='business-working-status-flip-view _clickable']"
                        )
                        if working_time_button:
                            await working_time_button.click()
                            await asyncio.sleep(1)

                        DAYS = await page.query_selector_all(
                            "//div[@class='business-working-intervals-view__item']/div[1]"
                        )

                        TIME = await page.query_selector_all(
                            "//div[@class='business-working-intervals-view__item']/div[2]"
                        )
                        if TIME and DAYS:
                            TIME = [await i.text_content() for i in TIME]
                            DAYS = [await i.text_content() for i in DAYS]

                            for day, time in zip(DAYS, TIME):
                                WORKING_TIME.append(f'{day} : {time}')
                            WORKING_TIME = '; '.join(WORKING_TIME)

                        close_button = await page.query_selector(
                            "//button[@class='close-button _color_black _circle _size_medium _offset_large']"
                        )
                        if close_button:
                            await close_button.click()

                        if WORKING_TIME == []:
                            WORKING_TIME = ''
                    except:
                        WORKING_TIME = ''

                    try:
                        phone_button = await page.query_selector(
                            "//div[@class='card-phones-view__more']"
                        )
                        if phone_button:
                            try:
                                await phone_button.click(timeout = 30000)
                            except:
                                pass

                        more_phone_button = await page.query_selector(
                            "//div[@class='card-phones-view']//div[@class='card-feature-view__arrow _view_down']"
                        )
                        if more_phone_button:
                            try:
                                await more_phone_button.click(timeout = 30000)
                            except:
                                pass

                        telephone_element = await page.query_selector_all(
                            "//div[@class='card-phones-view__phone-number']"
                        )
                        TELEPHONE = ', '.join([await i.text_content() for i in telephone_element])
                    except:
                        TELEPHONE = ''

                    try:
                        site_button = await page.query_selector(
                            "//div[contains(@class, 'card-feature-view') and contains(@class, '_view_normal') and contains(@class, '_size_small') and contains(@class, '_interactive')]//div[contains(@class, 'business-urls-view__url')]/ancestor::div[contains(@class, 'card-feature-view') and contains(@class, '_view_normal') and contains(@class, '_size_small') and contains(@class, '_interactive')]//div[@class='card-feature-view__additional']"
                        )
                        if site_button:
                            try:
                                await site_button.click(timeout = 30000)
                            except:
                                pass

                        SITE = await page.query_selector_all(
                            "//div[@class='business-urls-view__url']/a"
                        )
                        SITE = ', '.join([await i.get_attribute('href') for i in SITE])
                    except:
                        SITE = ''

                    if not SITE:
                        SITE = ''

                    try:
                        AREA = await page.query_selector(
                            "//meta[@itemprop='address']"
                        )
                        AREA = await AREA.get_attribute('content')
                    except:
                        AREA = ''

                    REGION = ''
                    CITY = ''

                    if AREA:
                        try:
                            REGION = AREA.split(',')[0]
                        except:
                            REGION = ''

                        try:
                            CITY = AREA.split(',')[1]
                        except:
                            CITY = ''

                    try:
                        TELEGRAM = await page.query_selector(
                            "//div[@class='business-contacts-view__social-button']/a[contains(@href, 't.me') or contains(@href, 'tg://')]"
                        )
                        TELEGRAM = await TELEGRAM.get_attribute('href')
                    except:
                        TELEGRAM = ''

                    try:
                        WHATSAPP = await page.query_selector(
                            "//div[@class='business-contacts-view__social-button']/a[contains(@href, 'wa.me') or contains(@href, 'api.whatsapp.com')]"
                        )
                        WHATSAPP = await WHATSAPP.get_attribute('href')
                    except:
                        WHATSAPP = ''

                    logger.info(f'Запрос: {request} / Название организации: {ORGANIZATION_TITLE}')

                    data.append(
                        {
                            'Название организации': ORGANIZATION_TITLE,
                            'Адрес': ADDRESS,
                            'Регион': REGION,
                            'Населенный пункт': CITY,
                            'Время работы': WORKING_TIME,
                            'Whatsapp': WHATSAPP,
                            'Telegram': TELEGRAM,
                            'Site': SITE,
                            'Телефон': TELEPHONE,
                            'Запрос': request
                        }
                    )
                    processed_businesses += 1
                    if processed_businesses % 5 == 0:
                        await bot.edit_message_text(
                            chat_id = chat_id,
                            message_id = mess_id.message_id,
                            text = f"Сейчас парсятся организации из запроса\n{link}\n\nВсего организаций найдено: {total_businesses}\nВсего организаций уже спарсено: {processed_businesses}"
                        )
                    await page.close()


            except Exception as unexpected_error:
                logger.error(unexpected_error)
            await page.close()
            await self.save_to_excel(data)
        return self.files

    async def save_to_excel(self, data):
        if data:
            df = pd.DataFrame(data)
            csv_buffer = io.StringIO()

            df.to_csv(csv_buffer, index = False)

            csv_buffer.seek(0)

            table_name = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.files.append(
                BufferedInputFile(
                    file = csv_buffer.getvalue().encode("utf-8"),
                    filename = f"{table_name}.csv",
                )
            )
            logger.info(self.files)

    async def main(self, links, chat_id):
        await self.parse(links, chat_id)


async def run_yandex_parser(links, chat_id):
    async with async_playwright() as playwright:
        yandex_parser = AsyncYandexParse(playwright)
        await yandex_parser.main(links, chat_id)
        return yandex_parser.files
