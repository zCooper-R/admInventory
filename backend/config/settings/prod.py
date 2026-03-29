from .base import *  # noqa: F401, F403
import environ

env = environ.Env()

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# WhiteNoise serves static files directly from Gunicorn (no Nginx required for static)
WHITENOISE_MAX_AGE = 31536000  # 1 year browser cache for hashed assets
