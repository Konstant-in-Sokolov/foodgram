![CI](https://github.com/Konstant-in-Sokolov/foodgram/actions/workflows/main.yml/badge.svg)

ip: 51.250.27.166
логин/пароль для суперюзера
admin@adm.in
admin

# Foodgram
Учебный проект на REST API для публикации и управления рецептами.

## Функциональность

- Регистрация и аутентификация пользователей
- CRUD для рецептов с тегами и ингредиентами
- Загрузка изображений рецептов (base64)
- Добавление/удаление рецептов в избранное
- Подписка/отписка на авторов рецептов
- Генерация списка покупок (список ингредиентов)

## Технологии

- Python 3.12
- Django & Django REST Framework
- Djoser (аутентификация)
- PostgreSQL
- Docker & Docker Compose
- Nginx
- GitHub Actions (CI/CD)


## Установка и запуск с Docker

Клонируйте репозиторий и перейдите в папку проекта:
```bash
git clone https://github.com/Konstant-in-Sokolov/foodgram.git
cd foodgram
```
Создайте файл .env по шаблону:
```bash
SECRET_KEY=<ваш_секрет>
DEBUG=False
ALLOWED_HOSTS=<ваш_домен>
POSTGRES_DB=<имя_бд>
POSTGRES_USER=<пользователь_бд>
POSTGRES_PASSWORD=<пароль_бд>
DB_HOST=db
DB_PORT=5432
```
Запуск сборки и поднятие контейнеров:
```bash
docker compose -f docker-compose.yml up -d --build
```

## локальный запуск без Docker

Установите зависимости Python:
```bash
cd backend/
python -m venv venv
source venv/scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
```
Установите зависимости фронтенда:
```bash
cd ../frontend/
npm ci
```
Настройте .env, мигрируйте БД и запустите проект:
```bash
cd ../backend/
python manage.py migrate
python manage.py runserver
```
API будет доступен по адресу http://127.0.0.1:8000/api/.


## CI/CD

- Автоматический запуск тестов
- Сборка и публикация Docker-образов
- Деплой на сервер через SSH и Docker Compose

## Примеры API эндпоинтов

Ниже приведены основные пути для работы с REST API:

- POST `/api/users/`  Регистрация нового пользователя
- POST `/api/auth/token/` Получение токена
- GET `/api/users/me/`   Получение данных текущего пользователя
- GET `/api/subscriptions/`   Список текущих подписок


## Автор

Константин Соколов