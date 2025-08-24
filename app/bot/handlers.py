"""Telegram bot handlers"""

import logging
import aiohttp
import json
from typing import Optional, Dict, Any

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from .keyboards import (
    get_start_keyboard, get_quiz_keyboard, 
    get_continue_keyboard, get_main_menu_keyboard
)
from .texts import TEXTS
from .states import QuizStates
from ..core.config import settings

logger = logging.getLogger(__name__)

# Main router
router = Router()

# API base URL
API_BASE = f"http://localhost:{settings.api_port}"

async def api_request(method: str, url: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """Make API request"""
    try:
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(f"{API_BASE}{url}") as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        logger.error(f"API request failed: {response.status}")
                        return None
            elif method == "POST":
                headers = {"Content-Type": "application/json"}
                async with session.post(
                    f"{API_BASE}{url}", 
                    json=data, 
                    headers=headers
                ) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        logger.error(f"API request failed: {response.status}")
                        return None
    except Exception as e:
        logger.error(f"API request error: {e}")
        return None

def register_handlers(dp):
    """Register all handlers"""
    dp.include_router(router)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    
    user = message.from_user
    telegram_id = user.id
    
    # Check if user exists
    user_stats = await api_request("GET", f"/public/users/{telegram_id}/stats")
    
    if user_stats:
        # User exists, show welcome back message
        await message.answer(
            TEXTS["welcome_back"].format(
                name=user_stats["full_name"],
                attempts=user_stats["attempts"],
                best_score=user_stats["best_score_percent"]
            ),
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # New user, ask for registration
        await message.answer(TEXTS["welcome_new"])
        await state.set_state(QuizStates.waiting_for_name)

@router.message(QuizStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Process user's full name"""
    full_name = message.text.strip()
    
    # Simple validation for first name and last name
    name_parts = full_name.split()
    if len(name_parts) < 2:
        await message.answer(TEXTS["invalid_name"])
        return
    
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:])
    
    # Register user
    result = await api_request("POST", "/public/users/register", {
        "telegram_id": message.from_user.id,
        "first_name": first_name,
        "last_name": last_name
    })
    
    if result and result.get("success"):
        await state.clear()
        await message.answer(
            TEXTS["registration_success"].format(name=full_name),
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(TEXTS["registration_error"])

@router.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    """Start a new quiz"""
    await callback.answer()
    
    # Start session
    result = await api_request("POST", "/public/sessions/start", {
        "telegram_id": callback.from_user.id,
        "shuffle": True
    })
    
    if not result or not result.get("session_id"):
        await callback.message.edit_text(TEXTS["quiz_start_error"])
        return
    
    session_id = result["session_id"]
    total_questions = result["total"]
    
    # Save session ID in state
    await state.update_data(session_id=session_id)
    await state.set_state(QuizStates.in_quiz)
    
    # Get first question
    await send_next_question(callback.message, session_id, state)

@router.callback_query(F.data.startswith("answer:"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    """Process quiz answer"""
    await callback.answer()
    
    data = await state.get_data()
    session_id = data.get("session_id")
    
    if not session_id:
        await callback.message.edit_text(TEXTS["session_error"])
        return
    
    # Extract option ID
    option_id = callback.data.split(":", 1)[1]
    
    # Submit answer
    result = await api_request("POST", f"/public/sessions/{session_id}/answer", {
        "option_id": option_id
    })
    
    if not result:
        await callback.message.edit_text(TEXTS["answer_error"])
        return
    
    # Show feedback
    is_correct = result["is_correct"]
    comment = result["comment"]
    progress = result["progress"]
    
    feedback_text = TEXTS["answer_correct"] if is_correct else TEXTS["answer_incorrect"]
    feedback_text += f"\n\n💬 {comment}"
    feedback_text += f"\n\n📊 Прогресс: {progress['current']}/{progress['total']} (правильных: {progress['correct']})"
    
    # Check if quiz is finished
    if progress["current"] >= progress["total"]:
        # Finish session
        finish_result = await api_request("POST", f"/public/sessions/{session_id}/finish")
        
        if finish_result:
            feedback_text += f"\n\n🎉 Тест завершён!\n"
            feedback_text += f"Результат: {finish_result['correct_count']}/{finish_result['total_count']} ({finish_result['score_percent']}%)"
            
            await callback.message.edit_text(
                feedback_text,
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
        else:
            await callback.message.edit_text(TEXTS["finish_error"])
    else:
        # Continue to next question
        await callback.message.edit_text(
            feedback_text,
            reply_markup=get_continue_keyboard()
        )

@router.callback_query(F.data == "next_question")
async def next_question(callback: CallbackQuery, state: FSMContext):
    """Go to next question"""
    await callback.answer()
    
    data = await state.get_data()
    session_id = data.get("session_id")
    
    if not session_id:
        await callback.message.edit_text(TEXTS["session_error"])
        return
    
    await send_next_question(callback.message, session_id, state)

async def send_next_question(message: Message, session_id: str, state: FSMContext):
    """Send next question to user"""
    # Get next question
    question_data = await api_request("GET", f"/public/sessions/{session_id}/next")
    
    if not question_data:
        # No more questions, finish quiz
        finish_result = await api_request("POST", f"/public/sessions/{session_id}/finish")
        
        if finish_result:
            result_text = f"🎉 Тест завершён!\n"
            result_text += f"Результат: {finish_result['correct_count']}/{finish_result['total_count']} ({finish_result['score_percent']}%)"
            
            await message.edit_text(
                result_text,
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
        else:
            await message.edit_text(TEXTS["finish_error"])
        return
    
    # Format question with answer options
    question_text = f"❓ <b>{question_data['title']}</b>\n\n"
    question_text += f"{question_data['text']}\n\n"
    
    # Add answer options to the question text
    for i, option in enumerate(question_data['options']):
        question_text += f"<b>{chr(65 + i)}.</b> {option['text']}\n"
    
    question_text += f"\n📊 Вопрос {question_data['current']} из {question_data['total']}"
    
    # Create keyboard with answer options
    keyboard = get_quiz_keyboard(question_data['options'])
    
    await message.edit_text(question_text, reply_markup=keyboard)

@router.callback_query(F.data == "view_stats")
async def view_stats(callback: CallbackQuery):
    """View user statistics"""
    await callback.answer()
    
    user_stats = await api_request("GET", f"/public/users/{callback.from_user.id}/stats")
    
    if user_stats:
        stats_text = f"📊 <b>Ваша статистика</b>\n\n"
        stats_text += f"👤 {user_stats['full_name']}\n"
        stats_text += f"📅 Зарегистрирован: {user_stats['registered_at'][:10]}\n"
        stats_text += f"🎯 Попыток: {user_stats['attempts']}\n"
        
        if user_stats['attempts'] > 0:
            stats_text += f"📈 Последний результат: {user_stats['last_score_percent']}%\n"
            stats_text += f"🏆 Лучший результат: {user_stats['best_score_percent']}%"
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(TEXTS["stats_error"])

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main menu"""
    await callback.answer()
    await state.clear()
    
    user_stats = await api_request("GET", f"/public/users/{callback.from_user.id}/stats")
    
    if user_stats:
        await callback.message.edit_text(
            TEXTS["main_menu"].format(name=user_stats["full_name"]),
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Главное меню",
            reply_markup=get_main_menu_keyboard()
        )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command"""
    user_stats = await api_request("GET", f"/public/users/{message.from_user.id}/stats")
    
    if user_stats:
        stats_text = f"📊 <b>Ваша статистика</b>\n\n"
        stats_text += f"👤 {user_stats['full_name']}\n"
        stats_text += f"📅 Зарегистрирован: {user_stats['registered_at'][:10]}\n"
        stats_text += f"🎯 Попыток: {user_stats['attempts']}\n"
        
        if user_stats['attempts'] > 0:
            stats_text += f"📈 Последний результат: {user_stats['last_score_percent']}%\n"
            stats_text += f"🏆 Лучший результат: {user_stats['best_score_percent']}%"
        
        await message.answer(stats_text)
    else:
        await message.answer("❌ Не удалось получить статистику")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
🤖 <b>Справка по боту</b>

Этот бот предназначен для проверки знаний аккаунт-менеджеров.

<b>Команды:</b>
/start - Начать работу с ботом
/stats - Посмотреть свою статистику
/help - Показать эту справку

<b>Как пройти тест:</b>
1. Нажмите "🎯 Начать тест"
2. Отвечайте на вопросы, выбирая правильный вариант
3. После каждого ответа увидите объяснение
4. В конце получите результат

Удачи в тестировании! 🚀
    """
    await message.answer(help_text)

# Handle unknown messages
@router.message()
async def unknown_message(message: Message, state: FSMContext):
    """Handle unknown messages"""
    current_state = await state.get_state()
    
    if current_state == QuizStates.waiting_for_name:
        # In name input state, treat as name
        await process_name(message, state)
    else:
        # Unknown command
        await message.answer(
            "❓ Не понял команду. Используйте кнопки меню или команду /help для справки.",
            reply_markup=get_main_menu_keyboard()
        )
