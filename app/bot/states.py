"""FSM states for the bot"""

from aiogram.fsm.state import State, StatesGroup

class QuizStates(StatesGroup):
    """States for quiz flow"""
    waiting_for_name = State()
    in_quiz = State()
    viewing_results = State()
