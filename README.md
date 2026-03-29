# admInventory

> **Система инвентаризации IT-оборудования** — веб-приложение для учёта компьютеров
> в организациях с несколькими филиалами. Планирование замены техники, Excel-импорт,
> автоматический агент сбора данных.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green?logo=django)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange)](CHANGELOG.md)

---

## Содержание

1. [Возможности](#возможности)
2. [Стек технологий](#стек-технологий)
3. [Архитектура](#архитектура)
4. [Быстрый старт (Docker)](#быстрый-старт-docker)
5. [Локальная разработка](#локальная-разработка)
6. [Продакшн-деплой](#продакшн-деплой)
7. [API](#api)
8. [Агент сбора данных](#агент-сбора-данных)
9. [Тесты](#тесты)
10. [Переменные окружения](#переменные-окружения)
11. [Roadmap](#roadmap)

---

## Возможности

| Функция | Описание |
|---------|----------|
| 📊 **Дашборд** | KPI-карточки, диаграммы Chart.js, последние изменения, алерт по замене |
| 💻 **PC инвентарь** | Список с фильтрами, сортировкой, пагинацией — без перезагрузки (HTMX) |
| ✏️ **CRUD** | Создание / редактирование / удаление через модальные окна |
| 📥 **Excel импорт** | Загрузка файла с логированием ошибок, шаблон для заполнения |
| 📤 **Excel экспорт** | Выгрузка всех ПК в `.xlsx` |
| 💰 **Бюджет замены** | Автоматическая оценка ПК по RAM, возрасту, статусу; расчёт суммы |
| 🤖 **Агент** | PowerShell / Python скрипт собирает данные с ПК и отправляет на сервер |
| ⚙️ **Настройки** | Веб-страница конфигурации — без пересборки проекта |
| 🌙 **Тёмная тема** | Переключатель с сохранением в `localStorage` |
| 📱 **Адаптивность** | Полная поддержка смартфонов и планшетов |
| 🔐 **Роли** | `admin` / `manager` (видит только свой филиал) / `user` |

---

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.12, Django 5.0 |
| API | Django REST Framework 3.15 |
| База данных | PostgreSQL 16 |
| Frontend | Django Templates, Bootstrap 5.3, HTMX 1.9, Chart.js |
| Импорт/Экспорт | pandas, openpyxl |
| Кеш | Django cache (LocMem / Redis) |
| Prod-сервер | Gunicorn + WhiteNoise |
| Контейнеры | Docker, Docker Compose |
| Тесты | pytest, pytest-django, factory-boy |
| CI | GitHub Actions |
| Линтеры | black, isort, flake8 |

---

## Архитектура

```
admInventory/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py       # общие настройки
│   │   │   ├── dev.py        # разработка
│   │   │   └── prod.py       # продакшн
│   │   ├── urls.py           # маршруты
│   │   ├── api_router.py     # DRF router
│   │   └── version.py        # версия приложения
│   ├── apps/
│   │   ├── users/            # кастомная модель User + роли
│   │   ├── locations/        # Organization → Location
│   │   ├── inventory/        # Device, SystemSettings, views/, services/
│   │   └── import_export/    # ImportLog, pandas-сервис
│   ├── templates/            # Django-шаблоны (Bootstrap 5 + HTMX)
│   ├── static/               # CSS (custom properties, dark mode) + JS
│   ├── tests/                # pytest-тесты
│   └── fixtures/             # демо-данные JSON
├── docker/
│   ├── entrypoint.sh         # dev (runserver)
│   └── entrypoint.prod.sh    # prod (gunicorn)
├── scripts/
│   ├── agent.ps1             # PowerShell агент
│   ├── agent.py              # Python агент
│   └── install_agent.bat     # установщик планировщика
├── docker-compose.yml        # dev
├── docker-compose.prod.yml   # production
├── Dockerfile
├── requirements.txt
├── .pre-commit-config.yaml
└── CHANGELOG.md
```

### Модели данных

```
Organization ──< Location ──< Device
                     │
               User (manager)
```

---

## Быстрый старт (Docker)

### Требования

- Docker Desktop 4+
- Git

### Запуск

```bash
git clone https://github.com/zCooper-R/admInventory.git
cd admInventory

# Скопировать и настроить переменные окружения
cp .env.example .env

# Запустить (первый раз ~2 минуты — загрузка образов)
docker compose up --build

# Приложение доступно: http://localhost:8000
# Логин по умолчанию создаётся командой:
docker compose exec web python manage.py createsuperuser
```

Демо-данные создаются автоматически при первом запуске.

**Demo-аккаунты** (создаются командой `create_demo_data`):

| Логин | Пароль | Роль | Доступ |
|-------|--------|------|--------|
| *(superuser)* | заданный при createsuperuser | admin | всё |
| `manager_technoprom` | `demo1234` | manager | ООО «ТехноПром» |
| `manager_school` | `demo1234` | manager | МОУ «Школа №12» |
| `manager_clinic` | `demo1234` | manager | ГБУЗ «Поликлиника №5» |

---

## Локальная разработка

```bash
# 1. Клонировать проект
git clone https://github.com/zCooper-R/admInventory.git
cd admInventory

# 2. Виртуальное окружение
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# 3. Зависимости
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Pre-commit хуки
pre-commit install

# 5. База данных (нужен PostgreSQL или Docker)
docker compose up db -d

# 6. Запуск
cd backend
python manage.py migrate
python manage.py create_demo_data
python manage.py runserver
```

---

## Продакшн-деплой

```bash
# Скопировать и заполнить продакшн-переменные
cp .env.example .env
# Отредактировать .env: SECRET_KEY, ALLOWED_HOSTS, POSTGRES_*, ...

docker compose -f docker-compose.prod.yml up --build -d
```

Продакшн-профиль использует:
- Gunicorn с 4 воркерами
- `DEBUG=False`
- WhiteNoise для статики
- `ManifestStaticFilesStorage` (хэшированные имена файлов)

---

## API

Базовый URL: `http://localhost:8000/api/v1/`

Аутентификация: сессия Django (Bearer-токен в разработке).

### Версия

```http
GET /api/version/
```
```json
{
  "app": "admInventory",
  "version": "0.1.0",
  "released": "2026-03-29",
  "status": "ok"
}
```

### Устройства

```http
GET  /api/v1/devices/              # список (пагинация, фильтры, поиск)
POST /api/v1/devices/              # создать
GET  /api/v1/devices/{id}/         # детали
PUT  /api/v1/devices/{id}/         # обновить
DEL  /api/v1/devices/{id}/         # удалить
POST /api/v1/devices/sync/         # агент: upsert по inventory_number
```

Параметры фильтрации: `?status=active`, `?device_type=PC`, `?location=1`  
Поиск: `?search=i5-12400`  
Сортировка: `?ordering=-updated_at`

#### Агент sync (пример)

```bash
curl -X POST http://localhost:8000/api/v1/devices/sync/ \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: YOUR_AGENT_API_KEY" \
  -d '{
    "inventory_number": "PC-OFFICE-01",
    "name": "Офисный ПК 01",
    "cpu": "Intel Core i5-12400",
    "ram": 16,
    "os": "Windows 11 Pro",
    "storage_type": "SSD",
    "storage_size": 512
  }'
```

---

## Агент сбора данных

Автоматически собирает характеристики ПК через WMI (Windows) и отправляет
на сервер. Не требует установки Python на целевых машинах.

```
scripts/
├── agent.ps1          PowerShell — рекомендуется для Windows
├── agent.py           Python — кросс-платформенный вариант
├── install_agent.bat  Установка в Планировщик задач (один клик)
└── README.md          Подробная инструкция для администраторов
```

**Установка на рабочем месте:**

```bat
:: Запустить от имени администратора
install_agent.bat
```

Скрипт создаёт задание в Планировщике, которое запускается при входе пользователя.

---

## Тесты

```bash
cd backend
pytest                        # все тесты
pytest -v                     # подробный вывод
pytest --cov=apps --cov-report=html   # с покрытием
pytest tests/test_settings.py # конкретный файл
```

Покрытие тестами:

| Модуль | Тесты |
|--------|-------|
| `DeviceViewSet` (API) | CRUD, фильтрация, поиск |
| `OrganizationViewSet`, `LocationViewSet` | список, создание |
| Веб-вью (дашборд, PC list, CRUD) | GET/POST, HTMX |
| Excel импорт / экспорт | загрузка файла, экспорт |
| `SystemSettings` | синглтон, кеш, инвалидация |
| Budget cache | populate, invalidate, сигналы |
| Critical badge | подсчёт, OOB-элементы |
| Import template | Content-Type, xlsx, колонки |

---

## Переменные окружения

Скопировать `.env.example` → `.env` и заполнить:

```dotenv
# Django
SECRET_KEY=your-super-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.dev

# PostgreSQL
POSTGRES_DB=inventory
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Агент
AGENT_API_KEY=change-me-to-random-string

# Продакшн
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Roadmap

### v0.2.0 — Ноутбуки и принтеры
- [ ] Отдельный список и дашборд для ноутбуков
- [ ] Карточки принтеров с учётом картриджей

### v0.3.0 — Отчёты и уведомления
- [ ] PDF-отчёт по замене техники
- [ ] Email-уведомления при критическом статусе
- [ ] Telegram-бот для быстрого поиска

### v0.4.0 — QR-коды и инвентаризация
- [ ] Генерация QR-кодов для каждого устройства
- [ ] Мобильное сканирование через камеру

### v1.0.0 — Production
- [ ] Redis для кеширования
- [ ] Celery для фоновых задач
- [ ] SSO / LDAP авторизация
- [ ] Многоязычность (ru / en)

---

## Лицензия

MIT © 2026 **Литвин Олег Олегович** — [qucooper@yandex.ru](mailto:qucooper@yandex.ru)
