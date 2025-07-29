import asyncio
import logging
import os
import sqlite3

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile

BOT_TOKEN = "6668788537:AAFmwHuuJkn9g_DUQeIZ-dXZYN-hfkPL_IQ"

PDF_FOLDER_PATH = 'product_files/'
logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

all_products = [
    "Назад", "Общая презентация", "Российские акции", "Российские акции вне НРД",
    "Российские IPO SPO", "Российские акции 120_80", "Международные облигации", "Российские облигации",
    "Валютные облигации с выплатой дохода", "Хедж-фонд А+", "Хедж-фонд Р5", "Хедж-фонд Д5",
    "Хедж-фонд Ю5", "Хедж-фонд Д1", "Хедж-фонд Р1", "Мгновенная ликвидность" ,"Хедж фонды", "Результаты фондов",
    "Сравнение с индексами", "Тарифы"
]

phone_number = None

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


# Функция для создания клавиатуры администратора
def get_admin_menu():
  buttons = ["Добавить пользователя", "Презентации"]
  kb = [[types.KeyboardButton(text=button)] for button in buttons]
  keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
  return keyboard


def get_unlogin_menu():
  buttons = ["Ввести номер телефона"]
  kb = [[types.KeyboardButton(text=button)] for button in buttons]
  keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
  return keyboard


class AddingUser(StatesGroup):
  name = State()
  admin = State()

  @dp.message(lambda message: message.text == "Добавить пользователя")
  async def ask_user_tel(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите username или номер пользователя в формате 89876543210")
    await state.set_state(AddingUser.name)


@dp.message(AddingUser.name)
async def get_user_tel(message: types.Message, state: FSMContext):
  await state.update_data(name=message.text)
  global name
  name = message.text
  await message.answer("Выберите роль пользователя:")
  await message.answer(
      "1 - если пользовтель администратор, \n0 - если пользователь не администратор"
  )
  await state.set_state(AddingUser.admin)


@dp.message(AddingUser.admin, F.text.in_(['1', '0']))
async def user_role(message: types.Message, state: FSMContext):
  await state.update_data(admin=message.text)
  add_user(name, message.text)
  await message.answer("Пользователь успешно добавлен",
                       reply_markup=get_admin_menu())
  await state.clear()


@dp.message(AddingUser.admin)
async def user_role_incorrectly(message: types.Message, state: FSMContext):
  await message.answer("Введите значение 1 или 0")


class RequestPhoneNumber(StatesGroup):
  phone_number = State()


@dp.message(lambda message: message.text == "Ввести номер телефона")
async def request_phone_number(message: types.Message, state: FSMContext):
  await message.answer(
      "Пожалуйста, введите ваш номер телефона (в формате 89876543210):")
  await state.set_state(RequestPhoneNumber.phone_number)


@dp.message(RequestPhoneNumber.phone_number)
async def get_tel(message: types.Message, state: FSMContext):
  await state.update_data(phone_number=message.text)
  global phone_number
  phone_number = message.text
  await message.answer(f"Ваш номер телефона: {phone_number} успешно получен.")
  await state.clear()


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
  user_name = message.from_user.username

  if user_name == None:
    user_name = phone_number

  if not is_registered(user_name) and not is_admin(user_name):
    await message.answer(
        "Извините, у вас нет доступа к этому боту.\n"
        "Для того чтобы получить доступ, обратитесь к администратору.")
    await message.answer("Ваш username: " + str(user_name),
                         reply_markup=get_unlogin_menu())
    return

  if is_admin(user_name):
    await message.answer("Привет, Админ! Добро пожаловать в Админ-панель.",
                         reply_markup=get_admin_menu())
  else:
    await message.answer("Привет! Добро пожаловать в бота.",
                         reply_markup=get_main_menu())


@dp.message(lambda message: message.text == "Презентации")
async def show_files(message: types.Message):
  user_name = message.from_user.username

  if not is_registered(user_name) and not is_admin(user_name):
    await message.answer(
        "Извините, у вас нет доступа к этому боту.\n"
        "Для того чтобы получить доступ, обратитесь к администратору.")
  else:
    buttons = all_products
    kb = [[types.KeyboardButton(text=button)] for button in buttons]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите продукт")
    await message.answer("Выберите стратегию для просмотра презентаций:",
                         reply_markup=keyboard)


@dp.message(lambda message: message.text == "Назад")
async def menu_handler(message: types.Message):
  if message.text == "Назад":
    if is_admin(message.from_user.username):
      await message.answer("Главное меню:", reply_markup=get_admin_menu())
    else:
      await message.answer("Главное меню:", reply_markup=get_main_menu())


@dp.message(lambda message: message.text in all_products)
async def pdf_search(message: types.Message):
  product_name = message.text
  c = 0
  if product_name in all_products:
    await message.answer(f"Презентации для продукта: {product_name}")
    for file_name in os.listdir(PDF_FOLDER_PATH):
      if file_name.endswith('.pdf') and product_name in file_name:
        file_path = os.path.join(PDF_FOLDER_PATH, file_name)
        pdf_file = FSInputFile(path=file_path)
        await bot.send_document(message.from_user.id, pdf_file)
        c += 1
  else:
    await message.answer(
        "Пожалуйста, выберите продукт из предложенных вариантов.")
  if c == 0:
    await message.answer("Файлы не найдены")


# Обработчик команды для добавления пользователя (только для администраторов)


async def main():
  await dp.start_polling(bot)


# keep_alive()

if __name__ == "__main__":
  asyncio.run(main())
