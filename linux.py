import asyncio
import re
from collections import deque
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import aiosqlite
from datetime import datetime, timedelta, timezone
import time

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)


API_TOKEN = '7518633518:AAGPpzuNc-zfTJORqU0HtysJtT2maMvZ6ww'
CHAI_URL = 'https://web.chai-research.com/chat/_bot_84f03ba4-5c22-432c-953b-bb2d9ea5e87b_jeujvN95MYfkLAND1KvUkgooqJr1_1746539448341'
EDGE_DRIVER_PATH = "/root/money/msedgedriver"
DB_PATH = "users.db"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

import tempfile
import shutil
import atexit

def create_edge_driver():
    service = Service(EDGE_DRIVER_PATH, log_path="msedgedriver.log")
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--headless=new")  # Можно убрать если нужен GUI

    # Уникальный временный профиль
    profile_dir = tempfile.mkdtemp(prefix="edge_profile_")
    options.add_argument(f"--user-data-dir={profile_dir}")

    # Гарантированно удаляем профиль после завершения
    def cleanup():
        shutil.rmtree(profile_dir, ignore_errors=True)
    atexit.register(cleanup)

    driver = webdriver.Edge(service=service, options=options)
    return driver

driver = create_edge_driver()
wait = WebDriverWait(driver, 30)


def google_login(email, password):
    driver.get("https://accounts.google.com/signin")
    email_input = wait.until(EC.element_to_be_clickable((By.ID, "identifierId")))
    email_input.clear()
    email_input.send_keys(email)
    driver.find_element(By.ID, "identifierNext").click()
    # Ждём появления поля пароля
    password_input = WebDriverWait(driver,120).until(EC.element_to_be_clickable((By.NAME, "Passwd")))
    for char in password:
        password_input.send_keys(char)
        time.sleep(0.1)
    driver.find_element(By.ID, "passwordNext").click()
    wait.until(EC.url_contains("myaccount.google.com"))
    print("Вход в Google выполнен успешно!")

def chai_login_via_google():
    driver.get("https://web.chai-research.com/")
    wait = WebDriverWait(driver, 30)
    time.sleep(2)

    explore_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//div[contains(@class, 'inline-flex') and .//p[text()='EXPLORE NOW']]"
    )))
    explore_btn.click()
    print("Кнопка 'EXPLORE NOW' нажата.")

    google_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[contains(., 'Google')]"
    )))
    google_btn.click()
    print("Кнопка 'Continue with Google' нажата.")

    time.sleep(2)
    print("Открытые окна:", driver.window_handles)

    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        print("Переключились на окно выбора аккаунта Google")

        try:
            account_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-identifier]"))
            )
            account_btn.click()
            print("Аккаунт Google выбран.")
            time.sleep(2)
        except Exception as e:
            print("Не удалось выбрать аккаунт Google:", e)

        driver.switch_to.window(driver.window_handles[0])
        print("Переключились обратно на основное окно")
    else:
        print("Окно выбора аккаунта Google не открылось, возможно уже залогинены")

    driver.get(CHAI_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
    print("Вход в Chai AI завершён, открыт чат с персонажем.")

DB_PATH = "users_chats.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_chats (
                user_id INTEGER PRIMARY KEY,
                chat_url TEXT NOT NULL,
                last_active TEXT NOT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                user_id INTEGER,
                character TEXT,
                timestamp TEXT
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                subscription TEXT,
                until TEXT
            );
        """)
        await db.commit()

async def save_user_chat(user_id: int, chat_url: str):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_chats (user_id, chat_url, last_active)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                chat_url=excluded.chat_url,
                last_active=excluded.last_active
        """, (user_id, chat_url, now))
        await db.commit()

