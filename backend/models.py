from datetime import datetime
from database import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связь с тренировками
    workouts = db.relationship('Workout', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'workout_count': len(self.workouts)
        }


class Workout(db.Model):
    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    workout_type = db.Column(db.String(50), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    calories_burned = db.Column(db.Integer)
    distance_km = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'workout_type': self.workout_type,
            'duration_minutes': self.duration_minutes,
            'calories_burned': self.calories_burned,
            'distance_km': self.distance_km,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }