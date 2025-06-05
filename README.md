# Mfdp

# Проект: Предиктивная аналитика городской мобильности

## Фаза 1. Бизнес-анализ (Business Understanding)

### 1.1 Цели и описание проекта

**Общая задача:** Прогнозирование спроса на услуги такси и каршеринга в городской среде (например, Нью-Йорк) с точностью до квартала и часа.

**Организационная структура:** Один разработчик.

**Предполагаемые пользователи:** Службы такси, операторы каршеринга, городской департамент транспорта.

**Бизнес-цель:** Сократить время ожидания машины и оптимизировать распределение автопарка, снижая «простой» и неэффективные перераспределения.

**Аналоги:** Yandex Go, Uber (информации нет в открытом доступе, но реализация использует комбинацию LSTM, GBDT и GNN). Решения принадлежат коммерческим компаниям, которые не публикуют их в открытом доступе.

---

### 1.2 Текущая ситуация (Assessing current solution)

**Данные:** 
- На начальных этапах хранятся на локальной машине, версионность поддерживается с помощью DVC.  
- При масштабировании будет переход к облачным решениям.  
- Данные будут в открытом доступе.

**Ресурсы:**  
- Есть локальная машина средней мощности.  
- При необходимости во время разработки будут рассмотрены облачные решения и/или закупка дополнительного «железа».  

**Основные датасеты:**
- NYC TLC Trip Record Data  
- Uber Travel Movement Data  
- Kaggle (NYC Taxi Trip Duration, Chicago Taxi Trips)

**Риски:**
1. Большой объём исходных данных (может потребоваться агрегация, downsampling).
2. Пропуски и шум в геолокациях или временных метках.
3. Сжатые сроки и большой выбор моделей реализации.
4. Возможные проблемы с интерпретацией/отладкой продвинутых моделей (LSTM/Transformer).

**Снижение рисков:**
1. Сократить детализацию.
2. На этапе экспериментов брать выборку данных за ограниченный период.
3. Обрабатывать пропуски (удалять или заменять наиболее часто встречающимися значениями) и фильтровать данные.
4. Реализовывать версии от простой к более продвинутой, чтобы сразу иметь рабочую версию проекта и улучшать её.
5. Для продвинутых моделей — поэтапное усложнение (по мере готовности предыдущего этапа).

---

### 1.3 Решаемые задачи с точки зрения аналитики (Data Mining Goals)

**ML-задача:** Прогнозировать объём поездок (т.е. спрос) на каждый час в каждом квартале.

**Метрики:** RMSE, MAE.

**Критерий успеха:** Каждая модель должна обгонять наивные решения на 15–20% по RMSE/MAE.

**Итоговый критерий успеха:** 
Каждая модель должна обгонять наивные решения на 15–20% по RMSE/MAE.
Показывает MAPE < 20% в большинстве зон.
Сохраняет стабильность ошибок между районами (std < 10% от среднего MAE).

---

### 1.4 План проекта (общий обзор)

1. **Бизнес-анализ (Business Understanding):** 1 неделя

2. **Анализ данных (Data Understanding):** 1 неделя
   - Сбор и первичный обзор данных
   - Первичная статистика и визуализация
   - Выводы об объёме и качестве данных

3. **Подготовка данных (Data Preparation):** 1 неделя
   - Фильтрация данных
   - Инженерия признаков (Feature Engineering)
   - Формирование выборок для обучения

4. **Моделирование (Modeling):** 2 недели
   - Наивные модели (Baseline)
   - Рекуррентная нейронная сеть (LSTM)
   - Опциональная продвинутая модель (Transformer)

5. **Оценка результатов (Evaluation):** 1 неделя
   - Сравнение моделей
   - Интерпретация и выводы
   - Выбор финальной модели

6. **Внедрение (Deployment):** 2 недели
   - Подготовка к продакшн-среде
   - Итеративное улучшение


# Проект: OTF (OpenTaxiForecast)

**Описание:**  
OTF — сервис для прогнозирования спроса на такси по районам города в режиме онлайн. Включает FastAPI-backend, асинхронный воркер на Celery, фронтенд на React/Vite, Telegram-бота и Nginx-прокси.

---

## Содержание

