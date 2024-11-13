from pathlib import Path
import os
from django.contrib.messages import constants as messages
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from dotenv import dotenv_values
env_vars = dotenv_values(".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = str(os.getenv('SECRET_KEY'))

DEBUG = env_vars['DEBUG']

DEBUG=True

ALLOWED_HOSTS = ['*']

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
}
# Application definition

INSTALLED_APPS = [

    'celery',
    "rest_framework",
    "rest_framework.authtoken",
    "drf_yasg",
    'whitenoise.runserver_nostatic',
    'ckeditor',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'users',
    'product',
    'orders',
    'cart',
    'payment',
    'app_common',
    'wishlist',
    'blog',
    'product_variations',
    'coupons'

]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

     "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = 'niwa_agro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.cart_views.user_cart_views.cart_count_processor',
                'app_common.app_common_views.app_common_views.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'niwa_agro.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_vars["DB_NAME"],
        "USER": env_vars["DB_USER"],
        "PASSWORD": env_vars["DB_PASSWORD"],
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}



# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'


PRODUCTION = str(os.getenv('PRODUCTION'))


STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage" 
STATIC_ROOT = os.path.join(BASE_DIR , 'staticfiles')

SITE_URL = 'http://127.0.0.1:8000'


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MESSAGE_TAGS = {
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.ERROR: 'alert-danger',
}




GST_CHARGE = 0.015
DELIVARY_CHARGE_PER_BAG = 50
DELIVARY_FREE_ORDER_AMOUNT = 750




# Emails

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'noreplyf577@gmail.com'
EMAIL_HOST_PASSWORD = 'lxlb pidz ggno lujv'
DEFAULT_FROM_EMAIL = 'your_email@gmail.com'




RAZORPAY_API_KEY = 'rzp_test_kugvSxFkbuJKAI'
RAZORPAY_API_SECRET = 'kI8OEz5kKfMRBcnTmQ14GDHy'
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

#delhivery
DELHIVERY_API_KEY  = '96eb7a5d79f87f5139d18917789627672163a2c3'
DELHIVERY_API_URL = 'https://api.delhivery.com'



LOGIN_REDIRECT_URL = 'cart:checkout'  # Redirect to checkout after login
LOGIN_URL = 'users:login'  # Ensure login URL is set


