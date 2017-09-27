"""
Django settings for openshift project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import imp

from django.utils.translation import ugettext_lazy as _

ON_OPENSHIFT = False
if 'OPENSHIFT_BUILD_SOURCE' in os.environ:
    ON_OPENSHIFT = True

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

AUTH_USER_MODEL = 'confla.ConflaUser'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    # safe value used for development when DJANGO_SECRET_KEY might not be set
    '9e4@&tw46$l31)zrqe3wi+-slqm(ruvz&se0^%9#6(_w3ui!c0'
)


# SECURITY WARNING: don't run with debug turned on in production!
if ON_OPENSHIFT:
    DEBUG = True
else:
    DEBUG = True

if DEBUG:
    ALLOWED_HOSTS = []
else:
    ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'confla',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# If you want configure the REDISCLOUD
if 'REDISCLOUD_URL' in os.environ and 'REDISCLOUD_PORT' in os.environ and 'REDISCLOUD_PASSWORD' in os.environ:
    redis_server = os.environ['REDISCLOUD_URL']
    redis_port = os.environ['REDISCLOUD_PORT']
    redis_password = os.environ['REDISCLOUD_PASSWORD']
    CACHES = {
        'default' : {
            'BACKEND' : 'redis_cache.RedisCache',
            'LOCATION' : '%s:%d'%(redis_server,int(redis_port)),
            'OPTIONS' : {
                'DB':0,
                'PARSER_CLASS' : 'redis.connection.HiredisParser',
                'PASSWORD' : redis_password,
            }
        }
    }
    MIDDLEWARE_CLASSES = ('django.middleware.cache.UpdateCacheMiddleware',) + MIDDLEWARE_CLASSES + ('django.middleware.cache.FetchFromCacheMiddleware',)


ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
     os.path.join(BASE_DIR,'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
#                "django.core.context_processors.tz",
            ],
        },
    },
]


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
if ON_OPENSHIFT:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['DATABASE_NAME'],
            'USER': os.environ['DATABASE_USER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD'],
            'HOST': os.environ['DATABASE_SERVICE_NAME'],
            'PORT': '5432',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'
LANGUAGES = (
    ('cs', _('Czech')),
    ('en', _('English')),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

TIME_ZONE = 'Europe/Prague'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')
STATIC_URL = '/static/'

if ON_OPENSHIFT:
    MEDIA_ROOT = os.path.join(os.environ.get('OPENSHIFT_DATA_DIR', ''), 'media')
else:
    MEDIA_ROOT = os.path.join(os.path.expanduser('~'), 'media')

MEDIA_URL = '/media/'
LOGIN_URL = '/login/'

# Timeslot difference for schedules
TIMEDELTA = 10 #minutes
