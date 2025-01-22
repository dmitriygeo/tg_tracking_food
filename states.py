from aiogram.fsm.state import StatesGroup, State

class Profilestates(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    MET = State()
    city = State()

class Foodstates(StatesGroup):
    amount = State()
