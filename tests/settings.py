from pathlib import Path

from tests.jinja2 import environment

SITE_ID = 1

DATABASE_ENGINE = 'sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PROJECT_ROOT = Path(__file__).parent

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'sass_processor',
    'tests',
]

TEMPLATES = [
    {
        'NAME': 'django',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
    {
        'NAME': 'jinja2',
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'tests.jinja2.environment'
        },
    }
]
COMPRESS_JINJA2_GET_ENVIRONMENT = environment

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
)

USE_TZ = True

SECRET_KEY = 'secret'

STATIC_URL = '/static/'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]

STATICFILES_DIRS = [
    PROJECT_ROOT / 'static',
]

STATIC_ROOT = PROJECT_ROOT / 'tmpstatic'

SASS_PROCESSOR_ENABLED = True

SASS_PROCESSOR_CUSTOM_FUNCTIONS = {
    'get-width': 'tests.get_width',
    'get-margins': 'tests.get_margins',
    'get-plain-color': 'tests.get_plain_color',
}

SASS_BLUE_COLOR = '#0000ff'
