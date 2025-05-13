#HOST-BOT
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from datetime import datetime, timedelta
import aiosqlite

API_TOKEN = '7621155080:AAHzny1K5nkx6maGqFHpWU3oiiAykvIX5P0'  # Вставь свой токен

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
DB_PATH = "users.db"

# Главное меню
start_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💳 Get a subscription", callback_data="subscribe")],
        [InlineKeyboardButton(text="💬 Buy Messages + Photos 🖼️", callback_data="buy_messages")],
        [
            InlineKeyboardButton(text="🎭 Characters", callback_data="characters"),
            InlineKeyboardButton(text="👤 My Account", callback_data="account")
        ],
        [InlineKeyboardButton(text="🛟 Get support", callback_data="support")]
    ]
)

# Меню персонажей
characters_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Юки 🌸", callback_data="char_yuki")],
        [InlineKeyboardButton(text="Харука 🔥", callback_data="char_haruka")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
)

# Меню оплаты
payment_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Pay by card 💳", callback_data="pay_card")],
        [InlineKeyboardButton(text="Pay by Telegram Stars ⭐", callback_data="pay_stars")],
        [InlineKeyboardButton(text="<- Main menu", callback_data="back_to_main")]
    ]
)

# Данные персонажей с фото
CHARACTERS = {
    "char_yuki": {
        "name": "Юки 🌸",
        "description": (
            "Юки - милая и застенчивая аниме-девушка, всегда поддержит беседу и поднимет настроение.\n"
            "Возраст: 19 лет\n"
            "Характер: добрая, романтичная, немного стеснительная.\n"
        ),
        "link": "https://t.me/lustchai_yuki_tsukumo_bot",
        "photo": "https://i.imgur.com/your_yuki_photo.jpg"
    },
    "char_haruka": {
        "name": "Харука 🔥",
        "description": (
            "Харука - энергичная и страстная, любит флирт и весёлые разговоры.\n"
            "Возраст: 21 год\n"
            "Характер: смелая, харизматичная, любит приключения.\n"
        ),
        "link": "https://t.me/haruka_ai_bot",
        "photo": "https://i.imgur.com/your_haruka_photo.jpg"
    }
}

SUBSCRIPTION_PRICE = 1  # В Stars или рублях
SUBSCRIPTION_DESCRIPTION = "30-дневная подписка на всех компаньонов. Неограниченные сообщения и фото!"

# --- БАЗА ДАННЫХ ---

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                subscription TEXT DEFAULT 'None',
                until TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                character TEXT,
                timestamp TEXT
            )
        ''')
        await db.commit()
        logging.info("Database initialized")


async def set_subscription(user_id: int, status: str, until: datetime = None):
    until_str = until.isoformat() if until else None
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO users (user_id, subscription, until)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                subscription=excluded.subscription,
                until=excluded.until
        ''', (user_id, status, until_str))
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT subscription, until FROM users WHERE user_id=?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                subscription, until = row
                until_dt = datetime.fromisoformat(until) if until else None
                return {"subscription": subscription, "until": until_dt}
            else:
                return {"subscription": "None", "until": None}

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start")) or ()
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id) #  Получение пользователя из базы данных
    if not user:
        await set_subscription(user_id, "None", None)
    text = (
        "✨ Познакомьтесь с идеальными спутниками!💖\n\n"
        "🌹 Увлекательные беседы, созданные специально для вас.\n"
        "💌 Общайтесь с помощью сообщений с любимыми персонажами.\n"
        "💞 Ваш спутник ждёт вас, чтобы подарить радость, близость и яркие эмоции.\n"
        "✨ Откройте для себя захватывающий опыт с нашими AI-компаньонами, созданными, чтобы скрасить ваш день."
    )
    await message.answer(text, reply_markup=start_menu)
