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
DEBUG = False

ALLOWED_HOSTS = ['*']

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

    'django_check_seo',

    'blog.apps.BlogConfig',
    'tools.apps.ToolsConfig',
    'taggit',
    'ckeditor',
    'rosetta',
    'parler',
    
    'django_celery_beat',
    'django_celery_results',

    'meta',
    'pwa',

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

# STATIC_URL = 'static/'
# Add these new lines
# STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# MEDIA_URL = 'media/'
# MEDIA_ROOT = BASE_DIR / 'media'
STATIC_URL = '/static/'
STATIC_ROOT = '/usr/local/lsws/Example/html/ilovepdf/static'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/usr/local/lsws/Example/html/ilovepdf/media'

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

# for django-celery-beat
CELERY_BROKER_URL = 'redis://localhost:6379'  # Or your preferred broker
CELERY_RESULT_BACKEND = 'redis://localhost:6379' 
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'  # Set to your timezone

CELERY_BEAT_SCHEDULE = {
    'delete_expired_pdfs': {
        'task': 'tools.tasks.delete_old_pdfs',
        'schedule': 3600,  # Runs hourly 
    },
}


META_SITE_PROTOCOL = 'http'
META_SITE_DOMAIN = 'ilovepdfconverteronline.com'
META_SITE_NAME = 'iLovePdfConverterOnline | Online Convert and Edit Tools for PDF Docs Excel Image PowerPoint HTML etc. files in clicks'
META_INCLUDE_KEYWORDS = ['pdf', 'converter', 'convert', 'online']
META_SITE_TYPE = 'website'
# META_DEFAULT_KEYWORDS = 
# META_IMAGE_URL = 
META_USE_OG_PROPERTIES = True
# META_USE_TWITTER_PROPERTIES = 
META_USE_SCHEMAORG_PROPERTIES = True
META_USE_TITLE_TAG = True
# META_USE_SITES = 
# META_OG_NAMESPACES = 
# META_OG_SECURE_URL_ITEMS =        
META_NAMESPACES = {
    'og': 'http://ilovepdfconverteronline/',  # Your preferred Open Graph prefix
    # ... other namespaces if needed ...
}

# The basic config (used by default) is located in django-check-seo/conf/settings.py
DJANGO_CHECK_SEO_SETTINGS = {
    "internal_links": 25,
    "meta_title_length": [15,30],
}



PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, "static/js", "serviceworker.js")
PWA_APP_DEBUG_MODE = True
PWA_APP_NAME = 'ilovepdfconverteronline'
PWA_APP_DESCRIPTION = "ILovePDFconverteronline PWA"
PWA_APP_THEME_COLOR = '#000000'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
	{
		'src': '/static/img/favicon.png',
		# 'sizes': '16x16'
		'sizes': '32x32'
	},
	{
		'src': '/static/img/loveicon.svg',
		# 'sizes': '16x16'
		'sizes': '512x512'
	},
    {
      "src": '/static/img/maskable/maskable_icon.png',
      "sizes": "any",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": '/static/img/maskable/maskable_icon_x48.png',
      "sizes": "48x48",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": '/static/img/maskable/maskable_icon_x72.png',
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": '/static/img/maskable/maskable_icon_x96.png',
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": '/static/img/maskable/maskable_icon_x128.png',
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": '/static/img/maskable/maskable_icon_x192.png',
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": '/static/img/maskable/maskable_icon_x384.png',
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": '/static/img/maskable/maskable_icon_x512.png',
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    },

    # {'size': '430x932', 'src': '/static/img/splash_screens/iPhone_15_Pro_Max__iPhone_15_Plus__iPhone_14_Pro_Max_landscape.png'},
    # {'size': '393x852', 'src': '/static/img/splash_screens/iPhone_15_Pro__iPhone_15__iPhone_14_Pro_landscape.png'},
    # {'size': '428x926', 'src': '/static/img/splash_screens/iPhone_14_Plus__iPhone_13_Pro_Max__iPhone_12_Pro_Max_landscape.png'},
    # {'size': '390x844', 'src': '/static/img/splash_screens/iPhone_14__iPhone_13_Pro__iPhone_13__iPhone_12_Pro__iPhone_12_landscape.png'},
    # {'size': '375x812', 'src': '/static/img/splash_screens/iPhone_13_mini__iPhone_12_mini__iPhone_11_Pro__iPhone_XS__iPhone_X_landscape.png'},
    # {'size': '414x896', 'src': '/static/img/splash_screens/iPhone_11_Pro_Max__iPhone_XS_Max_landscape.png'},
    # {'size': '414x896', 'src': '/static/img/splash_screens/iPhone_11__iPhone_XR_landscape.png'},
    # {'size': '414x736', 'src': '/static/img/splash_screens/iPhone_8_Plus__iPhone_7_Plus__iPhone_6s_Plus__iPhone_6_Plus_landscape.png'},
    # {'size': '375x667', 'src': '/static/img/splash_screens/iPhone_8__iPhone_7__iPhone_6s__iPhone_6__4.7__iPhone_SE_landscape.png'},
    # {'size': '320x568', 'src': '/static/img/splash_screens/4__iPhone_SE__iPod_touch_5th_generation_and_later_landscape.png'},
    # {'size': '102x1366', 'src': '/static/img/splash_screens/12.9__iPad_Pro_landscape.png'},
    # {'size': '834x1194', 'src': '/static/img/splash_screens/11__iPad_Pro__10.5__iPad_Pro_landscape.png'},
    # {'size': '820x1180', 'src': '/static/img/splash_screens/10.9__iPad_Air_landscape.png'},
    # {'size': '834x1112', 'src': '/static/img/splash_screens/10.5__iPad_Air_landscape.png'},
    # {'size': '810x1080', 'src': '/static/img/splash_screens/10.2__iPad_landscape.png'},
    # {'size': '768x1024', 'src': '/static/img/splash_screens/9.7__iPad_Pro__7.9__iPad_mini__9.7__iPad_Air__9.7__iPad_landscape.png'},
    # {'size': '744x1133', 'src': '/static/img/splash_screens/8.3__iPad_Mini_landscape.png'},
    # {'size': '430x932', 'src': '/static/img/splash_screens/iPhone_15_Pro_Max__iPhone_15_Plus__iPhone_14_Pro_Max_portrait.png'},
    # {'size': '393x852', 'src': '/static/img/splash_screens/iPhone_15_Pro__iPhone_15__iPhone_14_Pro_portrait.png'},
    # {'size': '428x926', 'src': '/static/img/splash_screens/iPhone_14_Plus__iPhone_13_Pro_Max__iPhone_12_Pro_Max_portrait.png'},
    # {'size': '390x844', 'src': '/static/img/splash_screens/iPhone_14__iPhone_13_Pro__iPhone_13__iPhone_12_Pro__iPhone_12_portrait.png'},
    # {'size': '375x812', 'src': '/static/img/splash_screens/iPhone_13_mini__iPhone_12_mini__iPhone_11_Pro__iPhone_XS__iPhone_X_portrait.png'},
    # {'size': '414x896', 'src': '/static/img/splash_screens/iPhone_11_Pro_Max__iPhone_XS_Max_portrait.png'},
    # {'size': '414x896', 'src': '/static/img/splash_screens/iPhone_11__iPhone_XR_portrait.png'},
    # {'size': '414x736', 'src': '/static/img/splash_screens/iPhone_8_Plus__iPhone_7_Plus__iPhone_6s_Plus__iPhone_6_Plus_portrait.png'},
    # {'size': '375x667', 'src': '/static/img/splash_screens/iPhone_8__iPhone_7__iPhone_6s__iPhone_6__4.7__iPhone_SE_portrait.png'},
    # {'size': '320x568', 'src': '/static/img/splash_screens/4__iPhone_SE__iPod_touch_5th_generation_and_later_portrait.png'},
    # {'size': '1024x1366', 'src': '/static/img/splash_screens/12.9__iPad_Pro_portrait.png'},
    # {'size': '834x1194', 'src': '/static/img/splash_screens/11__iPad_Pro__10.5__iPad_Pro_portrait.png'},
    # {'size': '820x1180', 'src': '/static/img/splash_screens/10.9__iPad_Air_portrait.png'},
    # {'size': '834x1112', 'src': '/static/img/splash_screens/10.5__iPad_Air_portrait.png'},
    # {'size': '810x1080', 'src': '/static/img/splash_screens/10.2__iPad_portrait.png'},
    # {'size': '768x1024', 'src': '/static/img/splash_screens/9.7__iPad_Pro__7.9__iPad_mini__9.7__iPad_Air__9.7__iPad_portrait.png'},
    # {'size': '744x1133', 'src': '/static/img/splash_screens/8.3__iPad_Mini_portrait.png'},
]

