import os
from pathlib import Path

from django.utils.translation import gettext_noop
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS: list[str] = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "phonenumber_field",
    # "multiselectfield",
    # "django_countries",
    "bootstrapform",
    # "captcha",
    "access",
    "connection",
    "credit",
    "medical",
    "payment",
    "planner",
    "renovation",
    "trip",
    "user",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "memento.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
            os.path.join(BASE_DIR, "templates", "email_templates"),
            os.path.join(BASE_DIR, "templates", "registration"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "memento.wsgi.application"

# Database

DATABASES = {
    # "default": {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": BASE_DIR / "db.sqlite3",
    # }
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": "5432",
    }
}

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization

# >> change to polish language <<
# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = "pl"
LANGUAGES = [("pl", gettext_noop("Polish")), ("en-gb", gettext_noop("British English"))]

# TIME_ZONE = "UTC"
TIME_ZONE = "Europe/Warsaw"

USE_I18N = True
USE_TZ = True

# Formatting

FORMAT_MODULE_PATH = [
    "formats",
]
USE_THOUSAND_SEPARATOR = True

# Email

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

# Static files (CSS, JavaScript, Images)

STATIC_URL = "/static/"
MEDIA_URL = "/uploads/"  #'/images/'

STATICFILES_DIRS = [
    (os.path.join(BASE_DIR, "static")),
]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR, "static", "uploads")  #'static/images'
TEST_ROOT = os.path.join(BASE_DIR, "static", "test")
TEMPORARY_ROOT = os.path.join(BASE_DIR, "static", "temporary")
LOGGER_ROOT = os.path.join(BASE_DIR, "static", "logs")

MAX_FILE_SIZE = 2621440
MAX_UPLOADED_FILES = 5

# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] [level: %(levelname)s]❗[logger: %(name)s]: %(message)s",
        },
        "simple": {
            "format": "{asctime} - {levelname}: ℹ️ {message}",
            "style": "{",
        },
        "test": {
            "format": "[%(asctime)s] [level: %(levelname)s] [logger: %(name)s]: 📉️ %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "filters": ["require_debug_true"],
            "formatter": "simple",
        },
        "file_memento": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "static", "logs", "memento.txt"),
            "formatter": "verbose",
            "encoding": "utf-8",
            "mode": "a+",
        },
        "file_info": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "static", "logs", "info.txt"),
            "formatter": "simple",
            "encoding": "utf-8",
            "mode": "a+",
        },
        "file_test": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "static", "logs", "test.txt"),
            "formatter": "test",
            "encoding": "utf-8",
            "mode": "a+",
        },
    },
    "loggers": {
        "memento": {
            "handlers": ["console", "file_memento"],
            "level": "INFO",
        },
        "all": {
            "handlers": ["file_info", "console"],
            "level": "INFO",
        },
        "test": {
            "handlers": ["console", "file_test"],
            "level": "INFO",
        },
        "root": {
            "handlers": ["console", "file_memento"],
            "level": "INFO",
        },
    }
}

# User model

AUTH_USER_MODEL = "user.User"

# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# PHONENUMBER_DEFAULT_REGION = 'PL'

RECAPTCHA_PUBLIC_KEY = os.environ.get("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = os.environ.get("RECAPTCHA_PRIVATE_KEY")
RECAPTCHA_PROXY = {
    "localhost": "http://127.0.0.1:8000",
}  # zmienić po migracji
GOOGLE_RECAPTCHA_SITE_KEY = os.environ.get("GOOGLE_RECAPTCHA_SITE_KEY") # usunąć na produkcji!
GOOGLE_RECAPTCHA_SECRET_KEY = os.environ.get("GOOGLE_RECAPTCHA_SECRET_KEY") # usunąć na produkcji!
SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]  # usunąć na produkcji!
