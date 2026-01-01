// Конфигурация API
const API_BASE_URL = 'http://localhost:5001/api';

// Состояние приложения
let currentUser = null;
let workouts = [];
let stats = {};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setDefaultDates();

    // Проверяем авторизацию при загрузке страницы
    const token = localStorage.getItem('token');
    if (token) {
        loadUserData();
        loadWorkouts();
        loadStats();
    }
});

// Установка дат по умолчанию
function setDefaultDates() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('workoutDate').value = today;

    // Устанавливаем даты для фильтров (последние 30 дней)
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    document.getElementById('filterDateFrom').value = thirtyDaysAgo.toISOString().split('T')[0];
    document.getElementById('filterDateTo').value = today;
}

// Проверка авторизации
function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        showMainContent();
    } else {
        showAuthButtons();
    }
}

// Отображение интерфейса
function showAuthButtons() {
    document.getElementById('authButtons').style.display = 'flex';
    document.getElementById('userInfo').style.display = 'none';
    document.getElementById('mainContent').style.display = 'none';
    document.getElementById('authSection').style.display = 'none';
}

function showMainContent() {
    document.getElementById('authButtons').style.display = 'none';
    document.getElementById('userInfo').style.display = 'flex';
    document.getElementById('mainContent').style.display = 'block';
    document.getElementById('authSection').style.display = 'none';
}

function showLogin() {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

function showRegister() {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function hideAuth() {
    document.getElementById('authSection').style.display = 'none';
}

// Уведомления
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// API запросы
async function makeRequest(url, options = {}) {
    const token = localStorage.getItem('token');

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка сервера');
        }

        return await response.json();
    } catch (error) {
        showNotification(error.message, 'error');
        throw error;
    }
}

// Аутентификация
async function login(event) {
    event.preventDefault();

    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const data = await makeRequest('/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        localStorage.setItem('token', data.token);
        currentUser = data.user;

        document.getElementById('username').textContent = currentUser.username;
        showNotification('Успешный вход!', 'success');

        hideAuth();
        showMainContent();
        loadWorkouts();
        loadStats();

        // Очистка формы
        document.getElementById('loginFormElement').reset();
    } catch (error) {
        console.error('Login error:', error);
    }
}

