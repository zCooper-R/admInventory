"""Constants for the target Excel import format."""
from __future__ import annotations

DATA_SHEET_NAME = "Таблица данных"

COL_ORGANIZATION = "Наименование юридического лица"
COL_OS = "Наименование ОС"
COL_INVENTORY = "Инв. №"
COL_CPU = "Наименование процессора"
COL_CPU_FREQ = "Тактовая частота"
COL_RAM = "Оперативная память"
COL_STORAGE_TYPE = "Тип диска"
COL_STORAGE_SIZE = "Емкость диска"
COL_BROWSER = "Браузер которым пользуетесь"
COL_ACCOUNTS = "Наличие личного аккаунта Google, аккаунта Apple или аккаунта Microsoft"
COL_INTERNET_SPEED = "Скорость интернета"
COL_PROVIDER = "Провайдер"
COL_ATTESTED = "Аттестованный компьютер"
COL_USES_TEXT = "Работа с текстом"
COL_USES_IMAGES = "Работа с картинками, фотографиями"
COL_USES_PRESENTATIONS = "Создание презентаций"
COL_USES_AUDIO = "Работа с аудио"
COL_USES_VIDEO = "Работа с видео"
COL_EMPLOYEE = "Фамилия, инициалы сотрудника"
COL_POSITION = "Должность"

REQUIRED_COLUMNS = {
    COL_ORGANIZATION,
    COL_INVENTORY,
    COL_OS,
    COL_RAM,
    COL_STORAGE_TYPE,
}

OPTIONAL_COLUMNS = {
    COL_CPU,
    COL_CPU_FREQ,
    COL_STORAGE_SIZE,
    COL_BROWSER,
    COL_ACCOUNTS,
    COL_INTERNET_SPEED,
    COL_PROVIDER,
    COL_ATTESTED,
    COL_USES_TEXT,
    COL_USES_IMAGES,
    COL_USES_PRESENTATIONS,
    COL_USES_AUDIO,
    COL_USES_VIDEO,
    COL_EMPLOYEE,
    COL_POSITION,
}

ALLOWED_STORAGE_TYPES = {"SSD", "HDD"}

ALLOWED_INTERNET_SPEEDS = {
    "До 5 Мб/с",
    "От 5 до 50 Мб/с",
    "От 50 до 100 Мб/с",
    "Свыше 100 Мб/с",
}
