from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from aiogram import Bot
from database import Database


class ReminderScheduler:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        self.scheduler.start()

    def add_reminder(self, user_id, task_id, task_text, reminder_time: datetime):
        self.scheduler.add_job(
            self._send_reminder,
            trigger=DateTrigger(run_date=reminder_time),
            args=[user_id, task_id, task_text],
            id = f'reminder_{user_id}_{task_id}'

        )

    async def _send_reminder(self, user_id, task_id, task_text):
        try:
            await self.bot.send_message(
                user_id,
                f"Напоминание: Задача '{task_text}' (ID: {task_id}) приближается к дедлайну! Завтра последний день."
            )
        except Exception as e:
            print(f'Ошибка отправки напоминания: {e}')

