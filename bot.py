import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
import pandas as pd
import os

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSGAzkrHzLNGq8vfOWc6lBr-7EjORyCyYrHBehlVpC377cu9ac0vhQq90NwFwXjY0XBu2I6UjWFxJjB/pub?output=csv"

def load_products():
    df = pd.read_csv(SHEET_URL)

    products = {}

    for _, row in df.iterrows():
        if str(row["available"]).lower() == "yes":
            products[row["product"]] = (
                row["opt3"],
                row["opt10"],
                row["retail"]
            )

    return products

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных среды")

user_last_product = {}
waiting_for_quantity = {}
products_cache = {}
last_update = 0

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏸 Каталог"), KeyboardButton(text="💳 Умови оплати і доставки")],
            [KeyboardButton(text="📞 Наші контакти")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_catalog_menu():
    products = load_products()
    keyboard = []
    buttons = [KeyboardButton(text=p) for p in products.keys()]

    for i in range(0, len(buttons), 2):
        keyboard.append(buttons[i:i + 2])

    keyboard.append([KeyboardButton(text="⬅ Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

async def catalog_handler(message: Message):
    await message.answer(
        "Оберіть товар:",
        reply_markup=get_catalog_menu()
    )

async def back_handler(message: Message):
    await message.answer(
        "Головне меню:",
        reply_markup=get_main_menu()
    )

async def product_handler(message: Message):
    products = load_products()

    if message.text in products:
        user_last_product[message.from_user.id] = message.text
        opt3, opt10, retail = products[message.text]

        text = (
            f"<b>{message.text}</b>\n\n"
            f"🏭 Гурт від 3 туб — {opt3} грн\n\n"
            f"🏬 Гурт від 10 туб — {opt10} грн\n\n"
            f"🛍 Роздріб — {retail} грн"
        )

        await message.answer(
            text,
            reply_markup=get_order_button(),
            parse_mode="HTML"
        )

def get_order_button():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Оформити замовлення")],
            [KeyboardButton(text="⬅ Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard


async def order_handler(message: Message):
    user_id = message.from_user.id

    if user_id in user_last_product:
        waiting_for_quantity[user_id] = True
        await message.answer("Вкажіть кількість туб:")
    else:
        await message.answer("Спочатку оберіть товар.")

async def quantity_handler(message: Message, bot: Bot):
    user_id = message.from_user.id

    if waiting_for_quantity.get(user_id):

        if not message.text.isdigit():
            await message.answer("Будь ласка, введіть число.")
            return

        quantity = message.text
        product = user_last_product.get(user_id, "Невідомо")

        username = message.from_user.username
        first_name = message.from_user.first_name

        text = (
            "📦 Нова заявка!\n\n"
            f"Товар: {product}\n"
            f"Кількість: {quantity} туб\n"
            f"Ім'я: {first_name}\n"
            f"Username: @{username}\n"
            f"ID: {user_id}"
        )

        await bot.send_message(chat_id=-1003774581808, text=text)

        await message.answer("Дякуємо за ваш вибір! Наш менеджер зв'яжется з Вами протягом дня 😊")

        # очищаем состояние
        waiting_for_quantity.pop(user_id)

async def start_handler(message: Message):
    await message.answer(
        "Вітаємо в нашому магазині!",
        reply_markup=get_main_menu()
    )

async def delivery_handler(message: Message):
    text = (
        "🚚 <b>Доставка по всій Україні</b>\n\n"
        "⚡ Відправка в день замовлення\n"
        "📦 Компанією \"Нова Пошта\" — 1–2 дні\n\n"
        
        "💳 <b>Оплата</b>\n\n"
        "💵 Післяплата\n"
        "💳 Visa / MasterCard\n"
        "🏦 Банківський переказ на ФОП\n"
        "💰 Готівкою\n\n"
        "✅ Гарантія якості"
    )
    await message.answer(text, parse_mode="HTML")

async def contacts_handler(message: Message):
    await message.answer("Наші контакти:\nТелефон: +380992626780\n"
                         "Instagram: https://www.instagram.com/yuliiavavdichyk_lingmei/\n"
                         "Telegram: @Yuliia_Vavdichyk")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(catalog_handler, F.text == "🏸 Каталог")
    dp.message.register(delivery_handler, F.text == "💳 Умови оплати і доставки")
    dp.message.register(contacts_handler, F.text == "📞 Наші контакти")
    dp.message.register(back_handler, F.text == "⬅ Назад")
    dp.message.register(order_handler, F.text == "🛒 Оформити замовлення")
    dp.message.register(product_handler, F.text)
    dp.message.register(quantity_handler)



    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())