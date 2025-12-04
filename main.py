import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import keyboard
from database import Database
from datetime import datetime, timedelta
from scheduler import ReminderScheduler
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("TOKEN не найден в .env")
bot = Bot(token=TOKEN)
dp = Dispatcher()

db = Database()

scheduler = ReminderScheduler(bot, db)


class AddTaskStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_category = State()
    waiting_for_deadline = State()


def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_start'), ]
    ])


def get_choice_keyboard(yes_text, no_text, yes_callback, no_callback):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=yes_text, callback_data=yes_callback)],
        [InlineKeyboardButton(text=no_text, callback_data=no_callback)]
    ])


@dp.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    '''

    Обработчик команды start Приветсвует пользователя и показывает списко доступных команд

    :param message:
    :type message: aiogram.types.Message

    '''
    await state.clear()  # Очищаем состояние
    user_id = message.from_user.id
    keyboard = [
        [InlineKeyboardButton(text="📝 Добавить задачу", callback_data="add")],
        [InlineKeyboardButton(text="📋 Список задач", callback_data="list")],
        [InlineKeyboardButton(text="🔍 Поиск задач", callback_data="search")],
        [InlineKeyboardButton(text="📤 Экспорт списка", callback_data="export")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.reply(
        "Привет! Это последняя версия to-do-list бота. Выбери действие или используй команды:\n"
        "/add - добавить задачу (пошагово)\n"
        "/list - список\n"
        "/search <слово> - поиск\n"
        "/export - экспорт\n"
        "/clear - очистить все задачи\n"
        "/done <id> - выполнить\n"
        "/delete <id> - удалить",
        reply_markup=markup
    )
    db.create_table(user_id)


@dp.callback_query(lambda c: c.data in ["add", "list", "search", "export"])
async def process_menu_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback_query.from_user.id
    action = callback_query.data
    if action == "add":
        await callback_query.message.edit_text("Введи текст задачи:", reply_markup=get_back_keyboard())
        await state.set_state(AddTaskStates.waiting_for_text)
    elif action == "list":
        await cmd_list_callback(callback_query)
    elif action == "search":
        await callback_query.message.edit_text(
            "Введи: /search <ключевое слово>\nПример: /search молоко",
            reply_markup=get_back_keyboard()
        )
    elif action == "export":
        await cmd_export_callback(callback_query)
    await callback_query.answer()


@dp.message(StateFilter(AddTaskStates.waiting_for_text))
async def process_task_text(message: Message, state: FSMContext):
    task_text = message.text.strip()
    if not task_text:
        await message.reply("Текст не может быть пустым. Введи текст задачи:", reply_markup=get_back_keyboard())
        return
    await state.update_data(task_text=task_text)
    markup = get_choice_keyboard("Добавить категорию", "Пропустить", "add_category", "skip_category")
    await message.reply("Хочешь добавить категорию?", reply_markup=markup)


@dp.callback_query(lambda c: c.data in ['add_category', 'skip_category'])
async def process_category_choice(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "add_category":
        await callback_query.message.edit_text("Введи название категории:", reply_markup=get_back_keyboard())
        await state.set_state(AddTaskStates.waiting_for_category)
    else:
        await state.update_data(category=None)
        # ОШИБКА БЫЛА ЗДЕСЬ: не было обработчика для кнопок add_deadline/skip_deadline
        markup = get_choice_keyboard("Добавить дедлайн", "Пропустить", "add_deadline", "skip_deadline")
        await callback_query.message.edit_text("Хочешь добавить дедлайн (YYYY-MM-DD)?", reply_markup=markup)
    await callback_query.answer()


# ДОБАВЛЕНО: обработчик выбора дедлайна
@dp.callback_query(lambda c: c.data in ['add_deadline', 'skip_deadline'])
async def process_deadline_choice(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "add_deadline":
        await callback_query.message.edit_text("Введи дедлайн в формате YYYY-MM-DD:", reply_markup=get_back_keyboard())
        await state.set_state(AddTaskStates.waiting_for_deadline)
    else:
        await state.update_data(deadline=None)
        await finalize_add_task(callback_query, state)
    await callback_query.answer()


@dp.message(StateFilter(AddTaskStates.waiting_for_category))
async def process_category_text(message: Message, state: FSMContext):
    category = message.text.strip()
    if not category:
        await message.reply("Категория не может быть пустой. Введи название категории:",
                            reply_markup=get_back_keyboard())
        return
    await state.update_data(category=category)
    markup = get_choice_keyboard("Добавить дедлайн", "Пропустить", "add_deadline", "skip_deadline")
    await message.reply("Хочешь добавить дедлайн (YYYY-MM-DD)?", reply_markup=markup)


@dp.message(StateFilter(AddTaskStates.waiting_for_deadline))
async def process_deadline_text(message: Message, state: FSMContext):
    deadline_str = message.text.strip()
    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        if deadline < today:
            await message.reply("Дедлайн не может быть в прошлом. Введи будущую дату (YYYY-MM-DD):",
                                reply_markup=get_back_keyboard())
            return
        if deadline > today.replace(year=today.year + 10):  # Не дальше 10 лет
            await message.reply("Дедлайн слишком далек. Введи дату в пределах 10 лет (YYYY-MM-DD):",
                                reply_markup=get_back_keyboard())
            return
        await state.update_data(deadline=deadline)
        await finalize_add_task(message, state)
    except ValueError:
        await message.reply("Неверный формат даты. Введи в формате YYYY-MM-DD (например, 2025-12-01):",
                            reply_markup=get_back_keyboard())


async def finalize_add_task(source, state: FSMContext):
    data = await state.get_data()
    user_id = source.from_user.id if isinstance(source, types.Message) else source.message.from_user.id
    task_text = data['task_text']
    category = data.get('category')
    deadline = data.get('deadline')
    try:
        task_id = db.add_task(user_id, task_text, category, deadline)
        if task_id is None or task_id == 0:
            raise ValueError("Не удалось добавить задачу в БД")
        response = f"Задача добавлена: {task_text}"
        if category:
            response += f" (Категория: {category})"
        if deadline:
            response += f" (Дедлайн: {deadline})"
            # Запланировать напоминание
            reminder_time = datetime.combine(deadline, datetime.min.time()) - timedelta(days=1)
            if reminder_time > datetime.now():
                scheduler.add_reminder(user_id, task_id, task_text, reminder_time)
        await state.clear()
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть список", callback_data="list")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="back_to_start")]
        ])
        if isinstance(source, types.CallbackQuery):
            await source.message.edit_text(response, reply_markup=markup)
        else:
            await source.reply(response, reply_markup=markup)
    except Exception as e:
        logging.error(f"Ошибка при добавлении: {e}")
        await state.clear()
        error_msg = f"Произошла ошибка при добавлении: {str(e)}. Попробуй позже."
        if isinstance(source, types.CallbackQuery):
            await source.message.edit_text(error_msg, reply_markup=get_back_keyboard())
        else:
            await source.reply(error_msg, reply_markup=get_back_keyboard())


async def cmd_list_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        tasks = db.get_tasks(user_id)
        if not tasks:
            await callback_query.message.edit_text("У тебя нет задач.", reply_markup=get_back_keyboard())
            return
        response = "Твои задачи:\n"
        keyboard = []
        for task in tasks:
            status = "✅ Выполнена" if task[4] else "❌ Не выполнена"
            cat = f" | Кат: {task[3]}" if task[3] else ""
            dl = f" | Дедлайн: {task[5]}" if task[5] else ""
            response += f"ID: {task[0]} | {task[2]}{cat}{dl} | {status}\n"
            if not task[4]:
                keyboard.append([
                    InlineKeyboardButton(text=f"✅ Выполнить {task[0]}", callback_data=f"done_{task[0]}"),
                    InlineKeyboardButton(text=f"🗑️ Удалить {task[0]}", callback_data=f"delete_{task[0]}")
                ])
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await callback_query.message.edit_text(response, reply_markup=markup)
    except Exception as e:
        logging.error(f"Ошибка при списке: {e}")
        await callback_query.message.edit_text("Произошла ошибка. Попробуй позже.", reply_markup=get_back_keyboard())


async def cmd_export_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        tasks = db.get_tasks(user_id)
        if not tasks:
            await callback_query.message.edit_text("Нет задач для экспорта.", reply_markup=get_back_keyboard())
            return
        content = "ID | Задача | Категория | Дедлайн | Статус\n"
        for task in tasks:
            status = "Выполнена" if task[4] else "Не выполнена"
            cat = task[3] or "Нет"
            dl = task[5] or "Нет"
            content += f"{task[0]} | {task[2]} | {cat} | {dl} | {status}\n"
        with open(f'tasks_{user_id}.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        await callback_query.message.edit_text("Экспорт готов! Скачай файл ниже.", reply_markup=get_back_keyboard())
        await callback_query.message.reply_document(types.FSInputFile(f'tasks_{user_id}.txt'),
                                                    caption="Твой список задач")
    except Exception as e:
        logging.error(f"Ошибка при экспорте: {e}")
        await callback_query.message.edit_text("Произошла ошибка. Попробуй позже.", reply_markup=get_back_keyboard())


@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_start(callback_query.message, state)
    await callback_query.answer()

@dp.message(Command('clear'))
async def cmd_clear(message: Message):
    user_id = message.from_user.id
    try:
        deleted_count = db.clear_all_tasks(user_id)
        await message.reply(f"Удалено {deleted_count} задач. Теперь список пуст.", reply_markup=get_back_keyboard())
    except Exception as e:
        logging.error(f"Ошибка при очистке: {e}")

@dp.message(Command('add'))
async def cmd_add(message: Message, state: FSMContext):
    await state.clear()
    await message.reply("Введи текст задачи:", reply_markup=get_back_keyboard())
    await state.set_state(AddTaskStates.waiting_for_text)


@dp.message(Command('list'))
async def cmd_list(message: Message):
    '''

    Обработчик команды list. Используется для выведения всех задач пользователя

    :param message: команда list
    :type message: aiogram.types.Message
    :return: Отправляет список задач пользователю
    :rtype: aiogram.types.Message

    '''
    user_id = message.from_user.id
    try:
        tasks = db.get_tasks(user_id)
        if not tasks:
            await message.reply("У тебя нет задач.", reply_markup=get_back_keyboard())
            return
        response = "Твои задачи:\n"
        keyboard = []
        for task in tasks:
            status = "✅ Выполнена" if task[4] else "❌ Не выполнена"
            cat = f" | Кат: {task[3]}" if task[3] else ""
            dl = f" | Дедлайн: {task[5]}" if task[5] else ""
            response += f"ID: {task[0]} | {task[2]}{cat}{dl} | {status}\n"
            if not task[4]:
                keyboard.append([
                    InlineKeyboardButton(text=f"✅ Выполнить {task[0]}", callback_data=f"done_{task[0]}"),
                    InlineKeyboardButton(text=f"🗑️ Удалить {task[0]}", callback_data=f"delete_{task[0]}")
                ])
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await message.reply(response, reply_markup=markup)
    except Exception as e:
        logging.error(f"Ошибка при списке: {e}")
        await message.reply("Произошла ошибка. Попробуй позже.", reply_markup=get_back_keyboard())

@dp.callback_query(lambda c: c.data.startswith('done_'))
async def process_done_callback(callback_query: types.CallbackQuery):
    '''

    Обработчик инлайн-кнопок для отметки выполненых задач

    :param callback_query: объект callback запроса от инлайн-кнопки
    :type callback_query: aiogram.types.CallbackQuery
    :return: Отмечает задачу выполненной
    :rtype: aiogram.types.CallbackQuery
    '''
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split('_')[1])
    try:
        if db.mark_done(user_id, task_id):
            await callback_query.message.edit_text("Задача отмечена как выполненная! Используй /list для обновления.",
                                                   reply_markup=get_back_keyboard())
            await callback_query.answer("Готово!")
        else:
            await callback_query.answer("Задача не найдена.")
    except Exception as e:
        logging.error(f"Ошибка при отметке: {e}")
        await callback_query.answer("Ошибка.")


@dp.callback_query(lambda c: c.data.startswith('delete_'))
async def process_delete_callback(callback_query: types.CallbackQuery):
    '''

    Обработчик инлайн-кнопок для удаления выполненых задач

    :param callback_query: объект callback запроса от инлайн-кнопки
    :type callback_query: aiogram.types.CallbackQuery
    :return: Отмечает задачу удаленной
    :rtype: aiogram.types.CallbackQuery
    '''
    user_id = callback_query.from_user.id
    task_id = int(callback_query.data.split('_')[1])
    try:
        if db.delete_task(user_id, task_id):
            await callback_query.message.edit_text("Задача удалена! Используй /list для обновления.",
                                                   reply_markup=get_back_keyboard())
            await callback_query.answer("Удалено!")
        else:
            await callback_query.answer("Задача не найдена.")
    except Exception as e:
        logging.error(f"Ошибка при удалении: {e}")
        await callback_query.answer("Ошибка.")

@dp.message(Command('search'))
async def cmd_search(message: Message):
    '''

    Обработчик команды search. Используется для поиска задач пользователя

    :param message: команда search и ее ID
    :type message: aiogram.types.Message
    :return: Сообщает статус задачи если такая найдена
    :rtype: aiogram.types.Message
    :raises Exception: при ошибках работы с базой данных во время поиска
     '''
    user_id = message.from_user.id
    keyword = message.text.replace('/search', '').strip()
    if not keyword:
        await message.reply("Укажи ключевое слово, например: /search молоко", reply_markup=get_back_keyboard())
        return
    try:
        tasks = db.search_tasks(user_id, keyword)
        if not tasks:
            await message.reply("Ничего не найдено.", reply_markup=get_back_keyboard())
            return
        response = f"Результаты поиска по '{keyword}':\n"
        for task in tasks:
            status = "✅ Выполнена" if task[4] else "❌ Не выполнена"
            response += f"ID: {task[0]} | {task[2]} | {status}\n"
        await message.reply(response, reply_markup=get_back_keyboard())
    except Exception as e:
        logging.error(f"Ошибка при поиске: {e}")
        await message.reply("Произошла ошибка. Попробуй позже.", reply_markup=get_back_keyboard())

@dp.message(Command('export'))
async def cmd_export(message: Message):
    '''

    Обработчик команды /export. Экспортирует все задачи пользователя в текстовый файл

    :param message: команда export
    :type message: aiogram.types.Message
    :return: Отправляет пользователю текстовый файл с задачами
    :rtype: aiogram.types.Message
    :raises Exception: при ошибках работы с базой данных или файловой системой
    '''
    user_id = message.from_user.id
    try:
        tasks = db.get_tasks(user_id)
        if not tasks:
            await message.reply("Нет задач для экспорта.", reply_markup=get_back_keyboard())
            return
        content = "ID | Задача | Категория | Дедлайн | Статус\n"
        for task in tasks:
            status = "Выполнена" if task[4] else "Не выполнена"
            cat = task[3] or "Нет"
            dl = task[5] or "Нет"
            content += f"{task[0]} | {task[2]} | {cat} | {dl} | {status}\n"
        with open(f'tasks_{user_id}.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        await message.reply_document(types.FSInputFile(f'tasks_{user_id}.txt'), caption="Твой список задач",
                                     reply_markup=get_back_keyboard())
    except Exception as e:
        logging.error(f"Ошибка при экспорте: {e}")
        await message.reply("Произошла ошибка. Попробуй позже.")

@dp.message(Command('done'))
async def cmd_done(message: Message):
    '''

    Обработчик команды /done. По ID задачи отмечает ее выполненой

    :param message: команда /done и ID задачи
    :type message: aiogram.types.Message
    :return: Отправляет результат отметки задачи
    :rtype: aiogram.types.Message
    '''
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
    '''

    Обработчик команды /delete. Служит для удаления задачи по ее ID

    :param message: Команда done и ID задачи
    :type message: aiogram.types.Message
    :return: Сообщает пользователю результат удаления задачи
    :rtype: aiogram.types.Message

    '''
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
async def unknown_command(message: Message):
    '''

    Обработчик любых команд неизвестных боту

    :param message: Любая команда, не заданная боту
    :type message: aiogram.types.Message
    :return: Отправляет пользователю сообщение с подсказкой ввести команду /start
    :rtype: aiogram.types.Message
    '''
    await message.reply('Неизвестная команда. Используй /start для справки.', reply_markup=get_back_keyboard())

async def main():
    '''

    Основная асинхронная функция для запуска бота.

    :return: запускает поллинг бота и планировщик напоминаний
    :rtype: None
    '''
    await scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())