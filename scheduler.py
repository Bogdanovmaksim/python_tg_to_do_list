import sqlite3
import os
from datetime import date

class Database:

    def __init__(self, db_name='todo_bot.db'):
        self.db_name = db_name
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        if not os.path.exists(self.db_name):
            conn = sqlite3.connect(self.db_name)
            conn.close()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        return conn

    def create_table(self, user_id):
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

    def add_task(self, user_id, task_text, category=None, deadline=None):
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?', (task_id, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def delete_task(self, user_id, task_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def clear_all_tasks(self, user_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE user_id = ?', (user_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted_count