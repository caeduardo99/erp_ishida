"""
Django settings for erp_ishida project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'o^5e=#lcb(lb%v#+2ri$c^ywgj1yabuv4pmhh=o(^-o_#xb4iw'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'erp',
    'sii_seguridad'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'erp_ishida.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'erp_ishida.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'main': {
        'ENGINE': config("ENGINE"),
        'NAME': config("MAIN_DB"),
        'USER': config("USUARIO_DB"),
        'PASSWORD': config("PASSWORD_DB"),
        'HOST': config("SERVER_DB"),
        'OPTIONS': {
            'driver': "ODBC Driver 17 for SQL Server",
        }
    },
    'empresa': {
        'ENGINE': config("ENGINE"),
        'NAME': config("EMPRESA_DB"),
        'USER': config("USUARIO_DB"),
        'PASSWORD': config("PASSWORD_DB"),
        'HOST': config("SERVER_DB"),
        'OPTIONS': {
            'driver': "ODBC Driver 17 for SQL Server",
        }
    },
      'default': {
        'ENGINE': config("ENGINE"),
        'NAME': config("MAIN_DB"),
        'USER': config("USUARIO_DB"),
        'PASSWORD': config("PASSWORD_DB"),
        'HOST': config("SERVER_DB"),
        'OPTIONS': {
            'driver': "ODBC Driver 17 for SQL Server",
        }
    },
    'empresa1': {
        'ENGINE': config("ENGINE"),
        'NAME': config("EMPRESA_DB1"),
        'USER': config("USUARIO_DB"),
        'PASSWORD': config("PASSWORD_DB"),
        'HOST': config("SERVER_DB"),
        'OPTIONS': {
            'driver': "ODBC Driver 17 for SQL Server",
        }
    }
}

DATABASE_ROUTERS = ['erp_ishida.router.DatabaseAppsRouter']
DATABASE_APPS_MAPPING = {
    'sii_seguridad': 'main',
    'erp': 'empresa'

}
# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


AUTHENTICATION_BACKENDS = ['sii_seguridad.autenticacion.backends.IshidaBackend']
AUTH_USER_MODEL = 'sii_seguridad.Usuario'
# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = 'static/'
LOGIN_URL = '/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')