1. [Краткий обзор](#краткий-обзор)  
2. [Архитектура проекта](#архитектура-проекта)  
3. [Backend (FastAPI)](#backend-fastapi)
   - [Эндпоинты API](#эндпоинты-api)
4. [Воркеры (RabbitMQ)](#воркеры-rabbitmq)  
5. [Frontend (React + Vite + TailwindCSS)](#frontend-react--vite--tailwindcss)
   - [Структура и страницы](#структура-и-страницы)
6. [Telegram-бот](#telegram-бот)
7. [Nginx-proxy](#nginx-proxy)
8. [Docker Compose](#docker-compose)  
9. [Контакты и поддержка](#контакты-и-поддержка)  

---

## Краткий обзор

OTF (OpenTaxiForecast) — это платформа для прогнозирования спроса на такси в городах.  Она предоставляет:

- **Быстрый REST API** для регистрации, авторизации, работы с балансом и историей транзакций, создания и получения результатов предсказаний.  
- **Асинхронные воркеры на Celery**, которые выполняют расчёты LSTM-модели и сохраняют результаты в базу данных.  
- **Современный SPA-фронтенд** на React/Vite с TailwindCSS, включающий защищённые маршруты и визуализацию данных.  
- **Telegram-бот** для быстрых запросов баланса и истории транзакций через мессенджер.  
- **Nginx-прокси** для отдачи фронтенда и проксирования API-запросов на backend.  

---

## Архитектура

```
app/
├── backend/
│   ├── api/
│   │   └── v1/
│   │       ├── schemas/
│   │       │   ├── auth.py          # Pydantic-схемы для запросов/ответов Auth
│   │       │   ├── balance.py       # Pydantic-схемы для запросов/ответов Balance
│   │       │   └── prediction.py    # Pydantic-схемы для запросов/ответов Prediction
│   │       ├── auth.py              # Роуты аутентификации: /api/v1/auth/*
│   │       ├── balance.py           # Роуты работы с балансом: /api/v1/balance/*
│   │       └── prediction.py        # Роуты прогнозов: /api/v1/prediction/*
│   ├── db/
│   │   ├── models/
│   │   │   ├── balance.py           # SQLAlchemy-модель транзакций баланса
│   │   │   ├── prediction.py        # SQLAlchemy-модель прогноза
│   │   │   └── user.py              # SQLAlchemy-модель пользователя
│   │   ├── config.py                # Конфигурация подключения к БД
│   │   └── db.py                    # Инициализация сессии SQLAlchemy
│   ├── services/
│   │   ├── core/
│   │   │   ├── enums.py             # Перечисления статусов (например, UserStatus)
│   │   │   ├── ml_model.py          # Логика ML-модели для прогноза
│   │   │   └── security.py          # JWT-шифрование, проверка токенов, hashing пароля
│   │   ├── balance_manager.py       # Операции пополнения баланса, истории транзакций
│   │   ├── data_manager.py          # Загрузка/предобработка данных (для ML)
│   │   ├── prediction_manager.py    # Управление задачами прогнозов, связь с очередью
│   │   └── user_manager.py          # Создание пользователя, проверка логина/пароля
│   ├── workers/
│   │   ├── connection.py            # Настройка подключения к RabbitMQ
│   │   ├── Dockerfile               # Сборка образа worker
│   │   ├── publisher.py             # Отправка задачи прогнозирования в очередь
│   │   └── worker.py                # Выполнение задач: вычисление прогноза, запись в БД
│   ├── Dockerfile                   # Сборка образа backend
│   ├── main.py                      # Запуск FastAPI-приложения
│   ├── main_test.py                 # Тесты для services
│   ├── requirements-backend.txt     # Зависимости для backend
│   └── requirements-worker.txt      # Зависимости для worker
├── frontend/
│   ├── public/
│   │   └── logo_v1.png     # Логотип и favicon
│   ├── src/
│   │   ├── assets/                  # Статические файлы (изображения, шрифты)
│   │   ├── components/              # Повторно используемые React-компоненты
│   │   ├── pages/                   # Страницы приложения (Home, Login, Balance, Info, Prediction, и т.д.)
│   │   ├── services/                # API-клиент, утилиты (axios-инстанс и т.д.)
│   │   ├── App.jsx                  # Точка входа React, реализация маршрутов (React Router)
│   │   ├── main.jsx                 # Монтирование React в HTML
│   │   ├── index.css                # Базовые глобальные стили
│   │   └── App.css                  # Стили компонентов (Tailwind + CSS)
│   ├── .eslintrc.cjs                # Конфигурация ESLint
│   ├── .prettierrc                  # Конфигурация Prettier
│   ├── Dockerfile                   # Сборка образа frontend (Vite + React)
│   ├── eslint.config.js             # Конфиг ESLint (дополнительные правила при необходимости)
│   ├── index.html                   # HTML-шаблон (удобно для dev-сервера)
│   ├── package.json                 # Скрипты, зависимости frontend
│   ├── postcss.config.js            # Конфиг PostCSS (TailwindCSS)
│   ├── tailwind.config.js           # Конфиг TailwindCSS (темы, плагины)
│   └── vite.config.js               # Конфиг Vite (alias, proxy для API)
└── tg_bot/
    ├── bot.py                       # Логика Telegram-бота (вебхук или polling)
    ├── Dockerfile                   # Сборка образа tg_bot
    └── requirements.txt             # Зависимости для бота
```

---

## Backend (FastAPI)

### Эндпоинты API

Все маршруты находятся под префиксом `/api/v1`. Для защищённых маршрутов требуется заголовок:
```
Authorization: Bearer <JWT_TOKEN>
```

#### 1. Auth (файл `app/auth.py`)

##### Регистрация нового пользователя
```
POST /api/v1/auth/register
```
- **Request Body** (JSON):
  ```json
  {
    "username": "user123",
    "password": "mypassword"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "access_token": "<JWT_TOKEN>",
    "token_type": "bearer",
    "bot_token": "<BOT_TOKEN>"
  }
  ```

##### Аутентификация (логин)
```
POST /api/v1/auth/login
```
- **Request Body** (JSON):
  ```json
  {
    "username": "user123",
    "password": "mypassword"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "<JWT_TOKEN>",
    "token_type": "bearer",
    "bot_token": "<BOT_TOKEN>"
  }
  ```

##### Получение информации о текущем пользователе
```
GET /api/v1/auth/me
```
- **Headers**:  
  `Authorization: Bearer <JWT_TOKEN>`
- **Response (200 OK)**:
  ```json
  {
    "username": "user123",
    "balance": 350.0,
    "status": "silver",
    "status_date_end": "2025-07-01"
  }
  ```

---

#### 2. Balance (файл `app/balance.py`)

##### Пополнение баланса
```
POST /api/v1/balance/top_up
```
- **Headers**:  
  `Authorization: Bearer <JWT_TOKEN>`
- **Request Body** (JSON):
  ```json
  {
    "amount": 250.0
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "new_balance": 600.0,
    "amount": 250.0
  }
  ```

##### Покупка (продление) статуса (silver, gold, diamond)
```
POST /api/v1/balance/purchase
```
- **Headers**:  
  `Authorization: Bearer <JWT_TOKEN>`
- **Request Body** (JSON):
  ```json
  {
    "status": "gold"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "gold",
    "status_date_end": "2025-08-10",
    "remaining_balance": 420.0
  }
  ```
- **Ошибки**:
  - `400 Bad Request`: неверный статус или недостаточно средств.

##### История операций с балансом
```
POST /api/v1/balance/history
```
- **Headers**:  
  `Authorization: Bearer <JWT_TOKEN>`
- **Request Body** (JSON, необязательное поле `amount` — число записей):
  ```json
  {
    "amount": 5
  }
  ```
  По умолчанию вернёт 5 последних записей, если `amount` не задан.
- **Response (200 OK)**:
  ```json
  {
    "history": [
      {
        "amount": 250.0,
        "description": "Пополнение счёта",
        "timestamp": "2025-06-05 18:00:00"
      },
      {
        "amount": -100.0,
        "description": "Покупка статуса silver",
        "timestamp": "2025-06-04 12:30:00"
      },
      ...
    ]
  }
  ```

---

#### 3. Prediction (файл `app/prediction.py`)

##### Бесплатное предсказание для NYC
```
POST /api/v1/prediction/nyc_free
```
- **Headers**:  
  `Authorization: Bearer <JWT_TOKEN>`
- **Request Body** (JSON):
  ```json
  {
    "district": 3
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 27,
    "model": "lstm",
    "city": "NYC",
    "district": 3,
    "hour": 14,
    "cost": 0.0,
    "status": "processing",
    "result": null,
    "timestamp": "2025-06-06 14:00:00"
  }
  ```
- **Ошибки**:
  - `429 Too Many Requests`: если пользователь исчерпал лимит бесплатных запросов.

##### Платное предсказание для NYC
```
POST /api/v1/prediction/nyc_cost
```
- **Headers**:  
  `Authorization: Bearer <JWT_TOKEN>`
- **Request Body** (JSON):
  ```json
  {
    "district": 5
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": 28,
    "model": "lstm",
    "city": "NYC",
    "district": 5,
    "hour": 15,
    "cost": 10.0,
    "status": "processing",
    "result": null,
    "timestamp": "2025-06-06 15:00:00"
  }
  ```
- **Ошибки**:
  - `402 Payment Required`: если недостаточно средств для платного запроса.

##### История предсказаний текущего пользователя
```
POST /api/v1/prediction/history
```
- **Headers**:  
  `Authorization: Bearer <JWT_TOKEN>`
- **Request Body** (JSON, необязательное поле `amount` — число записей):
  ```json
  {
    "amount": 5
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "history": [
      {
        "id": 28,
        "model": "lstm",
        "city": "NYC",
        "district": 5,
        "hour": 15,
        "cost": 10.0,
        "status": "completed",
        "result": "[5,6,7,8,10,12,11,9,7,6,5,4,3,4,6,9,11,13,15,14,12,10,8]",
        "timestamp": "2025-06-06 15:00:00"
      },
      ...
    ]
  }
  ```

##### Получение результата конкретного предсказания по ID
```
GET /api/v1/prediction/{prediction_id}
```
- **Headers**:  
  `Authorization: Bearer <JWT_TOKEN>`
- **Response (200 OK)** (если задача завершена):
  ```json
  {
    "id": 28,
    "model": "lstm",
    "city": "NYC",
    "district": 5,
    "hour": 15,
    "cost": 10.0,
    "status": "completed",
    "result": "[5,6,7,8,10,12,11,9,7,6,5,4,3,4,6,9,11,13,15,14,12,10,8]",
    "timestamp": "2025-06-06 15:00:00"
  }
  ```
- **Response (202 Accepted)** (если в обработке):
  ```json
  {
    "id": 29,
    "model": "lstm",
    "city": "NYC",
    "district": 7,
    "hour": 16,
    "cost": 0.0,
    "status": "processing",
    "result": null,
    "timestamp": "2025-06-06 16:00:00"
  }
  ```
- **Ошибки**:
  - `404 Not Found`: если указанного ID не существует или не принадлежит пользователю.

---

## Воркеры (RabbitMQ)

Воркеры реализованы в папке `workers/`. Используется RabbitMQ как брокер очередей и результат в базе данных.

- **tasks.py** содержит задачи:
  - `publish_prediction_task` — создаёт запись в БД и отправляет задачу на выполнение LSTM-модели.

Запуск воркеров (через Docker Compose) автоматически подключается к RabbitMQ и обрабатывает все очереди.

---

## Frontend (React + Vite + TailwindCSS)

### Установка и запуск

1. Перейти в папку `frontend`:
   ```bash
   cd frontend
   npm install
   ```

2. Запустить dev-сервер:
   ```bash
   npm run dev
   ```
   По умолчанию открывается `http://localhost:5173`.

### Структура и страницы

```
frontend/
├── public/
│   └── logo_v1.png     # Логотип и favicon
├── src/
│   ├── components/     # Компоненты (Navbar, ProtectedRoute, AuthForm)
│   ├── pages/          # Страницы (Home, Login, Register, Info, Balance, Prediction)
│   ├── services/       # API-интерфейсы (auth.js)
│   ├── App.jsx         # Корневой компонент с React Router
│   └── main.jsx        # Точка входа React
├── tailwind.config.js  # Конфигурация TailwindCSS
├── vite.config.js      # Конфигурация Vite
└── package.json        # Зависимости frontend
```

**Главные страницы:**
- **Home (`/`)**: приветствие, логотип, описание проекта. Кнопки «Login» / «Register».
- **Login (`/login`)**: форма входа.
- **Register (`/register`)**: форма регистрации.
- **Info (`/info`)**: профиль пользователя (данные из `auth/me`).
- **Balance (`/balance`)**: текущий баланс, форма пополнения, история транзакций, покупка/продление статуса.
- **Prediction (`/prediction`)**: форма создания прогноза, список исторических прогнозов, получение результатов по ID.

---

## Telegram-бот

### Настройка

1. Настройте `.env` в папке `telegram_bot`:
   ```env
   TELEGRAM_BOT_TOKEN=<Ваш_токен>
   API_URL=http://backend:8000/api/v1
   ```

---

## Nginx-proxy

- Сервис `nginx_proxy` в `docker-compose.yml` отдаёт статические файлы фронтенда из директории `frontend/dist`.
- Все запросы, начинающиеся с `/api/`, проксируются на `backend:8000`.

---

## Docker Compose

В корне проекта есть `docker-compose.yml`, который запускает все сервисы:
- **database**: база данных PostgreSQL.
- **rabbitmq**: брокер RabbitMQ.
- **backend**: FastAPI приложение.
- **frontend**: React приложение (Nginx отдаёт готовую сборку).
- **telegram_bot**: Telegram-бот.
- **nginx_proxy**: Nginx
- **worker**: Масштабируемые воркеры
- 

Пример запуска:
```bash
docker-compose up --build
```

После запуска:
- Фронтенд доступен по `http://localhost`.
- Backend API — `http://localhost/api/v1/...`.
- Бот доступен в Telegram.

---

## Контакты и поддержка

**Проект:** OTF (OpenTaxiForecast)

**Автор:** LuckyAm20  
- GitHub: https://github.com/LuckyAm20/mfdp  
- Email: mr.amix@mail.ru  

---

### Лицензия

Проект распространяется под лицензией MIT.  
Для подробностей см. файл [LICENSE](LICENSE).  