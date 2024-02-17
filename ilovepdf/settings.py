import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-okkh^d15@u5+lhc=tbb_^uxlb^f&9b)fe$&agsi!dmei@o2r@_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost','127.0.0.1','127.0.0.1:8000','127.0.0.1:8000/blog/']

SITE_ID = 1

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
    'blog.apps.BlogConfig',
    'tools.apps.ToolsConfig',
    'taggit',
    'ckeditor',
    'rosetta',
    'parler',


]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ilovepdf.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'ilovepdf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('af', _('Afrikaans')),
    ('ar', _('Arabic')),
    ('az', _('Azerbaijani')),
    ('bg', _('Bulgarian')),
    ('be', _('Belarusian')),
    ('bn', _('Bengali')),
    ('br', _('Breton')),
    ('bs', _('Bosnian')),
    ('ca', _('Catalan')),
    ('cs', _('Czech')),
    ('cy', _('Welsh')),
    ('da', _('Danish')),
    ('de', _('German')),
    ('el', _('Greek')),
    ('en', _('English')),
    ('en-gb', _('British English')),
    ('eo', _('Esperanto')),
    ('es', _('Spanish')),
    ('es-ar', _('Argentinian Spanish')),
    ('es-mx', _('Mexican Spanish')),
    ('es-ni', _('Nicaraguan Spanish')),
    ('es-ve', _('Venezuelan Spanish')),
    ('et', _('Estonian')),
    ('eu', _('Basque')),
    ('fa', _('Persian')),
    ('fi', _('Finnish')),
    ('fr', _('French')),
    ('fy-nl', _('Frisian')),
    ('ga', _('Irish')),
    ('gl', _('Galician')),
    ('he', _('Hebrew')),
    ('hi', _('Hindi')),
    ('hr', _('Croatian')),
    ('hu', _('Hungarian')),
    ('ia', _('Interlingua')),
    ('id', _('Indonesian')),
    ('is', _('Icelandic')),
    ('it', _('Italian')),
    ('ja', _('Japanese')),
    ('ka', _('Georgian')),
    ('kk', _('Kazakh')),
    ('km', _('Khmer')),
    ('kn', _('Kannada')),
    ('ko', _('Korean')),
    ('lb', _('Luxembourgish')),
    ('lt', _('Lithuanian')),
    ('lv', _('Latvian')),
    ('mk', _('Macedonian')),
    ('ml', _('Malayalam')),
    ('mn', _('Mongolian')),
    ('nb', _('Norwegian Bokmal')),
    ('ne', _('Nepali')),
    ('nl', _('Dutch')),
    ('nn', _('Norwegian Nynorsk')),
    ('pa', _('Punjabi')),
    ('pl', _('Polish')),
    ('pt', _('Portuguese')),
    ('pt-br', _('Brazilian Portuguese')),
    ('ro', _('Romanian')),
    ('ru', _('Russian')),
    ('sk', _('Slovak')),
    ('sl', _('Slovenian')),
    ('sq', _('Albanian')),
    ('sr', _('Serbian')),
    ('sr-latn', _('Serbian Latin')),
    ('sv', _('Swedish')),
    ('sw', _('Swahili')),
    ('ta', _('Tamil')),
    ('te', _('Telugu')),
    ('th', _('Thai')),
    ('tr', _('Turkish')),
    ('tt', _('Tatar')),
    ('udm', _('Udmurt')),
    ('uk', _('Ukrainian')),
    ('ur', _('Urdu')),
    ('vi', _('Vietnamese')),
    ('zh-cn', _('Simplified Chinese')),
    ('zh-tw', _('Traditional Chinese')),
]

PARLER_DEFAULT_LANGUAGE_CODE = 'en'

PARLER_LANGUAGES = {
    1 : (
        {'code' : 'af'},
        {'code' : 'ar'},
        {'code' : 'az'},
        {'code' : 'bg'},
        {'code' : 'be'},
        {'code' : 'bn'},
        {'code' : 'br'},
        {'code' : 'bs'},
        {'code' : 'ca'},
        {'code' : 'cs'},
        {'code' : 'cy'},
        {'code' : 'da'},
        {'code' : 'el'},
        {'code' : 'en'},
        {'code' : 'en-gb'},
        {'code' : 'eo'},
        {'code' : 'es'},
        {'code' : 'es-ar'},
        {'code' : 'es-mx'},
        {'code' : 'es-ni'},
        {'code' : 'es-ve'},
        {'code' : 'et'},
        {'code' : 'eu'},
        {'code' : 'fa'},
        {'code' : 'fi'},
        {'code' : 'fr'},
        {'code' : 'fy-nl'},
        {'code' : 'ga'},
        {'code' : 'gl'},
        {'code' : 'he'},
        {'code' : 'hi'},
        {'code' : 'hr'},
        {'code' : 'hu'},
        {'code' : 'ia'},
        {'code' : 'id'},
        {'code' : 'is'},
        {'code' : 'it'},
        {'code' : 'ja'},
        {'code' : 'ka'},
        {'code' : 'kk'},
        {'code' : 'km'},
        {'code' : 'kn'},
        {'code' : 'ko'},
        {'code' : 'lb'},
        {'code' : 'lt'},
        {'code' : 'lv'},
        {'code' : 'mk'},
        {'code' : 'ml'},
        {'code' : 'mn'},
        {'code' : 'nb'},
        {'code' : 'ne'},
        {'code' : 'nl'},
        {'code' : 'nn'},
        {'code' : 'pa'},
        {'code' : 'pl'},
        {'code' : 'pt'},
        {'code' : 'pt-br'},
        {'code' : 'ro'},
        {'code' : 'ru'},
        {'code' : 'sk'},
        {'code' : 'sl'},
        {'code' : 'sq'},
        {'code' : 'sr'},
        {'code' : 'sr-latn'},
        {'code' : 'sv'},
        {'code' : 'sw'},
        {'code' : 'ta'},
        {'code' : 'te'},
        {'code' : 'th'},
        {'code' : 'tr'},
        {'code' : 'tt'},
        {'code' : 'udm'},
        {'code' : 'uk'},
        {'code' : 'ur'},
        {'code' : 'vi'},
        {'code' : 'zh-cn'},
        {'code' : 'zh-tw'},
    ),
    'default':{
        'fallbacks': 'en',
        'hide_untranslated': False,
    }
}



TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
# Add these new lines
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
# STATICFILES_DIRS = [BASE_DIR / 'static'] # new

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

# APPEND_SLASH=False
# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'awesome_ckeditor': {
        # 'toolbar': 'Basic',
        'toolbar': 'full',
        'height': 300,
        'width': 900,
    },
}