async def get_user_chat(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_url FROM user_chats WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def update_last_active(user_id: int):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE user_chats SET last_active = ? WHERE user_id = ?", (now, user_id))
        await db.commit()

async def delete_user_chat(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_chats WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_all_user_chats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, chat_url, last_active FROM user_chats") as cursor:
            return await cursor.fetchall()


user_tabs = {}      # user_id -> window_handle
user_greeted = {}   # user_id -> bool
messages_in_queue = {}  # user_id -> int
message_queue = deque()

def escape_markdown_v2(text: str) -> str:
    special_chars = r'_*\[\]()~`>#+-=|{}.!\\'
    return re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)

def escape_inside_em(text: str) -> str:
    special_chars = r'*[]()~`>#+-=|{}.!\\'
    return re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)

def convert_em_to_markdown_italic(html_text: str) -> str:
    soup = BeautifulSoup(html_text, 'html.parser')
    for em_tag in soup.find_all('em'):
        em_text = em_tag.get_text()
        escaped_em_text = escape_inside_em(em_text)
        em_tag.string = f"_{escaped_em_text}_"
        em_tag.unwrap()
    text = soup.get_text()
    parts = re.split(r'(_.*?_)', text)
    for i, part in enumerate(parts):
        if not part.startswith('_'):
            parts[i] = escape_markdown_v2(part)
    return ''.join(parts)

def strip_markdown(text: str) -> str:
    return re.sub(r'[*_~`]', '', text).strip()


def send_message_to_chai(text: str, max_attempts: int = 3) -> str:
    try:
        wait = WebDriverWait(driver, 30)
        # Всегда ищем input_box заново перед каждым действием!
        input_box = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "textarea")))
        driver.execute_script("arguments[0].scrollIntoView(true);", input_box)
        input_box.clear()

        # Получаем количество сообщений до отправки
        bot_messages_before = driver.find_elements(By.CSS_SELECTOR, "div.rounded-t-lg")
        len_before = len(bot_messages_before)
        input_box.send_keys(text)
        input_box.send_keys(Keys.ENTER)

        # Ждём ответа с несколькими попытками
        for attempt in range(max_attempts):
            timeout = 30
            poll_interval = 0.5
            elapsed = 0
            while elapsed < timeout:
                time.sleep(poll_interval)
                elapsed += poll_interval
                # Ищем элементы ЗАНОВО каждый раз!
                bot_messages_after = driver.find_elements(By.CSS_SELECTOR, "div.rounded-t-lg")
                len_after = len(bot_messages_after)
                if len_after > len_before:
                    last_text_after = bot_messages_after[-1].text.strip()
                    if last_text_after and strip_markdown(last_text_after) != strip_markdown(text):
                        return last_text_after
            print(f"Попытка {attempt + 1}: ответ не получен, пробуем ещё раз...")
        return "Не удалось получить ответ от Chai AI."
    except Exception as e:
        return f"Ошибка: {e}"


    except Exception as e:
        return f"Ошибка: {e}"


def get_or_create_tab(user_id, chat_url):
    if user_id in user_tabs:
        try:
            driver.switch_to.window(user_tabs[user_id])
            if not driver.current_url.startswith(chat_url):
                driver.get(chat_url)
            return
        except Exception:
            del user_tabs[user_id]  # Удаляем нерабочие хэндлы

    driver.execute_script("window.open('about:blank');")
    new_tab = driver.window_handles[-1]
    driver.switch_to.window(new_tab)
    driver.get(chat_url)
    user_tabs[user_id] = new_tab





@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    chat_url = CHAI_URL  # Можно генерировать уникальную ссылку, если нужно
    get_or_create_tab(user_id, chat_url)
    await save_user_chat(user_id, chat_url)
    user_greeted[user_id] = False  # Сбросим приветствие для нового чата

    # Приветствие
    bot_messages = driver.find_elements(By.CSS_SELECTOR, "div.rounded-t-lg")
    if bot_messages:
        greeting_html = bot_messages[-1].get_attribute('innerHTML')
        formatted_greeting = convert_em_to_markdown_italic(greeting_html)
        await message.answer(formatted_greeting, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await message.answer("Подожди немного, идёт загрузка.\n Нажми /start")
    user_greeted[user_id] = True

async def process_message(user_id, text, message_obj):
    chat_url = await get_user_chat(user_id)
    get_or_create_tab(user_id, chat_url)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, send_message_to_chai, text)
    formatted_response = convert_em_to_markdown_italic(response)
    await message_obj.answer(formatted_response, parse_mode=ParseMode.MARKDOWN_V2)

    # Логируем только если реально получили ответ
    if not response.startswith("Ошибка"):
        await log_message(user_id, "char_yuki")

    # Уменьшаем счётчик сообщений в очереди
    if user_id in messages_in_queue:
        messages_in_queue[user_id] -= 1
        if messages_in_queue[user_id] <= 0:
            del messages_in_queue[user_id]

