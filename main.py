import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from database import Database

logging.basicConfig(level=logging.INFO)

TOKEN = 'TOKEN'
bot = Bot(token = TOKEN)
dp = Dispatcher()

db = Database()

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
    text = message.text.replace('/add ', '').strip()
    if not text:
        await message.reply('Ошибка: укажи текст задачи после /add, например: /add Купить молоко')
    try:
        db.add_task(user_id, text)
        await message.reply(f'Задача добавлена: {text}')
    except Exception as e:
        logging.error(f'Ошибка при добавлении задачи: {e}')
        await message.reply('Произошла ошибка при добавлении задачи. Попробуйте позже.')

@dp.message(Command('list'))
async def cmd_list(message:Message):
    user_id = message.from_user.id
    try:
        tasks = db.get_tasks(user_id)
        if not tasks:
            await message.reply('У тебя нет задач.')
            return
        response = 'Твои задачи\n'
        for task in tasks:
            status = "✅ Выполнена" if task[3] else "❌ Не выполнена"
            response += f"ID: {task[0]} | {task[2]} | {status}\n"
        await message.reply(response)
    except Exception as e:
        logging.error(f'Ошибка при получении списка задач: {e}')
        await message.reply('Произошла ошибка при получениия списка. Попробуйте позже.')

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
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())





