import asyncio
import gc
import io
import re
from datetime import datetime
from urllib.parse import unquote, urlparse, parse_qs

import pandas as pd
from aiogram.types import BufferedInputFile
from loguru import logger
from playwright.async_api import async_playwright, Playwright

from config import bot


class ToGisParser:
    current_datetime = datetime.now()

    def __init__(self, playwright: Playwright):
        """
            Инициализация браузера
            :param playwright:
        """
        self.firefox = playwright.firefox
        self.files = []

    async def create_page(self):
        try:
            context = await self.browser.new_context(
                locale = "ru-RU"
            )
            page = await context.new_page()

            await page.route(
                re.compile(r".*\.(jpg|png|jpeg|webp)$"),
                lambda route: route.abort()
            )
            return page
        except Exception as new_page_error:
            logger.error(f'ошибка при открытии новой страницы : {new_page_error}')
            return None

    async def parse_url(self, url):
        parsed_url = urlparse(url)

        path_parts = parsed_url.path.strip('/').split('/')

        search_term = None
        city = None

        if len(path_parts) > 1 and path_parts[0] != 'search':
            city = path_parts[0]

        if 'search' in path_parts:
            search_term = unquote(path_parts[path_parts.index('search') + 1])
        try:
            query_params = parse_qs(parsed_url.query)
            coordinates = query_params.get('m', [None])[0]
        except:
            coordinates = None

        return city, search_term, coordinates

    async def parse(self, links, chat_id):
        count = 0
        try:
            for link in links:
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
                data = []
                page = await self.create_page()
                if not page:
                    continue

                try:

                    try:
                        await page.goto(link, wait_until = 'domcontentloaded')
                        await asyncio.sleep(5)
                        cookie = await page.query_selector("//button[@class='_jro6t0']")
                        if cookie:
                            await cookie.click()
                    except Exception as e:
                        logger.error(e)

                    try:
                        elements_count = await page.query_selector("//span[@class='_1xhlznaa']")
                        elements_count = int(await elements_count.text_content())
                    except:
                        elements_count = 0

                    count_links = len(links)
                    mess_id = await bot.send_message(
                        chat_id = chat_id,
                        text = f"Начался процесс парсинга...\n\nСейчас собираются все организации по ссылке\n{link}\n\nВыполняется - {count}/{count_links}"
                    )

                    try:
                        request = await page.query_selector('//*[contains(@placeholder, "Поиск в 2ГИС")]')
                        request = str(await request.get_attribute('value'))
                    except:
                        request = ''

                    count += 1
                    count_proccess = 0
                    while True:
                        organization_elements = await page.query_selector_all(
                            "//div[@class='_1kf6gff']"
                        )
                        if not organization_elements:
                            organization_elements = await page.query_selector_all(
                                "//html/body/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/div/div/div/div[not(@class)]"
                            )

                        for organization_element in organization_elements:
                            try:
                                await organization_element.click()
                                await asyncio.sleep(0.5)
                                cookie = await page.query_selector("//button[@class='_jro6t0']")
                                if cookie:
                                    await cookie.click()
                            except Exception as e:
                                continue

                            try:
                                ORGANIZATION_TITLE = await page.query_selector("//h1[@class='_cwjbox']/span")
                                ORGANIZATION_TITLE = str(await ORGANIZATION_TITLE.text_content()).replace(
                                    '\u00A0', ' '
                                ).replace(
                                    '\u200B', ''
                                )
                            except:
                                ORGANIZATION_TITLE = ""

                            try:
                                ADDRESS = await page.query_selector(
                                    "//div[@class='_172gbf8'][1]//div[@class='_13eh3hvq']/div/div[1]"
                                )
                                ADDRESS = str(await ADDRESS.text_content()).replace('\u00A0', ' ').replace('\u200B', '')

                                if not ADDRESS:
                                    ADDRESS = await page.query_selector(
                                        "//span[@class='_oqoid']"
                                    )
                                    ADDRESS = await ADDRESS.text_content()
                            except:
                                ADDRESS = ''

                            try:
                                AREA = await page.query_selector("//div[@class='_1p8iqzw']")
                                AREA = await AREA.text_content()
                            except:
                                AREA = ''

                            region = ''
                            city = ''
                            if AREA:
                                try:
                                    region = AREA.split(',')[-2]
                                except:
                                    region = ''

                                try:
                                    city = ', '.join(AREA.split(',')[:-2])
                                except:
                                    city = ''

                            try:
                                SITE = await page.query_selector_all(
                                    "//div[@class='_49kxlr']//a[contains(@href, 'https')]"
                                )
                                SITE = ', '.join([await i.get_attribute('href') for i in SITE])
                            except:
                                SITE = ''

                            try:
                                WHATSAPP = await page.query_selector_all(
                                    "//div[@class='_2fgdxvm']//a[contains(@aria-label, 'WhatsApp')]"
                                )
                                WHATSAPP = ', '.join([await i.get_attribute('href') for i in WHATSAPP])
                            except:
                                WHATSAPP = ''

                            try:
                                TELEGRAM = await page.query_selector_all(
                                    "//div[@class='_2fgdxvm']//a[contains(@aria-label, 'Telegram')]"
                                )
                                TELEGRAM = ', '.join([await i.get_attribute('href') for i in TELEGRAM])
                            except:
                                TELEGRAM = ''

                            try:
                                phone_button = await page.query_selector(
                                    "//*[contains(@class, '_1y2y99m') and (contains(text(), 'Показать телефон') or contains(text(), 'Показать телефоны'))]"
                                )
                                await phone_button.click(timeout = 50000)
                                await asyncio.sleep(1)

                                TELEPHONE = await page.query_selector_all(
                                    "//div[@class='_49kxlr']//bdo"
                                )
                                TELEPHONE = [await i.text_content() for i in TELEPHONE]
                                TELEPHONE = '; '.join(TELEPHONE).replace(' ', '').replace('(', '').replace(
                                    ')', ''
                                ).replace(
                                    '-', ''
                                )
                            except:
                                TELEPHONE = ''

                            # Почта
                            try:
                                EMAIL = await page.query_selector(
                                    "//*[contains(@class, '_2lcm958') and contains(text(), '@')]"
                                )
                                EMAIL = await EMAIL.text_content()
                            except:
                                EMAIL = ''

                            try:
                                work_time_button = await page.query_selector(
                                    "//div[2][@class='_172gbf8']//div[@class='_z3fqkm']"
                                )

                                WORK_TIME = []
                                if work_time_button:
                                    await work_time_button.click()
                                    await asyncio.sleep(1)

                                    day = await page.query_selector_all("//div[@class='_z3iodz']/div[1]")
                                    day = [str(await i.text_content()).replace('\u00A0', ' ').replace('\u200B', '') for
                                           i in
                                           day]

                                    time = await page.query_selector_all("//div[@class='_z3iodz']/div[2]")
                                    time = [str(await i.text_content()).replace('\u00A0', ' ').replace('\u200B', '') for
                                            i
                                            in
                                            time]

                                    for day, time in zip(day, time):
                                        WORK_TIME.append(f'{day} : {time}')

                                else:
                                    work_time = await page.query_selector(
                                        "//div[@class='_172gbf8']//div[@class='_18zamfw']"
                                    )
                                    work_time = str(await work_time.text_content()).replace('\u00A0', ' ').replace(
                                        '\u200B', ''
                                    )

                                    WORK_TIME.append(work_time)

                                WORK_TIME = '; '.join(WORK_TIME)
                            except:
                                WORK_TIME = ''

                            data.append(
                                {
                                    'Название организации': ORGANIZATION_TITLE,
                                    'Адрес': ADDRESS,
                                    'Регион': region,
                                    'Населенный пункт': city,
                                    'Телефон': TELEPHONE,
                                    'Whatsapp': WHATSAPP,
                                    'Telegram': TELEGRAM,
                                    'Site': SITE,
                                    'Почта': EMAIL,
                                    'Рабочее время': WORK_TIME,
                                    'Запрос': request
                                }
                            )

                            logger.info(ORGANIZATION_TITLE)
                            count_proccess += 1
                            if count_proccess % 5 == 0:
                                await bot.edit_message_text(
                                    chat_id = chat_id,
                                    message_id = mess_id.message_id,
                                    text = f"Сейчас парсятся организации из запроса\n{link}\n\nВсего организаций найдено: {elements_count}\nВсего организаций уже спарсено: {count_proccess}"
                                )
                        gc.collect()
                        next_page = await page.query_selector(
                            "//html/body/div[2]/div/div/div[1]/div[1]/div[3]/div/div/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/div/div[3]/div[2]/div[2]"
                        )
                        try:
                            if next_page:
                                await next_page.click(timeout = 50000)
                                await asyncio.sleep(2)
                            else:
                                break
                        except Exception as e:
                            logger.error(e)
                            break
                finally:
                    await page.close()
                    await self.browser.close()
                    await self.save_to_excel(data)
        finally:
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


async def run_parse_2gis(links, chat_id):
    async with async_playwright() as playwright:
        parse_2gis = ToGisParser(playwright)
        await parse_2gis.main(links, chat_id)
        return parse_2gis.files
