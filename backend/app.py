from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flasgger import Swagger
from datetime import datetime
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

# Импорт модулей
from database import db, init_db
from models import User, Workout
from auth import hash_password, check_password, generate_token, token_required

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Конфигурация
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'

# Инициализация базы данных
db.init_app(app)
with app.app_context():
    db.create_all()

# Настройка Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api-docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Fitness Journal API",
        "description": "API для фитнес-журнала с аккаунтами пользователей",
        "version": "1.0.0",
        "contact": {
            "name": "Разработчик",
            "email": "developer@example.com"
        }
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT токен в формате: Bearer {token}"
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)


# Статические файлы
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ==================== Аутентификация ====================

@app.route('/api/register', methods=['POST'])
def register():
    """
    Регистрация нового пользователя
    ---
    tags:
      - Аутентификация
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              description: Имя пользователя
            email:
              type: string
              description: Email адрес
            password:
              type: string
              description: Пароль
    responses:
      201:
        description: Пользователь успешно зарегистрирован
      400:
        description: Ошибка валидации
    """
    data = request.get_json()

    # Валидация
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Все поля обязательны'}), 400

    # Проверка существующего пользователя
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Имя пользователя уже занято'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email уже зарегистрирован'}), 400

    # Создание пользователя
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hash_password(data['password'])
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Пользователь успешно зарегистрирован'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    """
    Вход в систему
    ---
    tags:
      - Аутентификация
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: Имя пользователя
            password:
              type: string
              description: Пароль
    responses:
      200:
        description: Успешный вход
      401:
        description: Неверные учетные данные
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Имя пользователя и пароль обязательны'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password(data['password'], user.password_hash):
        return jsonify({'error': 'Неверные учетные данные'}), 401

    token = generate_token(user.id)

    return jsonify({
        'token': token,
        'user': user.to_dict()
    }), 200


# ==================== Тренировки ====================