PWA_APP_ICONS_APPLE = [
	{
		'src': 'static/img/favicon.png',
		'sizes': '32x32'
	}
]
PWA_APP_SPLASH_SCREEN = [
	{
		'src': '/static/img/iloveicon512x512.png',
		# 'sizes': '16x16'
		'sizes': '512x512'
	},
	{
		'src': 'static/img/splash-640x1136.png',
		'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
	},

    # {
        
    #     'media': '(device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_15_Pro__iPhone_15__iPhone_14_Pro_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_15_Pro_Max__iPhone_15_Plus__iPhone_14_Pro_Max_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_14_Plus__iPhone_13_Pro_Max__iPhone_12_Pro_Max_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_14__iPhone_13_Pro__iPhone_13__iPhone_12_Pro__iPhone_12_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_13_mini__iPhone_12_mini__iPhone_11_Pro__iPhone_XS__iPhone_X_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_11_Pro_Max__iPhone_XS_Max_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_11__iPhone_XR_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_8_Plus__iPhone_7_Plus__iPhone_6s_Plus__iPhone_6_Plus_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/iPhone_8__iPhone_7__iPhone_6s__iPhone_6__4.7__iPhone_SE_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/4__iPhone_SE__iPod_touch_5th_generation_and_later_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/12.9__iPad_Pro_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/11__iPad_Pro__10.5__iPad_Pro_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 820px) and (device-height: 1180px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/10.9__iPad_Air_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/10.5__iPad_Air_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/10.2__iPad_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/9.7__iPad_Pro__7.9__iPad_mini__9.7__iPad_Air__9.7__iPad_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 744px) and (device-height: 1133px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)' 'src': 'static/img/splash_screens/8.3__iPad_Mini_landscape.png'
    # },
    # {
        
    #     'media': '(device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_15_Pro_Max__iPhone_15_Plus__iPhone_14_Pro_Max_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_15_Pro__iPhone_15__iPhone_14_Pro_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_14_Plus__iPhone_13_Pro_Max__iPhone_12_Pro_Max_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_14__iPhone_13_Pro__iPhone_13__iPhone_12_Pro__iPhone_12_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_13_mini__iPhone_12_mini__iPhone_11_Pro__iPhone_XS__iPhone_X_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_11_Pro_Max__iPhone_XS_Max_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_11__iPhone_XR_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_8_Plus__iPhone_7_Plus__iPhone_6s_Plus__iPhone_6_Plus_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/iPhone_8__iPhone_7__iPhone_6s__iPhone_6__4.7__iPhone_SE_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/4__iPhone_SE__iPod_touch_5th_generation_and_later_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/12.9__iPad_Pro_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/11__iPad_Pro__10.5__iPad_Pro_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 820px) and (device-height: 1180px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/10.9__iPad_Air_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/10.5__iPad_Air_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/10.2__iPad_portrait.png'
    # },
    # {
        
    #     'media': '(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)' 'src': 'static/img/splash_screens/9.7__iPad_Pro__7.9__iPad_mini__9.7__iPad_Air__9.7__iPad_portrait.png'
    # },
    {
        'src': 'static/img/splash_screens/8.3__iPad_Mini_portrait.png',
        'media': '(device-width: 744px) and (device-height: 1133px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)'
    }

    
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en'
PWA_APP_SHORTCUTS = [
    {
        'name': 'Shortcut',
        'url': '/target',
        'description': 'Shortcut to a page in my application'
    }
]
PWA_APP_SCREENSHOTS = [
    {
      'src': 'static/img/splash_screens/8.3__iPad_Mini_portrait.png',
      'sizes': '744x1133',
      "type": "image/png"
    }
]