from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from datetime import datetime

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Пароль', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = StringField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class EventForm(FlaskForm):
    title = StringField('Название мероприятия', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание')
    event_date = DateField('Дата проведения', validators=[DataRequired()], format='%Y-%m-%d')
    start_time = TimeField('Время начала', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('Время окончания', validators=[DataRequired()], format='%H:%M')
    location = StringField('Место проведения', validators=[DataRequired()])
    category = StringField('Категория', validators=[DataRequired()])
    organizer = StringField('Ответственный организатор', validators=[DataRequired()])
    submit = SubmitField('Сохранить')

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError('Время окончания должно быть позже времени начала')