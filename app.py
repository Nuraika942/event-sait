from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time, timedelta
from models import db, User, Event
from forms import RegistrationForm, LoginForm, EventForm
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ---------- Автоматическое заполнение демо-данными ----------
def populate_demo_data():
    """Создаёт тестовых пользователей и мероприятия, если база пустая."""
    if Event.query.count() >= 5:
        print("База уже содержит данные, пропускаем заполнение.")
        return

    print("🔄 Добавляем демо-пользователей и мероприятия...")

    users_data = [
        ('alex', 'alex@example.com', 'pass123'),
        ('maria', 'maria@example.com', 'pass123'),
        ('ivan', 'ivan@example.com', 'pass123'),
        ('nurs', 'nurs@example.com', '1234qwe'),
    ]
    created = []
    for username, email, pwd in users_data:
        if not User.query.filter_by(username=username).first():
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(pwd),
                role='user'
            )
            db.session.add(user)
            created.append(username)
    db.session.commit()
    if created:
        print(f"✅ Добавлены пользователи: {', '.join(created)}")

    # Все пользователи (включая админа)
    all_users = User.query.all()
    if not all_users:
        return

    titles = [
        "Еженедельное собрание команды", "Презентация проекта", "День рождения коллеги",
        "Воркшоп по Python", "Конференция Digital", "Спортивный турнир", "Обед с партнёрами",
        "Технический аудит", "Тимбилдинг", "Вебинар по продажам"
    ]
    categories = ["Работа", "Личное", "Обучение", "Развлечения", "Спорт"]
    locations = ["Офис", "Зум", "Конференц-зал", "Парк", "Кафе", "Спортзал"]

    start_date = date.today()
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
            title=random.choice(titles) + f" #{i + 1}",
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

    db.session.commit()
    print(f"✅ Добавлено {Event.query.count()} мероприятий.")
    print("👤 Доступные логины: alex/pass123, maria/pass123, ivan/pass123, nurs/1234qwe | admin/admin123")


# ---------- Создание таблиц и наполнение ----------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('✅ Создан администратор: admin / admin123')
    populate_demo_data()


# ---------- Загрузка пользователя ----------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Доступ запрещён. Требуются права администратора.', 'danger')
            return redirect(url_for('dashboard'))
        return func(*args, **kwargs)

    return decorated_view


# ------------------ Маршруты ------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Имя пользователя уже занято', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email уже используется', 'danger')
            return render_template('register.html', form=form)
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    now = datetime.now()
    upcoming_events = []
    if current_user.role == 'admin':
        events = Event.query.filter(Event.event_date >= now.date()).order_by(Event.event_date, Event.start_time).all()
    else:
        events = Event.query.filter_by(user_id=current_user.id).filter(Event.event_date >= now.date()).order_by(
            Event.event_date, Event.start_time).all()

    for ev in events:
        ev_datetime = datetime.combine(ev.event_date, ev.start_time)
        if ev_datetime > now and ev_datetime <= now + timedelta(days=1):
            upcoming_events.append(ev)
    return render_template('dashboard.html', upcoming_events=upcoming_events)


