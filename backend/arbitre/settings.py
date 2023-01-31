"""
Django settings for arbitre project.

Generated by 'django-admin startproject' using Django 4.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import environ

# Reading .env file
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    "SECRET_KEY"
)  # "django-insecure-9p0it%1(1)sv%+s&bv0n@8330j*_)qm76ejwrzg(nea-m=v278"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", env("HOSTNAME", default="")]


# Application definition

INSTALLED_APPS = [
    "api.apps.ApiConfig",
    "corsheaders",
    "django_celery_beat",
    "django.contrib.admin",
    "django.contrib.auth",
    "mozilla_django_oidc",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "drf_yasg",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework_simplejwt",
    "rest_framework",
    "runner.apps.RunnerConfig",
]

# Add 'mozilla_django_oidc' authentication backend
# https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html#changing-how-django-users-are-created

AUTHENTICATION_BACKENDS = (
    "arbitre.oidc.CustomOIDCAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
)

OIDC_RP_CLIENT_ID = env("OIDC_RP_CLIENT_ID", default="arbitre-backend")
OIDC_RP_CLIENT_SECRET = env("OIDC_RP_CLIENT_SECRET", default="")
OIDC_OP_AUTHORIZATION_ENDPOINT = (
    "http://localhost:8080/realms/arbitre/protocol/openid-connect/auth"
)
OIDC_OP_TOKEN_ENDPOINT = (
    "http://localhost:8080/realms/arbitre/protocol/openid-connect/token"
)
OIDC_OP_USER_ENDPOINT = (
    "http://localhost:8080/realms/arbitre/protocol/openid-connect/userinfo"
)

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "https://"
    if env("USE_HTTPS") == "true"
    else "http://" + env("HOSTNAME", default="localhost")
]
CSRF_COOKIE_SECURE = env("USE_HTTPS", default=True)
SESSION_COOKIE_SECURE = env("USE_HTTPS", default=True)

ROOT_URLCONF = "arbitre.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "arbitre.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static-backend/"
STATIC_ROOT = "static/static-backend/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django Rest Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "mozilla_django_oidc.contrib.drf.OIDCAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    )
}

# Simple JWT

SIMPLE_JWT = {
    # "ACCESS_TOKEN_LIFETIME": timedelta(seconds=5),  # (minutes=5),
    # "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    # "ROTATE_REFRESH_TOKENS": False,
    # "BLACKLIST_AFTER_ROTATION": False,
    # "UPDATE_LAST_LOGIN": False,
    # "ALGORITHM": "HS256",
    # "SIGNING_KEY": SECRET_KEY,
    # "VERIFYING_KEY": None,
    # "AUDIENCE": None,
    # "ISSUER": None,
    # "JWK_URL": None,
    # "LEEWAY": 0,
    # "AUTH_HEADER_TYPES": ("Bearer",),
    # "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    # "USER_ID_FIELD": "id",
    # "USER_ID_CLAIM": "user_id",
    # "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    # "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    # "TOKEN_TYPE_CLAIM": "token_type",
    # "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    # "JTI_CLAIM": "jti",
    # "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    # "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    # "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

# Celery Settings
CELERY_BROKER_URL = "amqp://guest:guest@localhost//"
CELERY_RESULT_BACKEND = "rpc://"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