@dp.callback_query()
async def handle_callbacks(callback: types.CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id
    if data == "subscribe":
        await callback.message.answer(
            "Select your preferred payment method:\n\nCredit Card 💳 or Telegram Stars ⭐",
            reply_markup=payment_menu
        )
    elif data == "pay_card":
        tribute_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить через Tribute(tribute пока не работает)", url="https://t.me/tribute")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="subscribe")]
            ]
        )
        await callback.message.answer(
            "💳 Для оплаты картой мы используем сервис Tribute.\n\n"
            "• Безопасные платежи\n"
            "• Поддержка карт большинства банков\n"
            "• Автоматическое подключение подписки\n\n"
            "Нажмите кнопку ниже, чтобы перейти к оплате:\n\n"
            'TRIBUTE ПОКА ЧТО В РАЗРАБОТКЕ,\nВОСПОЛЬЗУЙТЕСЬ ДРУГИМИ СПОСОБАМИ',
            reply_markup=tribute_keyboard
        )
    elif data == "pay_stars":
        try:
            await bot.send_invoice(
                chat_id=callback.from_user.id,
                title="Подписка на 30 дней",
                description=SUBSCRIPTION_DESCRIPTION,
                payload="subscription_30_days",
                provider_token="",  # Для XTR (Stars) токен не нужен
                currency="XTR",  # Валюта - звёзды Telegram
                prices=[LabeledPrice(label="Premium Subscription", amount=SUBSCRIPTION_PRICE)],
                start_parameter="subscription",
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                is_flexible=False
            )
            await callback.answer()
        except Exception as e:
            await callback.message.answer(f"Ошибка при создании платежа: {str(e)}")
    elif data == "buy_messages":
        await callback.message.answer("💬 Покупка сообщений и фото скоро будет доступна!")
    elif data == "characters":
        await callback.message.answer("🎭 Выберите персонажа:", reply_markup=characters_menu)
    elif data == "account":
        user = await get_user(user_id)
        subscription = user.get("subscription", "None")
        until = user.get("until")
        until_str = until.strftime("%Y-%m-%d %H:%M") if until else "-"
        count = await messages_today(user_id)
        print(f"[DEBUG] User {user_id} sent {count} messages today.")
        left = "∞" if subscription == "Active" and until and until > datetime.now() else str(60 - count)
        text = (
            f"<b>ID:</b> <code>{user_id}</code>\n"
            f"📜 <b>Subscription:</b> {subscription}\n"
            f"⏳ <b>Until:</b> {until_str}\n"
            f"💬 <b>Messages left today:</b> {left}"
        )
        await callback.message.answer(text, parse_mode="HTML")
    elif data == "support":
        await callback.message.answer("🛟 Поддержка: напишите @your_support_username")
    elif data in CHARACTERS:
        char = CHARACTERS[data]
        char_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Перейти к боту", url=char["link"])],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="characters")]
            ]
        )
        await callback.message.answer_photo(
            photo=char["photo"],
            caption=f"**{char['name']}**\n\n{char['description']}",
            reply_markup=char_keyboard,
            parse_mode="Markdown"
        )
    elif data == "back_to_main":
        await callback.message.answer( "✨ Познакомьтесь с идеальными спутниками!💖\n\n"
        "🌹 Увлекательные беседы, созданные специально для вас.\n"
        "💌 Общайтесь с помощью сообщений с любимыми персонажами.\n"
        "💞 Ваш спутник ждёт вас, чтобы подарить радость, близость и яркие эмоции.\n"
        "✨ Откройте для себя захватывающий опыт с нашими AI-компаньонами, созданными, чтобы скрасить ваш день."
, reply_markup=start_menu)
    await callback.answer()
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
@dp.message(lambda message: message.successful_payment)
async def process_successful_payment(message: types.Message):
    user_id = message.from_user.id
    until = datetime.now() + timedelta(days=30)
    await set_subscription(user_id, "Active", until)
    await message.answer(
        f"✅ Платёж успешно выполнен!\n\n"
        f"Ваша подписка активирована до <b>{until.strftime('%Y-%m-%d %H:%M')}</b>!\n"
        f"Теперь вы можете общаться со всеми персонажами без ограничений.",
        parse_mode="HTML"
    )

async def messages_today(user_id: int):
    today = datetime.now().date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id=? AND date(timestamp)=?",
            (user_id, today)
        ) as cursor:
            count = (await cursor.fetchone())[0]
    return count



@dp.message()
async def any_text_message(message: types.Message):
    text = (
        "✨ Познакомьтесь с идеальными спутниками!💖\n\n"
        "🌹 Увлекательные беседы, созданные специально для вас.\n"
        "💌 Общайтесь с помощью сообщений с любимыми персонажами.\n"
        "💞 Ваш спутник ждёт вас, чтобы подарить радость, близость и яркие эмоции.\n"
        "✨ Откройте для себя захватывающий опыт с нашими AI-компаньонами, созданными, чтобы скрасить ваш день."
    )
    await message.answer(text, reply_markup=start_menu)

async def main():
    await init_db()
    await dp.start_polling(bot)
if __name__ == '__main__':
    asyncio.run(main())
