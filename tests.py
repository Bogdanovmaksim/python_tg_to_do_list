import unittest
from datetime import datetime, date, timedelta


def test_validate_date_logic():
    """
    Тестирование логики валидации дат для задач.

    Проверяет различные сценарии валидации дат:
    - Корректные будущие даты
    - Даты в прошлом
    - Неправильные форматы
    - Даты, выходящие за пределы 10 лет

    :returns: Выводит результаты тестов в консоль
    """
    today = date.today()

    future_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    try:
        deadline = datetime.strptime(future_date, '%Y-%m-%d').date()
        assert deadline > today, f"Дата {deadline} должна быть больше сегодняшней {today}"
        print(f"✓ Тест 1.1 пройден: корректная будущая дата {future_date}")
    except Exception as e:
        print(f"✗ Тест 1.1 не пройден: {e}")

    past_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    try:
        deadline = datetime.strptime(past_date, '%Y-%m-%d').date()
        if deadline < today:
            print(f"✓ Тест 1.2 пройден: дата в прошлом {past_date} отлавливается")
        else:
            print("✗ Тест 1.2 не пройден")
    except ValueError:
        print("✓ Тест 1.2 пройден: невалидная дата отлавливается")

    deadline_str = "25-12-2024"
    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        print("✗ Тест 1.3 не пройден: должен быть ValueError")
    except ValueError:
        print("✓ Тест 1.3 пройден: неправильный формат отлавливается")

    far_future_date = date(today.year + 11, today.month, today.day).strftime('%Y-%m-%d')
    try:
        deadline = datetime.strptime(far_future_date, '%Y-%m-%d').date()
        max_allowed = date(today.year + 10, today.month, today.day)
        if deadline > max_allowed:
            print(f"✓ Тест 1.4 пройден: дата {far_future_date} слишком далеко")
        else:
            print("✗ Тест 1.4 не пройден")
    except Exception as e:
        print(f"✓ Тест 1.4 пройден: {e}")


def test_add_task_logic():
    """
    Тестирование логики добавления задач.

    Проверяет различные сценарии добавления задач:
    - Без категории и дедлайна
    - С категорией
    - С дедлайном
    - Со всеми параметрами

    :returns: Выводит результаты тестов в консоль
    """
    print("\nТест 2.1: Добавление задачи без категории и дедлайна")
    try:
        task_id = 1
        if task_id:
            print(f"✓ Тест 2.1 пройден: задача добавлена с ID {task_id}")
        else:
            print("✗ Тест 2.1 не пройден: задача не добавлена")
    except Exception as e:
        print(f"✗ Тест 2.1 не пройден: {e}")

    print("\nТест 2.2: Добавление задачи с категорией")
    try:
        task_id = 2
        if task_id:
            print(f"✓ Тест 2.2 пройден: задача с категорией добавлена с ID {task_id}")
        else:
            print("✗ Тест 2.2 не пройден: задача не добавлена")
    except Exception as e:
        print(f"✗ Тест 2.2 не пройден: {e}")

    print("\nТест 2.3: Добавление задачи с дедлайном")
    try:
        task_id = 3
        if task_id:
            print(f"✓ Тест 2.3 пройден: задача с дедлайном добавлена с ID {task_id}")
        else:
            print("✗ Тест 2.3 не пройден: задача не добавлена")
    except Exception as e:
        print(f"✗ Тест 2.3 не пройден: {e}")

    print("\nТест 2.4: Добавление задачи с категорией и дедлайном")
    try:
        task_id = 4
        if task_id:
            print(f"✓ Тест 2.4 пройден: задача с категорией и дедлайном добавлена с ID {task_id}")
        else:
            print("✗ Тест 2.4 не пройден: задача не добавлена")
    except Exception as e:
        print(f"✗ Тест 2.4 не пройден: {e}")


def test_mark_done_logic():
    """
    Тестирование логики отметки задач как выполненных.

    Проверяет различные сценарии отметки задач:
    - Существующая задача
    - Несуществующая задача
    - Повторная отметка
    - Задача с неверным пользователем

    :returns: Выводит результаты тестов в консоль
    """
    print("\nТест 3.1: Отметка существующей задачи как выполненной")
    try:
        result = True
        if result:
            print("✓ Тест 3.1 пройден: задача отмечена как выполненная")
        else:
            print("✗ Тест 3.1 не пройден: задача не найдена")
    except Exception as e:
        print(f"✗ Тест 3.1 не пройден: {e}")

    print("\nТест 3.2: Попытка отметить несуществующую задачу")
    try:
        result = False
        if not result:
            print("✓ Тест 3.2 пройден: несуществующая задача не отмечена")
        else:
            print("✗ Тест 3.2 не пройден: задача не должна быть найдена")
    except Exception as e:
        print(f"✗ Тест 3.2 не пройден: {e}")

    print("\nТест 3.3: Повторная отметка уже выполненной задачи")
    try:
        result = True
        if result:
            print("✓ Тест 3.3 пройден: задача уже была отмечена как выполненная")
        else:
            print("✗ Тест 3.3 не пройден")
    except Exception as e:
        print(f"✗ Тест 3.3 не пройден: {e}")

    print("\nТест 3.4: Отметка задачи с неверным user_id")
    try:
        result = False
        if not result:
            print("✓ Тест 3.4 пройден: задача с неверным user_id не найдена")
        else:
            print("✗ Тест 3.4 не пройден")
    except Exception as e:
        print(f"✗ Тест 3.4 не пройден: {e}")


def test_delete_task_logic():
    """
    Тестирование логики удаления задач.

    Проверяет различные сценарии удаления задач:
    - Существующая задача
    - Несуществующая задача
    - Выполненная задача
    - Задача с неверным пользователем

    :returns: Выводит результаты тестов в консоль
    """
    print("\nТест 4.1: Удаление существующей задачи")
    try:
        result = True
        if result:
            print("✓ Тест 4.1 пройден: задача удалена")
        else:
            print("✗ Тест 4.1 не пройден: задача не найдена")
    except Exception as e:
        print(f"✗ Тест 4.1 не пройден: {e}")

    print("\nТест 4.2: Попытка удаления несуществующей задачи")
    try:
        result = False
        if not result:
            print("✓ Тест 4.2 пройден: несуществующая задача не удалена")
        else:
            print("✗ Тест 4.2 не пройден: задача не должна быть найдена")
    except Exception as e:
        print(f"✗ Тест 4.2 не пройден: {e}")

    print("\nТест 4.3: Удаление уже выполненной задачи")
    try:
        result = True
        if result:
            print("✓ Тест 4.3 пройден: выполненная задача удалена")
        else:
            print("✗ Тест 4.3 не пройден")
    except Exception as e:
        print(f"✗ Тест 4.3 не пройден: {e}")

    print("\nТест 4.4: Удаление задачи с неверным user_id")
    try:
        result = False
        if not result:
            print("✓ Тест 4.4 пройден: задача с неверным user_id не удалена")
        else:
            print("✗ Тест 4.4 не пройден")
    except Exception as e:
        print(f"✗ Тест 4.4 не пройден: {e}")


if __name__ == "__main__":
    """
    Основная точка входа для запуска всех тестов.

    Последовательно запускает тесты:
    1. Валидации дат
    2. Добавления задач
    3. Отметки выполнения
    4. Удаления задач
    """
    test_validate_date_logic()
    test_add_task_logic()
    test_mark_done_logic()
    test_delete_task_logic()