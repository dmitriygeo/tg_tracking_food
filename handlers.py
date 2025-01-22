from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
import aiohttp
from states import Profilestates, Foodstates
from aiogram.fsm.context import FSMContext
from utils import calculate_water, calculate_calories
import data
from config import WEATHER_TOKEN, headers

router = Router()



@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Настройте ваш профиль\n"
        "/calculate - Расчет нормы воды и калорий\n"
        "/log_water - Запишите сколько вы выпили воды\n"
        "/log_food - Запишите сколько вы съели\n"
        "/log_workout - Запишите вашу тренировку\n"
        "/check_progress - Посмотрите ваш прогресс за день\n"
    )


@router.message(Command('set_profile'))
async def start_profile(message: Message, state: FSMContext):
    await message.reply('Введите ваш вес (в кг):')
    await state.set_state(Profilestates.weight)

@router.message(Profilestates.weight)
async def process_weight(message:Message, state: FSMContext):
    await state.update_data(weight=int(message.text))
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(Profilestates.height)

@router.message(Profilestates.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=int(message.text))
    await message.reply("Введите ваш возраст:")
    await state.set_state(Profilestates.age)

@router.message(Profilestates.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Profilestates.activity)

@router.message(Profilestates.activity)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=int(message.text))

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Сидячий",callback_data="btn1"),
        InlineKeyboardButton(text='Малоподвижный', callback_data='btn2'),
        InlineKeyboardButton(text='Подвижный', callback_data='btn3')
    )
    await message.reply("Укажите ваш образ жизни", reply_markup=builder.as_markup())
    await state.set_state(Profilestates.MET)

@router.callback_query()
async def callback_handler(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == 'btn1':
        await state.update_data(MET=3)
        await callback_query.message.answer('Вы выбрали сидячий образ жизни.')
    if callback_query.data == 'btn2':
        await state.update_data(MET=5)
        await callback_query.message.answer('Вы выбрали малоподвижный образ жизни')
    if callback_query.data == 'btn3':
        await state.update_data(MET=8)
        await callback_query.message.answer('Вы выбрали подвижный образ жизни')
    await callback_query.answer()
    await callback_query.message.answer("В каком городе вы находитесь?")
    await state.set_state(Profilestates.city)

@router.message(Profilestates.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.reply("Введите команду /calculate для расчета нормы воды и калорий")

    user_data = await state.get_data()
    data.users[message.from_user.id] = user_data
    await state.clear()

@router.message(Command('calculate'))
async def calculate(message: Message):
    id_user = message.from_user.id
    user_data = data.users.get(id_user, {})
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://api.openweathermap.org/data/2.5/weather?q={user_data['city']}&appid={WEATHER_TOKEN}&units=metric") as res:
            res = await res.json()
            temperature = res['main']['temp']
    water = calculate_water(user_data['weight'], user_data['activity'], temperature)
    calorie_goal = calculate_calories(user_data['weight'], user_data['height'], user_data['age'],
                                          user_data['activity'], user_data['MET'])

    user_data['water_goal'] = water
    user_data['calorie_goal'] = calorie_goal

    data.users[message.from_user.id] = user_data

    await message.answer(f"Ваш профиль сохранён! Ваша норма воды: {water} мл, Ваша норма калорий: {calorie_goal} ккал.")

@router.message(Command('log_water'))
async def log_water(message: Message):
    id_user = message.from_user.id
    count = int(message.text.split()[1])
    user_data = data.users.get(id_user, {})
    user_data['logged_water'] = user_data.get('logged_water', 0) + count
    await message.answer(f"Записано: {count} мл воды. Всего выпито: {user_data['logged_water']} мл.")

@router.message(Command('log_food'))
async def log_food(message: Message, state: FSMContext):
    food_name = message.text.split()[1]
    body = {
        "query": food_name,
        "timezone": "US/Eastern"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"https://trackapi.nutritionix.com/v2/natural/nutrients", json=body, headers=headers) as response:
            data = await response.json()
            products = data.get('foods', [])
            if products:
                first_products = products[0]
                kcal = first_products.get('nf_calories', {})
                grams = first_products.get('serving_weight_grams', {})
                kcal_per_100 = kcal/grams * 100
                await message.answer(f"{food_name} - {kcal_per_100:.1f} ккал на 100 г. Сколько грамм вы съели?")
                await state.update_data(food_name=food_name, kcal_per_100=kcal_per_100)
                await state.set_state(Foodstates.amount)
            else:
                await message.answer("К сожалению, Ваш продукт не найден. Попробуте другое название")

@router.message(Foodstates.amount)
async def set_food_amount(message: Message, state: FSMContext):
    id_user = message.from_user.id
    grams = int(message.text)
    user_data = await state.get_data()
    kcal_per_100 = user_data.get('kcal_per_100', 0)
    total_kcal = kcal_per_100 * grams / 100
    users = data.users.get(id_user, {})
    users['total_kcal'] = users.get('total_kcal', 0) + total_kcal
    await message.answer(f"Записано: {total_kcal:.1f} ккал.")
    await state.update_data(total_kcal=total_kcal)

    await state.clear()

@router.message(Command('log_workout'))
async def log_workout(message: Message, state: FSMContext):
    id_user = message.from_user.id
    workout = message.text.split()
    if len(workout) != 3:
        await message.answer('Неверный ввод. Введите в формате /log_workout <тип тренировки> <время (мин)>')
        return
    workout_type, workout_time = workout[1], int(workout[2])

    user_data = await state.get_data()
    weight = data.users[id_user]['weight']

    calories_burn = (workout_time) * (5 * 3.5 * weight) / 200
    water = (workout_time // 30) * 500
    users = data.users.get(id_user, {})
    users['calories_burn'] = users.get('calories_burn', 0) + calories_burn
    await state.update_data(burned_calories=user_data.get("burned_calories", 0) + calories_burn)
    await message.answer(f"{workout_type} {workout_time} минут — {calories_burn} ккал. Выпейте дополнительно {water} мл воды.")

@router.message(Command('check_progress'))
async def check_progress(message: Message):
    id_user = message.from_user.id
    user_data = data.users.get(id_user, {})

    progress = (
        f"📊Прогресс:\n"
        f"Вода:\n"
        f"- Выпито: {user_data.get('logged_water', 0)} мл из {user_data.get('water_goal', 0)} мл.\n"
        f"- Осталось: {user_data.get('water_goal', 0) - user_data.get('logged_water', 0)} мл.\n\n"
        f"Калории:\n"
        f"- Потреблено: {user_data.get('total_kcal', 0)} ккал из {user_data.get('calorie_goal', 0)} ккал.\n"
        f"- Сожжено: {user_data.get('calories_burn', 0)} ккал.\n"
        f"- Баланс: {user_data.get('total_kcal', 0) - user_data.get('calories_burn', 0)} ккал."
    )
    await message.answer(progress)


