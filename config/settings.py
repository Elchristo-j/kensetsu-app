"""
Django settings for config project.
Updated by Ms.Perfect for Render & Local Development.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================
# セキュリティ設定
# ==========================================

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-nhtj$^$miwt^=x$g8_pmtn0f2!^0$!+2!@7(r98xek2x1sa2n0')
DEBUG = True
ALLOWED_HOSTS = ['*']


# ==========================================
# アプリケーション定義
# ==========================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'jobs',
    'accounts',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ==========================================
# データベース設定
# ==========================================

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600
    )
}


# ==========================================
# 言語・時間設定
# ==========================================

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True


# ==========================================
# 静的ファイル (CSS/JS) 設定
# ==========================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ==========================================
# 画像ファイル (Media) 設定
# ==========================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================
# ログイン・ログアウト設定
# ==========================================

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'


# ==========================================
# メール送信設定（Gmail用）
# ==========================================

# 現在のメール設定を以下のように書き換えてみてください
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465               # 587 から 465 に変更
EMAIL_USE_TLS = False          # True から False に変更
EMAIL_USE_SSL = True           # 新しく True を追加
EMAIL_HOST_USER = 'hiroshi.77dk@gmail.com'
EMAIL_HOST_PASSWORD = 'fjzafkfjetgueblb'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 10             # 少し余裕を持って10秒に

# ★接続待ち時間を5秒に制限（Renderのタイムアウト対策）
EMAIL_TIMEOUT = 5


# ==========================================
# 本番環境セキュリティ（Render）
# ==========================================

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.ngrok-free.dev',
    'http://localhost',
    'http://127.0.0.1',
]

if 'RENDER' in os.environ:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SAMESITE = 'None'