async def queue_worker():
    while True:
        if message_queue:
            user_id, text, message_obj = message_queue.popleft()
            try:
                await process_message(user_id, text, message_obj)
            except Exception as e:
                print(f"Ошибка: {e}. Возвращаем сообщение в очередь.")
                message_queue.appendleft((user_id, text, message_obj))  # Возвращаем обратно
                await asyncio.sleep(5)  # Пауза перед повторной попыткой
        else:
            await asyncio.sleep(0.1)

@dp.message(F.from_user.is_bot == False)
async def handle_message(message: types.Message):
    if message.text and message.text.startswith('/'):
        return
    user_id = message.from_user.id

    chat_url = await get_user_chat(user_id)
    if not chat_url:
        await message.answer("Напиши /start для создания чата!")
        return

    get_or_create_tab(user_id, chat_url)
    await update_last_active(user_id)

    # Приветствие (если нужно)
    if not user_greeted.get(user_id, False):
        bot_messages = driver.find_elements(By.CSS_SELECTOR, "div.rounded-t-lg")
        if bot_messages:
            greeting_html = bot_messages[-1].get_attribute('innerHTML')
            formatted_greeting = convert_em_to_markdown_italic(greeting_html)
            await message.answer(formatted_greeting, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await message.answer("Привет! Я готов общаться с тобой.")
        user_greeted[user_id] = True

    # Лимиты и очередь
    count_in_db = await messages_today(user_id)
    count_in_queue = messages_in_queue.get(user_id, 0)
    total_count = count_in_db + count_in_queue

    if total_count >= 60:
        await message.answer("🚫 Лимит 60 сообщений на сегодня исчерпан!\nКупите подписку для безлимита.")
        return

    messages_in_queue[user_id] = count_in_queue + 1
    message_queue.append((user_id, message.text, message))

import asyncio
from datetime import datetime, timedelta, timezone

async def cleanup_task():
    while True:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        rows = await get_all_user_chats()
        for user_id, chat_url, last_active_str in rows:
            last_active = datetime.fromisoformat(last_active_str)
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            if last_active < cutoff:
                if user_id in user_tabs:
                    try:
                        driver.switch_to.window(user_tabs[user_id])
                        driver.close()
                    except Exception as e:
                        print(f"Ошибка при закрытии вкладки пользователя {user_id}: {e}")
                    del user_tabs[user_id]
                await delete_user_chat(user_id)
                print(f"Закрыт чат пользователя {user_id} из-за неактивности.")
        await asyncio.sleep(800)  # Проверять каждые 10 минут




async def log_message(user_id: int, character: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, character, timestamp) VALUES (?, ?, ?)",
            (user_id, character, datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

async def messages_today(user_id: int):
    today = datetime.now(timezone.utc).date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id=? AND date(timestamp)=?",
            (user_id, today)
        ) as cursor:
            count = (await cursor.fetchone())[0]
    return count

async def can_send_message(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT subscription, until FROM users WHERE user_id=?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
    if row and row[0] == "Active" and row[1] and datetime.fromisoformat(row[1]) > datetime.now(timezone.utc).isoformat():
        return True, None  # Безлимит
    count = await messages_today(user_id)
    return count < 60, 60 - count


async def main():
    await init_db()
    chai_login_via_google()
    asyncio.create_task(cleanup_task())
    print("Бот запущен. Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    google_login("tgmoney109@gmail.com", "Ker010203")
    chai_login_via_google()
    asyncio.run(main())

