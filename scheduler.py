from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from aiogram import Bot
from database import Database


class ReminderScheduler:
    '''
    Класс для управления напоминаниями о задачах.

    Использует APScheduler для отправки уведомлений пользователям
    о приближающихся дедлайнах задач.
    '''
    def __init__(self, bot: Bot, db: Database):
        '''
        Инициализирует планировщик напоминаний.

        :param bot: объект бота для отправки сообщений
        :type bot: aiogram.Bot
        :param db: объект базы данных для работы с задачами
        :type db: Database
        '''
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        '''
        Запускает планировщик напоминаний.

        Должен быть вызван один раз при старте бота.

        :returns: none
        '''
        self.scheduler.start()

    def add_reminder(self, user_id, task_id, task_text, reminder_time: datetime):
        '''
    Добавляет напоминание о задаче в планировщик.

    :param user_id: ID пользователя в Telegram
    :type user_id: int
    :param task_id: ID задачи в базе данных
    :type task_id: int
    :param task_text: текст задачи для напоминания
    :type task_text: str
    :param reminder_time: время отправки напоминания
    :type reminder_time: datetime.datetime
    :returns: none
        '''
        self.scheduler.add_job(
            self._send_reminder,
            trigger=DateTrigger(run_date=reminder_time),
            args=[user_id, task_id, task_text],
            id = f'reminder_{user_id}_{task_id}'

        )

    async def _send_reminder(self, user_id, task_id, task_text):
        '''
        Отправляет напоминание пользователю.

        Внутренний метод, вызывается планировщиком автоматически.

        :param user_id: ID пользователя в Telegram
        :type user_id: int
        :param task_id: ID задачи в базе данных
        :type task_id: int
        :param task_text: текст задачи для напоминания
        :type task_text: str
        :returns: none
        :raises Exception: при ошибках отправки сообщения
        '''
        try:
            await self.bot.send_message(
                user_id,
                f"Напоминание: Задача '{task_text}' (ID: {task_id}) приближается к дедлайну! Завтра последний день."
            )
        except Exception as e:
            print(f'Ошибка отправки напоминания: {e}')

