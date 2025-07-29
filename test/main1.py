import asyncio
import logging
import os
import sqlite3
import hashlib

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile

# from backround import keep_alive

BOT_TOKEN = "6668788537:AAFmwHuuJkn9g_DUQeIZ-dXZYN-hfkPL_IQ"

PDF_FOLDER_PATH = 'product_files/'
logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

all_products = [
    "Назад", "Общая презентация", "Российские акции", "Российские акции вне НРД",
    "Российские IPO SPO", "Международные облигации", "Российские облигации",
    "Валютные облигации с выплатой дохода", "Хедж-фонд А+", "Хедж-фонд Р5", "Хедж-фонд Д5",
    "Хедж-фонд Ю5", "Хедж-фонд Д1", "Мгновенная ликвидность", "Результаты фондов",
    "Инвестиционные результаты 2023", "Тарифы"
]

phone_number = None

def create_tables():
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_name TEXT PRIMARY KEY,
            is_admin INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_password_users (
            login TEXT PRIMARY KEY,
            password TEXT,
            is_admin INTEGER
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login_password(login, password):
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password, is_admin FROM login_password_users WHERE login = ?", (login,))
    result = cursor.fetchone()
    conn.close()
    if result:
        stored_password, is_admin = result
        return stored_password == hash_password(password), is_admin
    return False, False

def is_admin(user_name):
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE user_name = ?",
                   (user_name, ))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def is_registered(user_name):
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_name FROM users WHERE user_name = ?",
                   (user_name, ))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_user(user_name, user_role):
    conn = sqlite3.connect('db.db')
    conn.execute(
        "INSERT OR IGNORE INTO users (user_name, is_admin) VALUES (?, ?)",
        (user_name, user_role))
    conn.commit()
    conn.close()

def get_main_menu():
    buttons = ["Презентации"]
    kb = [[types.KeyboardButton(text=button)] for button in buttons]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard

def get_admin_menu():
    buttons = ["Добавить пользователя", "Презентации"]
    kb = [[types.KeyboardButton(text=button)] for button in buttons]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_name = message.from_user.username
    if is_registered(user_name):
        await message.answer("Вы успешно авторизованы.", reply_markup=get_main_menu())
    else:
        await message.answer("Введите ваш логин:")
        await LoginStates.login.set()

class LoginStates(StatesGroup):
    login = State()
    password = State()

@dp.message(LoginStates.login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Введите ваш пароль:")
    await LoginStates.password.set()

@dp.message(LoginStates.password)
async def process_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    login = data.get("login")
    password = message.text

    auth_success, is_admin = check_login_password(login, password)
    if auth_success:
        await message.answer("Вы успешно авторизованы.", reply_markup=get_main_menu())
        if is_admin:
            await message.answer("Вы авторизовались как администратор.", reply_markup=get_admin_menu())
    else:
        await message.answer("Неправильный логин или пароль.")
    await state.finish()

@dp.message(lambda message: message.text == "Добавить пользователя" and is_admin(message.from_user.username))
async def add_user_start(message: types.Message):
    buttons = ["Добавить по номеру телефона", "Добавить по логину и паролю"]
    kb = [[types.KeyboardButton(text=button)] for button in buttons]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Выберите способ добавления пользователя:", reply_markup=keyboard)

@dp.message(lambda message: message.text == "Добавить по номеру телефона" and is_admin(message.from_user.username))
async def add_user_by_phone(message: types.Message):
    await message.answer("Введите номер телефона нового пользователя:")
    await AddUserStates.phone.set()

class AddUserStates(StatesGroup):
    phone = State()
    role = State()
    login = State()
    password = State()

@dp.message(AddUserStates.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите роль пользователя (0 - обычный, 1 - админ):")
    await AddUserStates.role.set()

@dp.message(AddUserStates.role)
async def process_role_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    phone = data.get("phone")
    role = int(message.text)
    add_user(phone, role)
    await message.answer("Пользователь добавлен.")
    await state.finish()

@dp.message(lambda message: message.text == "Добавить по логину и паролю" and is_admin(message.from_user.username))
async def add_user_by_login_password(message: types.Message):
    await message.answer("Введите логин нового пользователя:")
    await AddUserStates.login.set()

@dp.message(AddUserStates.login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Введите пароль нового пользователя:")
    await AddUserStates.password.set()

@dp.message(AddUserStates.password)
async def process_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    login = data.get("login")
    password = hash_password(message.text)
    await state.update_data(password=password)
    await message.answer("Введите роль пользователя (0 - обычный, 1 - админ):")
    await AddUserStates.role.set()

@dp.message(AddUserStates.role)
async def process_role_login_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    login = data.get("login")
    password = data.get("password")
    role = int(message.text)
    conn = sqlite3.connect('db.db')
    conn.execute("INSERT OR IGNORE INTO login_password_users (login, password, is_admin) VALUES (?, ?, ?)", (login, password, role))
    conn.commit()
    conn.close()
    await message.answer("Пользователь добавлен.")
    await state.finish()

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
