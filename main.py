import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import keyboard

from database import Database
from datetime import datetime, timedelta
from scheduler import ReminderScheduler

logging.basicConfig(level=logging.INFO)

TOKEN = '8257429587:AAH1HhfxGuig5rm0rWnuSXTKO60PqCAOvow'
bot = Bot(token = TOKEN)
dp = Dispatcher()

db = Database()

scheduler = ReminderScheduler(bot, db)

def parse_add_command(text):
    parts = text.split()
    if len(parts) < 2:
        return None, None, None
    task_text = []
    category = None
    deadline = None
    i = 1
    while i < len(parts):
        if parts[i].lower() == 'category' and i + 1 < len(parts):
            category = parts[i + 1]
            i += 2
        elif parts[i].lower() == 'deadline' and i + 1 < len(parts):
            try:
                deadline = datetime.strptime(parts[i + 1], '%Y-%m-%d').date()
                i += 2
            except ValueError:
                return None, None, None  # Неверный формат даты
        else:
            task_text.append(parts[i])
            i += 1
    if not task_text:
        return None, None, None
    return ' '.join(task_text), category, deadline



@dp.message(Command('start'))
async def cmd_start(message:Message):
    user_id = message.from_user.id
    await message.reply(
        "Привет! Это твой to-do бот. Используй команды:\n"
        "/add текст задачи - добавить задачу\n"
        "/list - показать все задачи\n"
        "/done id - отметить задачу выполненной\n"
        "/delete id - удалить задачу\n"
        "ID задач можно увидеть в списке."
    )
    db.create_table(user_id)

@dp.message(Command('add'))
async def cmd_add(message:Message):
    user_id = message.from_user.id
    command_text = message.text.replace('/add ', '').strip()
    task_text, category, deadline = parse_add_command(command_text)
    if not task_text:
        await message.reply('Ошибка: укажи текст задачи после /add, например: /add Купить молоко category Работа deadline 2025-12-01')
        return
    try:
        task_id = db.add_task(user_id, task_text, category, deadline)
        response = f'Задача добавлена: {task_id}'
        if category:
            response += f' (Категория: {category})'
        if deadline:
            response += f'Дедлайн: {deadline}'

            reminder_time = datetime.combine(deadline, datetime.min.time()) - timedelta(days=1)
            if reminder_time > datetime.now():
                scheduler.add_reminder(user_id, task_id, task_text, reminder_time)
        await message.reply(response)
    except Exception as e:
        logging.error(f'Ошбика при добавлении: {e}')
        await message.reply('Произошла ошибка. Попробуй позже.')



@dp.message(Command('list'))
async def cmd_list(message:Message):
    user_id = message.from_user.id
    try:
        tasks = db.get_tasks(user_id)
        if not tasks:
            await message.reply("У тебя нет задач.")
            return
        response = "Твои задачи:\n"
        keyboard = []
        for task in tasks:
            status = "✅ Выполнена" if task[4] else "❌ Не выполнена"
            cat = f" | Кат: {task[3]}" if task[3] else ""
            dl = f" | Дедлайн: {task[5]}" if task[5] else ""
            response += f"ID: {task[0]} | {task[2]}{cat}{dl} | {status}\n"
            if not task[4]:  # Только для невыполненных
                keyboard.append([InlineKeyboardButton(text=f"✅ Выполнить {task[0]}", callback_data=f"done_{task[0]}")])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await message.reply(response, reply_markup=markup)
    except Exception as e:
        logging.error(f"Ошибка при списке: {e}")
        await message.reply("Произошла ошибка. Попробуй позже.")

@dp.callback_query(lambda c: c.data.startswith('done_'))
async def process_done_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split('_')[1])
    try:
        if db.mark_done(user_id, task_id):
            await callback_query.message.edit_text("Задача отмечена как выполненная!")
            await callback_query.answer("Готово!")
        else:
            await callback_query.answer("Задача не найдена.")
    except Exception as e:
        logging.error(f"Ошибка при отметке: {e}")
        await callback_query.answer("Ошибка.")


'''Надо бы добавить обработчик команды /search '''


'''Добавь команду /export'''


@dp.message(Command('done'))
async def cmd_done(message: Message):
    user_id = message.from_user.id
    try:
        task_id = int(message.text.replace('/done', '').strip())
        if db.mark_done(user_id, task_id):
            await message.reply(f"Задача {task_id} отмечена как выполненная!")
        else:
            await message.reply(f"Задача {task_id} не найдена или уже выполнена.")
    except ValueError:
        await message.reply("Ошибка: укажи ID задачи числом, например: /done 1")
    except Exception as e:
        logging.error(f"Ошибка при отметке задачи: {e}")
        await message.reply("Произошла ошибка. Попробуй позже.")

@dp.message(Command('delete'))
async def cmd_delete(message: Message):
    user_id = message.from_user.id
    try:
        task_id = int(message.text.replace('/delete', '').strip())
        if db.delete_task(user_id, task_id):
            await message.reply(f"Задача {task_id} удалена!")
        else:
            await message.reply(f"Задача {task_id} не найдена.")
    except ValueError:
        await message.reply("Ошибка: укажи ID задачи числом, например: /delete 1")
    except Exception as e:
        logging.error(f"Ошибка при удалении задачи: {e}")
        await message.reply("Произошла ошибка. Попробуй позже.")

@dp.message()
async def unknown_command(message:Message):
    await message.reply('Неизвестная команда. Используй /start для справки.')

async def main():
    await scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())





