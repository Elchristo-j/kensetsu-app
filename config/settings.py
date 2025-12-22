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

# 本番(Render)では環境変数から読み込み、無ければデフォルト値を使います
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-nhtj$^$miwt^=x$g8_pmtn0f2!^0$!+2!@7(r98xek2x1sa2n0')

# デバッグモード（本番でFalseにするのが理想ですが、開発中はTrueでOK）
DEBUG = True

# どこからでもアクセス許可（Renderのドメイン制限で弾かれないように）
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
    'jobs',      # 自作アプリ
    'accounts',  # 自作アプリ
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Renderで静的ファイルを扱うために必須
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
# データベース設定 (最重要)
# ==========================================

# Renderの環境変数にDATABASE_URLがあればPostgreSQLを使い、
# なければ手元のSQLiteを使う、賢い自動切り替え設定です。
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600
    )
}


# ==========================================
# パスワードバリデーション
# ==========================================

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

# WhiteNoiseを使って、Render上で効率よくファイルを配信する設定
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
# その他（メール・CSRF・iPhone対策）
# ==========================================

# 開発用メール設定（コンソールに表示）
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Renderやngrokはhttpsで通信するため、Djangoに「今はhttpsだよ」と教える設定
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF検証で信頼するURLリスト
# RenderのURLと、ローカル開発用のURLを許可します
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',  # Renderの全サブドメインを許可
    'https://*.ngrok-free.dev', # ngrokも許可
    'http://localhost',
    'http://127.0.0.1',
]

# iPhone(Safari)でのログイン不具合を防ぐ設定
# 本番環境(Render)でのみCookieのセキュリティを強化し、ローカルでは緩める
if 'RENDER' in os.environ:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SAMESITE = 'None'