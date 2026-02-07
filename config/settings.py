"""
Django settings for config project.
Updated for SSL Email Support & Render Stability.
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
    # ... 拡張ライブラリ ...
    'cloudinary_storage',
    'cloudinary',
    # ... 自作アプリ ...
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
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # ★修正: 存在しないファイルを読み込まないよう削除しました
                # 'jobs.context_processors.pending_verification_count', 
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

#STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



# ==========================================
# 画像ファイル (Media) 設定 (Cloudinary)
# ==========================================

# 1. Cloudinaryの設定
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

# 2. 画像の保存先をCloudinaryに変更
#DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================
# ログイン・ログアウト設定
# ==========================================

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'


# ==========================================
# メール送信設定
# ==========================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'hiroshi.77dk@gmail.com'
EMAIL_HOST_PASSWORD = 'fjzafkfjetgueblb'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 10


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

# ==========================================
# Stripe設定
# ==========================================

STRIPE_PUBLISHABLE_KEY = os.environ.get(
    'STRIPE_PUBLISHABLE_KEY', 
    'pk_test_51R4us3DADu8qJkAGldBZjQUaJGvQuxfXRlGpDcVjrTrbrpyfDIibFKymQmHYccC9XBIBd7zdZfw0ekDPV92R3hZX009p1pDn4g'
)

STRIPE_SECRET_KEY = os.environ.get(
    'STRIPE_SECRET_KEY', 
    'sk_test_51R4us3DADu8qJkAGUGryys0UPY8HNJCwtIl40CMS3H80S2I5MciV8RmUUzYnxgBZvWeK9a7bkWGFhUzISJUeVZrk000PyPj0UO'
)

STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

STRIPE_PRICE_IDS = {
    'silver': 'price_1SoEIGDADu8qJkAGq7P5azgd',
    'gold': 'price_1SoEJMDADu8qJkAG1kNZbtM9',
    'platinum': 'price_1SoEJyDADu8qJkAGapSq3ize',
}

# ==========================================
# ストレージ設定 (Django 5.0+ 対応版)
# ==========================================
STORAGES = {
    # 静的ファイル (CSS/JS) -> WhiteNoiseを使う
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    # メディアファイル (画像) -> Cloudinaryを使う
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
}