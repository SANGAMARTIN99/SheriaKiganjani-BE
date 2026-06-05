from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"postgres://{config('DB_USER')}:{config('DB_PASSWORD', default='postgres')}@{config('DB_HOST', default='localhost')}:{config('DB_PORT', default='5432')}/{config('DB_NAME')}"
    )
}


CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Google OAuth
GOOGLE_CLIENT_ID = '59314419071-joo08eb568esk2rs1vh2sicd057lv5dd.apps.googleusercontent.com'
