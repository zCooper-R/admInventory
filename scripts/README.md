# IT Inventory — Agent Scripts

Автоматический сбор данных об оборудовании ПК и отправка в систему инвентаризации.

---

## Как это работает

```
ПК сотрудника (Windows/Linux/macOS)
    ↓  запуск по расписанию (раз в неделю)
agent.ps1 / agent.py
    ↓  собирает: CPU, RAM, диск, ОС, серийный номер, hostname
    ↓  POST /api/v1/devices/sync/   (с заголовком X-Api-Key)
Django API
    ↓  update_or_create по inventory_number = "AUTO-<hostname>"
База данных — данные всегда актуальны ✓
```

---

## Файлы

| Файл | Описание |
|---|---|
| `agent.ps1` | PowerShell агент (Windows, рекомендуется) |
| `agent.py` | Python агент (Windows / Linux / macOS) |
| `install_agent.bat` | Установщик: запускается один раз с правами Администратора |

---

## Быстрый старт (1 ПК)

1. Откройте `install_agent.bat` в текстовом редакторе
2. Замените `YOUR-SERVER-ADDRESS` на адрес вашего сервера
3. Замените `change-me-before-production` на значение `AGENT_API_KEY` из `.env`
4. Запустите от имени Администратора — готово!

---

## Массовая установка без обхода каждого ПК

### Вариант A: через сетевую папку (самый простой)

1. Положите скрипты в сетевую папку: `\\SERVER\IT_Tools\`
2. Разошлите пользователям ссылку с инструкцией "запустить 1 раз как админ"
3. Или попросите любого сотрудника с правами локального администратора

**Плюс**: не нужна инфраструктура AD, работает в любой сети.

### Вариант Б: через групповые политики (GPO) ← рекомендуется для AD

Если в организации есть Active Directory, IT-администратор настраивает один раз:

```
Конфигурация компьютера
  → Политики
    → Конфигурация Windows
      → Скрипты (запуск/завершение)
        → Запуск
          → Добавить: \\DC\SYSVOL\scripts\agent.ps1
```

Или через GPO Scheduled Tasks:
```
Конфигурация компьютера
  → Настройки
    → Параметры панели управления
      → Назначенные задания
        → Новая задача: agent.ps1 каждый понедельник
```

**Плюс**: полностью автоматически, нет ничего делать на ПК пользователей.

### Вариант В: через Intune / MDM (современные организации)

Создайте PowerShell Script в Microsoft Intune:
- Скрипт: содержимое `agent.ps1` (с уже подставленными URL и ключом)
- Запуск от: System
- Частота: еженедельно (через Detection Script)

### Вариант Г: Python агент (без PowerShell)

Для Linux/macOS или если PowerShell недоступен:

```bash
# Установка зависимостей
pip install requests psutil

# Настройка
export INVENTORY_API_URL="http://your-server/api/v1/devices/sync/"
export INVENTORY_API_KEY="your-api-key"
export INVENTORY_LOCATION_ID="3"   # ID площадки

# Запуск
python agent.py

# Добавить в crontab (раз в неделю по понедельникам):
# 0 9 * * 1 INVENTORY_API_URL="..." INVENTORY_API_KEY="..." python /opt/it_agent/agent.py
```

---

## Настройка сервера

### .env файл

Добавьте ключ в `.env`:
```
AGENT_API_KEY=замените-на-длинный-случайный-ключ
```

Генерация ключа:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Привязка к площадке

Агент может указать, к какой площадке относится ПК:

**PowerShell** (`agent.ps1`):
```powershell
$LOCATION_ID = 5   # ID из /admin/locations/location/
```

**Python** (`agent.py`):
```bash
export INVENTORY_LOCATION_ID=5
```

Если не указан — ПК создаётся без площадки (можно назначить позже в веб-интерфейсе).

---

## API endpoint

```
POST /api/v1/devices/sync/
Headers: X-Api-Key: <ваш-ключ>
         Content-Type: application/json

Body:
{
  "inventory_number": "AUTO-PC-BUHGALTER",  // обязательно
  "name":             "PC-BUHGALTER",
  "hostname":         "PC-BUHGALTER",
  "cpu":              "Intel Core i5-12400",
  "ram":              16,
  "os":               "Windows 11 Pro 23H2",
  "storage_type":     "SSD",
  "storage_size":     512,
  "serial_number":    "SN1234567",
  "location_id":      5,
  "purchase_date":    "2022-03-15"   // только при первом создании
}

Ответ 201 (создан) или 200 (обновлён):
{
  "created": true,
  "device": { "id": 42, "name": "PC-BUHGALTER", ... }
}
```