@app.route('/events')
@login_required
def events():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'event_date')

    if current_user.role == 'admin':
        query = Event.query
    else:
        query = Event.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(Event.title.contains(search) | Event.description.contains(search))
    if category:
        query = query.filter(Event.category == category)

    if sort == 'event_date':
        query = query.order_by(Event.event_date, Event.start_time)
    elif sort == 'title':
        query = query.order_by(Event.title)

    events_list = query.all()
    categories = db.session.query(Event.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('events.html', events=events_list, search=search, category=category, categories=categories,
                           sort=sort)


@app.route('/event/new', methods=['GET', 'POST'])
@login_required
def event_create():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            event_date=form.event_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            location=form.location.data,
            category=form.category.data,
            organizer=form.organizer.data,
            user_id=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash('Мероприятие успешно создано!', 'success')
        return redirect(url_for('events'))
    return render_template('event_form.html', form=form, title='Новое мероприятие')


@app.route('/event/<int:id>')
@login_required
def event_detail(id):
    event = Event.query.get_or_404(id)
    if current_user.role != 'admin' and event.user_id != current_user.id:
        flash('У вас нет прав для просмотра этого мероприятия', 'danger')
        return redirect(url_for('events'))
    return render_template('event_detail.html', event=event)


@app.route('/event/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def event_edit(id):
    event = Event.query.get_or_404(id)
    if current_user.role != 'admin' and event.user_id != current_user.id:
        flash('У вас нет прав для редактирования', 'danger')
        return redirect(url_for('events'))
    form = EventForm(obj=event)
    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.event_date = form.event_date.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.location = form.location.data
        event.category = form.category.data
        event.organizer = form.organizer.data
        db.session.commit()
        flash('Мероприятие обновлено', 'success')
        return redirect(url_for('event_detail', id=event.id))
    return render_template('event_form.html', form=form, title='Редактирование мероприятия', event=event)


@app.route('/event/<int:id>/delete', methods=['POST'])
@login_required
def event_delete(id):
    event = Event.query.get_or_404(id)
    if current_user.role != 'admin' and event.user_id != current_user.id:
        flash('Нет прав для удаления', 'danger')
        return redirect(url_for('events'))
    db.session.delete(event)
    db.session.commit()
    flash('Мероприятие удалено', 'success')
    return redirect(url_for('events'))


@app.route('/calendar')
@login_required
def calendar_view():
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    if current_user.role == 'admin':
        events_in_month = Event.query.filter(Event.event_date >= first_day, Event.event_date <= last_day).all()
    else:
        events_in_month = Event.query.filter_by(user_id=current_user.id).filter(Event.event_date >= first_day,
                                                                                Event.event_date <= last_day).all()

    events_by_day = {}
    for ev in events_in_month:
        day = ev.event_date.day
        events_by_day.setdefault(day, []).append(ev)

    start_weekday = first_day.weekday()
    prev_month_days = start_weekday if start_weekday != 6 else 0
    if month == 1:
        prev_last_day = date(year - 1, 12, 1)
    else:
        prev_last_day = date(year, month - 1, 1)
    prev_last_day = (prev_last_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    cal_days = []
    for i in range(prev_month_days, 0, -1):
        cal_days.append(
            {'day': prev_last_day.day - i + 1, 'month': month - 1 if month > 1 else 12, 'current': False, 'events': []})
    for d in range(1, last_day.day + 1):
        cal_days.append({'day': d, 'month': month, 'current': True, 'events': events_by_day.get(d, [])})
    remaining = 42 - len(cal_days)
    for d in range(1, remaining + 1):
        cal_days.append({'day': d, 'month': month + 1 if month < 12 else 1, 'current': False, 'events': []})

    weeks = [cal_days[i:i + 7] for i in range(0, len(cal_days), 7)]
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    return render_template('calendar.html', weeks=weeks, current_year=year, current_month=month, prev_year=prev_year,
                           prev_month=prev_month, next_year=next_year, next_month=next_month)


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)


@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Нельзя удалить самого себя', 'danger')
        return redirect(url_for('admin_users'))
    Event.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {user.username} удалён', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/events')
@login_required
@admin_required
def admin_events():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('admin_events.html', events=events)


@app.route('/api/events', methods=['GET'])
@login_required
def api_events():
    if current_user.role == 'admin':
        events = Event.query.all()
    else:
        events = Event.query.filter_by(user_id=current_user.id).all()
    result = []
    for ev in events:
        result.append({
            'id': ev.id,
            'title': ev.title,
            'description': ev.description,
            'event_date': ev.event_date.isoformat(),
            'start_time': ev.start_time.strftime('%H:%M'),
            'end_time': ev.end_time.strftime('%H:%M'),
            'location': ev.location,
            'category': ev.category,
            'organizer': ev.organizer,
            'user_id': ev.user_id
        })
    return jsonify(result)


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)