@app.route('/api/workouts', methods=['GET'])
@token_required
def get_workouts():
    """
    Получение списка тренировок пользователя
    ---
    tags:
      - Тренировки
    security:
      - Bearer: []
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
        description: Начальная дата фильтрации
      - name: end_date
        in: query
        type: string
        format: date
        description: Конечная дата фильтрации
      - name: workout_type
        in: query
        type: string
        description: Тип тренировки для фильтрации
    responses:
      200:
        description: Список тренировок
    """
    user = request.current_user

    # Фильтры
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    workout_type = request.args.get('workout_type')

    query = Workout.query.filter_by(user_id=user.id)

    if start_date:
        query = query.filter(Workout.date >= datetime.strptime(start_date, '%Y-%m-%d').date())

    if end_date:
        query = query.filter(Workout.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    if workout_type:
        query = query.filter(Workout.workout_type == workout_type)

    workouts = query.order_by(Workout.date.desc()).all()

    return jsonify([workout.to_dict() for workout in workouts]), 200


@app.route('/api/workouts', methods=['POST'])
@token_required
def create_workout():
    """
    Создание новой тренировки
    ---
    tags:
      - Тренировки
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - date
            - workout_type
            - duration_minutes
          properties:
            date:
              type: string
              format: date
              description: Дата тренировки
            workout_type:
              type: string
              description: Тип тренировки
            duration_minutes:
              type: integer
              description: Продолжительность в минутах
            calories_burned:
              type: integer
              description: Сожженные калории
            distance_km:
              type: number
              format: float
              description: Дистанция в километрах
            notes:
              type: string
              description: Дополнительные заметки
    responses:
      201:
        description: Тренировка создана
      400:
        description: Ошибка валидации
    """
    user = request.current_user
    data = request.get_json()

    # Валидация обязательных полей
    if not data or 'date' not in data or 'workout_type' not in data or 'duration_minutes' not in data:
        return jsonify({'error': 'Дата, тип и продолжительность обязательны'}), 400

    try:
        workout = Workout(
            user_id=user.id,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            workout_type=data['workout_type'],
            duration_minutes=data['duration_minutes'],
            calories_burned=data.get('calories_burned'),
            distance_km=data.get('distance_km'),
            notes=data.get('notes')
        )

        db.session.add(workout)
        db.session.commit()

        return jsonify(workout.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': f'Ошибка в данных: {str(e)}'}), 400


@app.route('/api/workouts/<int:workout_id>', methods=['GET'])
@token_required
def get_workout(workout_id):
    """
    Получение конкретной тренировки
    ---
    tags:
      - Тренировки
    security:
      - Bearer: []
    parameters:
      - name: workout_id
        in: path
        type: integer
        required: true
        description: ID тренировки
    responses:
      200:
        description: Данные тренировки
      404:
        description: Тренировка не найдена
    """
    user = request.current_user
    workout = Workout.query.filter_by(id=workout_id, user_id=user.id).first()

    if not workout:
        return jsonify({'error': 'Тренировка не найдена'}), 404

    return jsonify(workout.to_dict()), 200


@app.route('/api/workouts/<int:workout_id>', methods=['PUT'])
@token_required
def update_workout(workout_id):
    """
    Обновление тренировки
    ---
    tags:
      - Тренировки
    security:
      - Bearer: []
    parameters:
      - name: workout_id
        in: path
        type: integer
        required: true
        description: ID тренировки
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            date:
              type: string
              format: date
            workout_type:
              type: string
            duration_minutes:
              type: integer
            calories_burned:
              type: integer
            distance_km:
              type: number
              format: float
            notes:
              type: string
    responses:
      200:
        description: Тренировка обновлена
      404:
        description: Тренировка не найдена
    """
    user = request.current_user
    workout = Workout.query.filter_by(id=workout_id, user_id=user.id).first()

    if not workout:
        return jsonify({'error': 'Тренировка не найдена'}), 404

    data = request.get_json()

    if 'date' in data:
        workout.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'workout_type' in data:
        workout.workout_type = data['workout_type']
    if 'duration_minutes' in data:
        workout.duration_minutes = data['duration_minutes']
    if 'calories_burned' in data:
        workout.calories_burned = data['calories_burned']
    if 'distance_km' in data:
        workout.distance_km = data['distance_km']
    if 'notes' in data:
        workout.notes = data['notes']

    db.session.commit()

    return jsonify(workout.to_dict()), 200


@app.route('/api/workouts/<int:workout_id>', methods=['DELETE'])
@token_required
def delete_workout(workout_id):
    """
    Удаление тренировки
    ---
    tags:
      - Тренировки
    security:
      - Bearer: []
    parameters:
      - name: workout_id
        in: path
        type: integer
        required: true
        description: ID тренировки
    responses:
      200:
        description: Тренировка удалена
      404:
        description: Тренировка не найдена
    """
    user = request.current_user
    workout = Workout.query.filter_by(id=workout_id, user_id=user.id).first()

    if not workout:
        return jsonify({'error': 'Тренировка не найдена'}), 404

    db.session.delete(workout)
    db.session.commit()

    return jsonify({'message': 'Тренировка удалена'}), 200


# ==================== Статистика ====================

@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats():
    """
    Получение статистики тренировок
    ---
    tags:
      - Статистика
    security:
      - Bearer: []
    parameters:
      - name: period
        in: query
        type: string
        enum: [week, month, year, all]
        default: month
        description: Период для статистики
    responses:
      200:
        description: Статистика тренировок
    """
    user = request.current_user
    period = request.args.get('period', 'month')

    # Расчет дат в зависимости от периода
    end_date = datetime.now().date()

    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    elif period == 'year':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = None

    query = Workout.query.filter_by(user_id=user.id)
    if start_date:
        query = query.filter(Workout.date >= start_date)

    workouts = query.all()

    # Расчет статистики
    total_workouts = len(workouts)
    total_duration = sum(w.duration_minutes for w in workouts)
    total_calories = sum(w.calories_burned or 0 for w in workouts)
    total_distance = sum(w.distance_km or 0 for w in workouts)

    # Статистика по типам тренировок
    workout_types = {}
    for workout in workouts:
        workout_type = workout.workout_type
        if workout_type not in workout_types:
            workout_types[workout_type] = {
                'count': 0,
                'total_duration': 0,
                'total_calories': 0
            }

        workout_types[workout_type]['count'] += 1
        workout_types[workout_type]['total_duration'] += workout.duration_minutes
        workout_types[workout_type]['total_calories'] += workout.calories_burned or 0

    return jsonify({
        'total_workouts': total_workouts,
        'total_duration_minutes': total_duration,
        'total_calories_burned': total_calories,
        'total_distance_km': total_distance,
        'workout_types': workout_types,
        'period': period,
        'start_date': start_date.isoformat() if start_date else None,
        'end_date': end_date.isoformat()
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)