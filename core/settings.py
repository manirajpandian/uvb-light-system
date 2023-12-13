# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

import os
from decouple import config
from unipath import Path
from django.db.models import BigAutoField
import locale
from django.utils import timezone


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).parent
CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = 'http://127.0.0.1:8000/'
# BASE_URL = 'http://52.192.209.112/'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='S#perS3crEt_1122')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default="maniraj@mosaique.link")
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default="ihxonvfuwxuuclmh")
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# load production server from .env
ALLOWED_HOSTS = ['localhost', '127.0.0.1', config('SERVER', default='127.0.0.1')]
# ALLOWED_HOSTS = ['localhost', '52.192.209.112']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.authentication.apps.AuthenticationConfig',
    'apps.home',
]
# this for custom login using profile object
AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.ProfileBackend',
    'django.contrib.auth.backends.ModelBackend', 
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
LOGIN_REDIRECT_URL = "home"  # Route defined in home/urls.py
LOGOUT_REDIRECT_URL = "home"  # Route defined in home/urls.py
TEMPLATE_DIR = os.path.join(CORE_DIR, "apps/templates")  # ROOT dir for templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
          
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database 
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql', 
        'NAME': 'postgres_16',
        'USER': 'postgres',
        'PASSWORD': 'root',
        'HOST': 'localhost',  # Replace with your PostgreSQL server's address if necessary
        'PORT': '5432',          # Leave empty to use the default PostgreSQL port (usually 5432)
    }
}

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_L10N = True


#############################################################

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(CORE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# user profile image static files.

STATICFILES_DIRS = (
    os.path.join(CORE_DIR, 'apps/static'),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

#############################################################
#############################################################
