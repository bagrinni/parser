import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputMediaPhoto
from aiogram.filters import Command
from aiogram import F
from aiohttp import web
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = '7809115494:AAHSe9imJdXIcnfPV2aAEDa32lxZyw084Ec'
bot = Bot(token=BOT_TOKEN, timeout=10)
dispatcher = Dispatcher()

# Глобальная переменная для драйвера
driver = None  # Инициализируем driver как None

def create_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium_stealth import stealth

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Google Inc.",
            renderer="ANGLE (NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)",
            fix_hairline=True)
    return driver

def get_driver():
    global driver
    if driver is None:
        driver = create_driver()
    return driver

def close_driver():
    global driver
    if driver:
        driver.quit()
        driver = None

def parse_wildberries(url):
    driver = get_driver()
    try:
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.product-gallery'))
        )

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.swiper-slide'))
        )

        images = set()
        swiper_slides = driver.find_elements(By.CSS_SELECTOR, '.swiper-slide')

        max_slides = 50
        count = 0

        for slide in swiper_slides:
            if count >= max_slides:
                break

            try:
                data_ind = slide.get_attribute('data-ind')
                img_elements = slide.find_elements(By.CSS_SELECTOR, 'img.swiper-slide__img')

                for img_element in img_elements:
                    img_src = img_element.get_attribute('src')

                    if img_src and img_src not in images:
                        images.add(img_src)
                        logger.info(f"Найдено изображение с data-ind={data_ind}: {img_src}")
                    elif img_src:
                        logger.info(f"Изображение с data-ind={data_ind} уже добавлено: {img_src}")
                    else:
                        logger.warning(f"Изображение не найдено в блоке с data-ind={data_ind}")

                count += 1
            except Exception as e:
                logger.warning(f"Ошибка при обработке блока с data-ind={data_ind}: {e}")

        if not images:
            logger.error("Не удалось найти изображения на странице.")

        return {'images': list(images)}

    except Exception as e:
        logger.error(f"Ошибка при парсинге Wildberries: {e}")
        return {'error': f"Ошибка при парсинге Wildberries: {e}"}

@dispatcher.message(Command('start'))
async def start_message(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на товар с Wildberries, и я пришлю изображения.")

@dispatcher.message(F.text.startswith('http'))
async def handle_link(message: types.Message):
    logger.info(f"Получен запрос от пользователя {message.from_user.id} с URL: {message.text}")
    url = message.text.strip()
    await message.reply("Начинаю парсинг... Подождите.")
    try:
        result = parse_wildberries(url)
        if 'error' in result:
            await message.reply(f"Ошибка: {result['error']}")
        else:
            images = result['images']
            if images:
                await message.reply(f"Найдено {len(images)} изображений. Отправляю...")

                media_group = [InputMediaPhoto(media=img) for img in images[:10]]  # Ограничение на 10 изображений
                await message.answer_media_group(media=media_group)
            else:
                await message.reply("Изображения не найдены.")
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса от пользователя {message.from_user.id}: {str(e)}")
        await message.reply(f"Произошла ошибка: {str(e)}")

@dispatcher.message(Command('close'))
async def close_driver_message(message: types.Message):
    close_driver()
    await message.reply("Драйвер закрыт. Бот остановлен.")

async def on_start(request):
    update = types.Update(**await request.json())
    await dispatcher.process_update(update)
    return web.Response()

async def on_shutdown(request):
    close_driver()
    return web.Response()

async def set_webhook():
    url = f"https://parser-yxqp.onrender.com/webhook"  # Ваш URL Render
    await bot.set_webhook(url)

async def main():
    await set_webhook()

    app = web.Application()
    app.router.add_get('/webhook', on_start)
    app.router.add_post('/webhook', on_start)

    port = os.getenv('PORT', 8080)
    logging.info(f"Бот запущен на порту {port}")
    web.run_app(app, port=port)

if __name__ == '__main__':
    asyncio.run(main())
