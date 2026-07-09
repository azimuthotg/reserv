from .settings import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'preview_db.sqlite3',
    }
}
DEBUG = True
ALLOWED_HOSTS = ['*']
