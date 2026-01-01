import jwt
import bcrypt
from datetime import datetime, timedelta
from flask import current_app
from functools import wraps
from flask import request, jsonify
from models import User


def hash_password(password):
    """Хеширование пароля"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def check_password(password, hashed_password):
    """Проверка пароля"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_token(user_id):
    """Генерация JWT токена"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def decode_token(token):
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Декоратор для защиты endpoint'ов"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]

        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Неверный или просроченный токен'}), 401

        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 401

        request.current_user = user
        return f(*args, **kwargs)

    return decorated