async function register(event) {
    event.preventDefault();

    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    // Проверка паролей
    if (password !== confirmPassword) {
        showNotification('Пароли не совпадают', 'error');
        return;
    }

    try {
        await makeRequest('/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });

        showNotification('Регистрация успешна! Теперь войдите в систему.', 'success');
        showLogin();

        // Очистка формы
        document.getElementById('registerFormElement').reset();
    } catch (error) {
        console.error('Registration error:', error);
    }
}

function logout() {
    localStorage.removeItem('token');
    currentUser = null;
    workouts = [];
    stats = {};

    showNotification('Вы вышли из системы', 'info');
    showAuthButtons();
}

// Загрузка данных пользователя
async function loadUserData() {
    try {
        // В этом примере нет отдельного endpoint для данных пользователя
        // Используем данные из токена или обновляем после входа
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Тренировки
async function loadWorkouts() {
    try {
        const data = await makeRequest('/workouts');
        workouts = data;
        renderWorkouts();
    } catch (error) {
        console.error('Error loading workouts:', error);
    }
}

function renderWorkouts() {
    const workoutsList = document.getElementById('workoutsList');
    const searchTerm = document.getElementById('searchWorkouts').value.toLowerCase();
    const filterType = document.getElementById('filterType').value;
    const dateFrom = document.getElementById('filterDateFrom').value;
    const dateTo = document.getElementById('filterDateTo').value;

    let filteredWorkouts = [...workouts];

    // Фильтрация
    if (searchTerm) {
        filteredWorkouts = filteredWorkouts.filter(workout =>
            workout.notes && workout.notes.toLowerCase().includes(searchTerm)
        );
    }

    if (filterType) {
        filteredWorkouts = filteredWorkouts.filter(workout =>
            workout.workout_type === filterType
        );
    }

    if (dateFrom) {
        filteredWorkouts = filteredWorkouts.filter(workout =>
            workout.date >= dateFrom
        );
    }

    if (dateTo) {
        filteredWorkouts = filteredWorkouts.filter(workout =>
            workout.date <= dateTo
        );
    }

    if (filteredWorkouts.length === 0) {
        workoutsList.innerHTML = `
            <div class="workout-card">
                <p style="text-align: center; color: #666;">Тренировки не найдены</p>
            </div>
        `;
        return;
    }

    workoutsList.innerHTML = filteredWorkouts.map(workout => `
        <div class="workout-card">
            <div class="workout-header">
                <span class="workout-date">${formatDate(workout.date)}</span>
                <span class="workout-type">${workout.workout_type}</span>
            </div>
            <div class="workout-details">
                <div class="workout-detail">
                    <i class="fas fa-clock"></i>
                    <span>${workout.duration_minutes} мин</span>
                </div>
                ${workout.calories_burned ? `
                <div class="workout-detail">
                    <i class="fas fa-fire"></i>
                    <span>${workout.calories_burned} ккал</span>
                </div>
                ` : ''}
                ${workout.distance_km ? `
                <div class="workout-detail">
                    <i class="fas fa-route"></i>
                    <span>${workout.distance_km} км</span>
                </div>
                ` : ''}
            </div>
            ${workout.notes ? `
            <div class="workout-notes">
                <strong>Заметки:</strong> ${workout.notes}
            </div>
            ` : ''}
            <div class="workout-actions">
                <button onclick="openEditModal(${workout.id})" class="btn btn-secondary">
                    <i class="fas fa-edit"></i> Редактировать
                </button>
            </div>
        </div>
    `).join('');
}

function filterWorkouts() {
    renderWorkouts();
}

async function addWorkout(event) {
    event.preventDefault();

    const workout = {
        date: document.getElementById('workoutDate').value,
        workout_type: document.getElementById('workoutType').value,
        duration_minutes: parseInt(document.getElementById('duration').value),
        calories_burned: document.getElementById('calories').value ?
                         parseInt(document.getElementById('calories').value) : null,
        distance_km: document.getElementById('distance').value ?
                     parseFloat(document.getElementById('distance').value) : null,
        notes: document.getElementById('notes').value || null
    };

    try {
        await makeRequest('/workouts', {
            method: 'POST',
            body: JSON.stringify(workout)
        });

        showNotification('Тренировка добавлена!', 'success');
        document.getElementById('addWorkoutForm').reset();
        setDefaultDates();

        loadWorkouts();
        loadStats();
    } catch (error) {
        console.error('Error adding workout:', error);
    }
}

// Редактирование тренировок
function openEditModal(workoutId) {
    const workout = workouts.find(w => w.id === workoutId);
    if (!workout) return;

    document.getElementById('editWorkoutId').value = workout.id;
    document.getElementById('editWorkoutDate').value = workout.date;
    document.getElementById('editWorkoutType').value = workout.workout_type;
    document.getElementById('editDuration').value = workout.duration_minutes;
    document.getElementById('editCalories').value = workout.calories_burned || '';
    document.getElementById('editDistance').value = workout.distance_km || '';
    document.getElementById('editNotes').value = workout.notes || '';

    document.getElementById('editModal').style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

async function updateWorkout(event) {
    event.preventDefault();

    const workoutId = document.getElementById('editWorkoutId').value;
    const workout = {
        date: document.getElementById('editWorkoutDate').value,
        workout_type: document.getElementById('editWorkoutType').value,
        duration_minutes: parseInt(document.getElementById('editDuration').value),
        calories_burned: document.getElementById('editCalories').value ?
                         parseInt(document.getElementById('editCalories').value) : null,
        distance_km: document.getElementById('editDistance').value ?
                     parseFloat(document.getElementById('editDistance').value) : null,
        notes: document.getElementById('editNotes').value || null
    };

    try {
        await makeRequest(`/workouts/${workoutId}`, {
            method: 'PUT',
            body: JSON.stringify(workout)
        });

        showNotification('Тренировка обновлена!', 'success');
        closeEditModal();

        loadWorkouts();
        loadStats();
    } catch (error) {
        console.error('Error updating workout:', error);
    }
}

async function deleteWorkout() {
    const workoutId = document.getElementById('editWorkoutId').value;

    if (!confirm('Вы уверены, что хотите удалить эту тренировку?')) {
        return;
    }

    try {
        await makeRequest(`/workouts/${workoutId}`, {
            method: 'DELETE'
        });

        showNotification('Тренировка удалена!', 'success');
        closeEditModal();

        loadWorkouts();
        loadStats();
    } catch (error) {
        console.error('Error deleting workout:', error);
    }
}

// Статистика
async function loadStats() {
    const period = document.getElementById('periodSelect').value;

    try {
        stats = await makeRequest(`/stats?period=${period}`);
        renderStats();
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function renderStats() {
    const statsGrid = document.getElementById('statsGrid');

    if (!stats.total_workouts) {
        statsGrid.innerHTML = `
            <div class="stat-card">
                <h3>0</h3>
                <p>Нет тренировок за выбранный период</p>
            </div>
        `;
        return;
    }

    statsGrid.innerHTML = `
        <div class="stat-card">
            <h3>${stats.total_workouts}</h3>
            <p>Всего тренировок</p>
        </div>
        <div class="stat-card">
            <h3>${Math.round(stats.total_duration_minutes / 60)}</h3>
            <p>Часов тренировок</p>
        </div>
        ${stats.total_calories_burned ? `
        <div class="stat-card">
            <h3>${stats.total_calories_burned}</h3>
            <p>Сожжено калорий</p>
        </div>
        ` : ''}
        ${stats.total_distance_km ? `
        <div class="stat-card">
            <h3>${stats.total_distance_km.toFixed(1)}</h3>
            <p>Километров пройдено</p>
        </div>
        ` : ''}
    `;

    // Добавляем статистику по типам тренировок
    if (stats.workout_types && Object.keys(stats.workout_types).length > 0) {
        Object.entries(stats.workout_types).forEach(([type, data]) => {
            const typeCard = document.createElement('div');
            typeCard.className = 'stat-card';
            typeCard.innerHTML = `
                <h3>${data.count}</h3>
                <p>${type}</p>
                <small>${data.total_duration} мин</small>
            `;
            statsGrid.appendChild(typeCard);
        });
    }
}

// Вспомогательные функции
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}