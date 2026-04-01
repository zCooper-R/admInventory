from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR.parent, ".env"))

SECRET_KEY = env("SECRET_KEY")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.users",
    "apps.locations",
    "apps.inventory",
    "apps.import_export",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static in prod without Nginx
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.inventory.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="db"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/"

# Agent sync API key (set AGENT_API_KEY in .env to a strong random string)
AGENT_API_KEY = env("AGENT_API_KEY", default="change-me-before-production")

from django.contrib.messages import constants as message_constants  # noqa: E402
MESSAGE_TAGS = {message_constants.ERROR: "danger"}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

LOG_DIR = Path(env("LOG_DIR", default=str(BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = env("LOG_LEVEL", default="INFO").upper()
DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO").upper()
IMPORT_LOG_LEVEL = env("IMPORT_LOG_LEVEL", default="INFO").upper()
REPLACEMENT_LOG_LEVEL = env("REPLACEMENT_LOG_LEVEL", default="INFO").upper()
WEB_LOG_LEVEL = env("WEB_LOG_LEVEL", default="INFO").upper()
AUDIT_LOG_LEVEL = env("AUDIT_LOG_LEVEL", default="INFO").upper()
SECURITY_LOG_LEVEL = env("SECURITY_LOG_LEVEL", default="WARNING").upper()
DB_LOG_LEVEL = env("DB_LOG_LEVEL", default="WARNING").upper()
ENABLE_DB_LOG = env.bool("ENABLE_DB_LOG", default=False)
LOG_BACKUP_DAYS = env.int("LOG_BACKUP_DAYS", default=14)

_common_handler_kwargs = {
    "class": "logging.handlers.TimedRotatingFileHandler",
    "when": "midnight",
    "interval": 1,
    "backupCount": LOG_BACKUP_DAYS,
    "encoding": "utf-8",
    "delay": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "human": {
            "format": "{asctime} | {levelname:<8} | {name} | {message}",
            "style": "{",
        },
        "detailed": {
            "format": "{asctime} | {levelname:<8} | {name} | pid={process:d} tid={thread:d} | {module}:{lineno} | {message}",
            "style": "{",
        },
        "audit": {
            "format": "{asctime} | AUDIT | {name} | user={user} | action={action} | {message}",
            "style": "{",
        },
    },
    "filters": {
        "audit_context": {
            "()": "apps.inventory.logging.AuditContextFilter",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "human",
        },
        "app_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "app.log"),
            "formatter": "human",
            "level": LOG_LEVEL,
        },
        "errors_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "errors.log"),
            "formatter": "detailed",
            "level": "ERROR",
        },
        "import_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "import.log"),
            "formatter": "detailed",
            "level": IMPORT_LOG_LEVEL,
        },
        "replacement_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "replacement.log"),
            "formatter": "detailed",
            "level": REPLACEMENT_LOG_LEVEL,
        },
        "web_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "web.log"),
            "formatter": "human",
            "level": WEB_LOG_LEVEL,
        },
        "security_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "security.log"),
            "formatter": "detailed",
            "level": SECURITY_LOG_LEVEL,
        },
        "db_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "db.log"),
            "formatter": "detailed",
            "level": DB_LOG_LEVEL,
        },
        "tasks_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "tasks.log"),
            "formatter": "detailed",
            "level": LOG_LEVEL,
        },
        "audit_file": {
            **_common_handler_kwargs,
            "filename": str(LOG_DIR / "audit.log"),
            "formatter": "audit",
            "level": AUDIT_LOG_LEVEL,
            "filters": ["audit_context"],
        },
    },
    "root": {
        "handlers": ["console", "app_file", "errors_file"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "app_file", "errors_file"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["errors_file", "web_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security_file", "errors_file"],
            "level": SECURITY_LOG_LEVEL,
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["db_file"] if ENABLE_DB_LOG else ["console"],
            "level": DB_LOG_LEVEL if ENABLE_DB_LOG else "WARNING",
            "propagate": False,
        },
        "apps.import_export": {
            "handlers": ["import_file", "errors_file"],
            "level": IMPORT_LOG_LEVEL,
            "propagate": False,
        },
        "apps.import_export.excel_import": {
            "handlers": ["import_file", "errors_file"],
            "level": IMPORT_LOG_LEVEL,
            "propagate": False,
        },
        "apps.inventory.services.replacement": {
            "handlers": ["replacement_file", "errors_file"],
            "level": REPLACEMENT_LOG_LEVEL,
            "propagate": False,
        },
        "apps.inventory.views": {
            "handlers": ["web_file", "errors_file"],
            "level": WEB_LOG_LEVEL,
            "propagate": False,
        },
        "apps.inventory.audit": {
            "handlers": ["audit_file", "errors_file"],
            "level": AUDIT_LOG_LEVEL,
            "propagate": False,
        },
        "apps.tasks": {
            "handlers": ["tasks_file", "errors_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
