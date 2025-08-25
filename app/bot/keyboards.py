"""Telegram bot keyboards"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict

def get_start_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for start message"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Начать тест", callback_data="start_quiz")]
    ])

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Выбрать тест", callback_data="select_test")],
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="view_stats")],
    ])

def get_quiz_keyboard(options: List[Dict[str, str]]) -> InlineKeyboardMarkup:
    """Keyboard for quiz questions"""
    buttons = []
    
    # Add option buttons with just letters (A, B, C, etc.)
    for i, option in enumerate(options):
        button_text = f"{chr(65 + i)}"  # Just the letter: A, B, C, etc.
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"answer:{option['id']}"
        )])
    
    # Add main menu button
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_continue_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to continue to next question"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data="next_question")]
    ])

def get_finish_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for finished quiz"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Пройти еще раз", callback_data="start_quiz")],
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="view_stats")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Simple keyboard to return to main menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_test_selection_keyboard(tests: list) -> InlineKeyboardMarkup:
    """Test selection keyboard"""
    keyboard = []
    for test in tests:
        text = f"📝 {test['name']} ({test['questions_count']} вопросов)"
        callback_data = f"start_test:{test['id']}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    
    # Add back to menu button
    keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
