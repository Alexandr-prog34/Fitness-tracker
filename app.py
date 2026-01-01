import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='frontend')
CORS(app)

# Создаем папки если их нет
os.makedirs('frontend', exist_ok=True)

@app.route('/')
def home():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

@app.route('/api/health')
def health():
    return jsonify({
        "status": "running",
        "service": "Fitness Journal",
        "version": "1.0"
    })

@app.route('/api/workouts')
def workouts():
    return jsonify([
        {"id": 1, "type": "Бег", "duration": 30},
        {"id": 2, "type": "Йога", "duration": 45}
    ])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)