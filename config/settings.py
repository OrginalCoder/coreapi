import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-coreapi-dev-key-local-38a4bc89f920'
)

DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS_RAW = os.getenv(
    'DJANGO_ALLOWED_HOSTS',
    '127.0.0.1,localhost,testserver,.pythonanywhere.com,coreapi.pythonanywhere.com'
)
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_RAW.split(',') if host.strip()]
if '.pythonanywhere.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.pythonanywhere.com')
if 'coreapi.pythonanywhere.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('coreapi.pythonanywhere.com')

CSRF_TRUSTED_ORIGINS_RAW = os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '')
if CSRF_TRUSTED_ORIGINS_RAW:
    CSRF_TRUSTED_ORIGINS = [
        origin.strip() for origin in CSRF_TRUSTED_ORIGINS_RAW.split(',') if origin.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://coreapi.pythonanywhere.com',
        'https://*.pythonanywhere.com',
        'http://127.0.0.1:8000',
        'http://localhost:8000',
    ]

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AI_RATE_LIMIT = os.getenv('AI_RATE_LIMIT', '20/minute')

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'core.throttling.ChatRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'chat': AI_RATE_LIMIT,
        'anon': AI_RATE_LIMIT,
    },
    'UNAUTHENTICATED_USER': None,
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 262144

SPECTACULAR_SETTINGS = {
    'TITLE': 'CoreAPI — AI Question & Answer API',
    'DESCRIPTION': (
        'CoreAPI — developer-oriented, lightweight AI question-answer API. '
        'Submit a question via POST /api/v1/chat/ and receive a structured JSON response.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SERVERS': [
        {'url': 'https://coreapi.pythonanywhere.com', 'description': 'Production Server'},
        {'url': 'http://127.0.0.1:8000', 'description': 'Development Server'},
    ],
    'TAGS': [
        {'name': 'Chat', 'description': 'AI savol-javob amallari / AI question-answer operations'}
    ],
}

AI_PROVIDER_TYPE = os.getenv('AI_PROVIDER_TYPE', 'groq')
AI_PROVIDER_URL = os.getenv('AI_PROVIDER_URL', 'https://api.groq.com/openai/v1')
AI_PROVIDER_KEYWORD = os.getenv('AI_PROVIDER_KEYWORD', 'text')
AI_PROVIDER_API_KEY = os.getenv('AI_PROVIDER_API_KEY', '') or os.getenv('GROQ_API_KEY', '')
AI_PROVIDER_MODEL = os.getenv('AI_PROVIDER_MODEL', 'openai/gpt-oss-20b')
AI_PROVIDER_TIMEOUT = int(os.getenv('AI_PROVIDER_TIMEOUT', '60'))
