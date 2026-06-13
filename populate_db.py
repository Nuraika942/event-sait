"""
Скрипт для добавления демо-пользователей и мероприятий в существующую базу данных.
Запускать только один раз или когда нужно обновить данные.
Для запуска: python populate_db.py
"""

from app import app, db
from models import User, Event
from werkzeug.security import generate_password_hash
from datetime import datetime, date, time, timedelta
import random

def populate():
    with app.app_context():
        # Проверяем, есть ли уже пользователь nurs
        if User.query.filter_by(username='nurs').first():
            print("Пользователь nurs уже существует, пропускаем создание.")
        else:
            # Добавляем нужных пользователей
            users_data = [
                ('alex', 'alex@example.com', 'pass123'),
                ('maria', 'maria@example.com', 'pass123'),
                ('ivan', 'ivan@example.com', 'pass123'),
                ('nurs', 'nurs@example.com', '1234qwe'),
            ]
            created = []
            for username, email, pwd in users_data:
                if not User.query.filter_by(username=username).first():
                    u = User(
                        username=username,
                        email=email,
                        password_hash=generate_password_hash(pwd),
                        role='user'
                    )
                    db.session.add(u)
                    created.append(username)
            db.session.commit()
            print(f"✅ Добавлены пользователи: {', '.join(created)}")

        # Проверяем, есть ли уже мероприятия
        if Event.query.count() >= 5:
            print(f"Уже есть {Event.query.count()} мероприятий, демо-события не добавляем.")
            return

        # Генерируем 20 случайных событий
        all_users = User.query.all()
        if not all_users:
            print("Нет пользователей, сначала добавьте пользователей.")
            return

        titles = [
            "Еженедельное собрание команды", "Презентация проекта", "День рождения коллеги",
            "Воркшоп по Python", "Конференция Digital", "Спортивный турнир", "Обед с партнёрами",
            "Технический аудит", "Тимбилдинг", "Вебинар по продажам"
        ]
        categories = ["Работа", "Личное", "Обучение", "Развлечения", "Спорт"]
        locations = ["Офис", "Зум", "Конференц-зал", "Парк", "Кафе", "Спортзал"]

        start_date = date.today()
        events_added = 0
        for i in range(20):
            rand_days = random.randint(0, 30)
            event_date = start_date + timedelta(days=rand_days)
            hour_start = random.randint(9, 18)
            minute_start = random.choice([0, 30])
            start_time = time(hour_start, minute_start)
            duration_hours = random.choice([1, 2])
            end_hour = hour_start + duration_hours
            end_time = time(end_hour, minute_start) if end_hour <= 23 else time(23, 0)

            event = Event(
                title=random.choice(titles) + f" #{i+1}",
                description=f"Автоматически сгенерированное мероприятие.\nДетали уточняйте у организатора.",
                event_date=event_date,
                start_time=start_time,
                end_time=end_time,
                location=random.choice(locations),
                category=random.choice(categories),
                organizer=random.choice([u.username for u in all_users]),
                user_id=random.choice(all_users).id
            )
            db.session.add(event)
            events_added += 1
        db.session.commit()
        print(f"✅ Добавлено {events_added} мероприятий.")

        print("\n🎉 Демо-данные успешно добавлены!")
        print("👤 Логины: alex/pass123, maria/pass123, ivan/pass123, nurs/1234qwe | admin/admin123")

if __name__ == '__main__':
    populate()