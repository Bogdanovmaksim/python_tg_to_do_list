import sqlite3
import os
from datetime import date

class Database:

    def __init__(self, db_name='todo_bot.db'):
        """
        Инициализирует объект базы данных.

        :param db_name: Имя файла базы данных.
        :type db_name: str
        :example:
                db = Database('todo_bot.db')
                db = Database()
        """
        self.db_name = db_name
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """
        Проверяет существование файла базы данных и создает его при необходимости.

        :raises sqlite3.Error: Если не удается создать файл базы данных.
        :example:
        self._ensure_db_exists()

        """
        if not os.path.exists(self.db_name):
            conn = sqlite3.connect(self.db_name)
            conn.close()

    def _get_connection(self):
        """
        Создает и возвращает соединение с базой данных.

        :param user_id: ID пользователя Telegram (используется для логики изоляции).
        :type user_id: int
        :return: Соединение с SQLite базой данных.
        :rtype: sqlite3.Connection
        :raises sqlite3.Error: Если не удается установить соединение.
        :example:
            conn = self._get_connection(123456)
        """
        conn = sqlite3.connect(self.db_name)
        return conn

    def create_table(self, user_id):
        """
        Создает таблицу tasks если она не существует.

        :param user_id: ID пользователя Telegram (для совместимости с интерфейсом).
        :type user_id: int
        :raises sqlite3.Error: Если не удается создать таблицу.
        :example:
            db.create_table(123456)

        """

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
             CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_text TEXT NOT NULL,
                category TEXT,
                done INTEGER DEFAULT 0,
                deadline DATE
            )
        ''')
        conn.commit()
        conn.close()

    def add_task(self ,user_id, task_text, category=None, deadline=None):
        """
        Добавляет новую задачу для указанного пользователя.

        :param user_id: ID пользователя Telegram.
        :type user_id: int
        :param task_text: Текст задачи.
        :type task_text: str
        :type: category: str
        :type: deadline: datetime
        :return: None
        :raises sqlite3.Error: Если не удается добавить задачу.
        :example:
            db.add_task(123456, "Купить молоко")

        """

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
                    INSERT INTO tasks (user_id, task_text, category, deadline)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, task_text, category, deadline))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id

    def get_tasks(self, user_id):
        """
        Получает все задачи для указанного пользователя.

        :param user_id: ID пользователя Telegram.
        :type user_id: int
        :return: Список задач пользователя.
        :rtype: list of tuples
        :raises sqlite3.Error: Если не удается получить задачи.
        :example:
            tasks = db.get_tasks(123456)

        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
                    SELECT id, user_id, task_text, category, done, deadline
                    FROM tasks WHERE user_id = ? ORDER BY id
                ''', (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    def mark_done(self, user_id, task_id):
        """
        Отмечает задачу как выполненную.

        :param user_id: ID пользователя Telegram.
        :type user_id: int
        :param task_id: ID задачи для отметки.
        :type task_id: int
        :return: True если задача была обновлена, False если задача не найдена.
        :rtype: bool
        :raises sqlite3.Error: Если не удается обновить задачу.
        :example:
            result = db.mark_done(123456, 1)  # True - задача найдена и обновлена
            result = db.mark_done(123456, 999)  # False - задача не найдена
        """

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?', (task_id, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def delete_task(self, user_id, task_id):
        """
        Удаляет задачу пользователя.

        :param user_id: ID пользователя Telegram.
        :type user_id: int
        :param task_id: ID задачи для удаления.
        :type task_id: int
        :return: True если задача была удалена, False если задача не найдена.
        :rtype: bool
        :raises sqlite3.Error: Если не удается удалить задачу.
        :example:
            result = db.delete_task(123456, 1)
            result = db.delete_task(123456, 999)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def search_tasks(self, user_id, keyword):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, user_id, task_text, category, done, deadline
            FROM tasks WHERE user_id = ? AND task_text LIKE ?
        ''', (user_id, f'%{keyword}%'))
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def clear_all_tasks(self, user_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE user_id = ?', (user_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted_count



