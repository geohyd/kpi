# coding: utf-8
from .base import *
# ANTEA END
# Add specific VARIABLES for production environment here
# So far, all values are declared in `base.py`

# ANTEA : Add some CONFIG
# add 'STATS_FILE': "/srv/kobo/kpi/webpack-stats.json",
# vraiment nécessaire ?
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'jsapp/compiled/',
        'STATS_FILE': "/srv/kobo/kpi/webpack-stats.json",
        'POLL_INTERVAL': 0.5,
        'TIMEOUT': 5,
    }
}

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('PG_DB_KPI', 'kobo_db'),
        'USER': os.environ.get('PG_USER', 'kobo'),
        'PASSWORD': os.environ.get('PG_PASS', 'kobo'),
        'HOST': os.environ.get('PG_HOST', '127.0.0.1'),
        'PORT': os.environ.get('PG_PORT', '5432'),
    },
    'kobocat': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('PG_DB_KOBO', 'kobo_db'),
        'USER': os.environ.get('PG_USER', 'kobo'),
        'PASSWORD': os.environ.get('PG_PASS', 'kobo'),
        'HOST': os.environ.get('PG_HOST', '127.0.0.1'),
        'PORT': os.environ.get('PG_PORT', '5432'),
        'OPTIONS': {
            'options': '-c search_path=kobo'
        },
    }
}


CONSTANCE_CONFIG["SOURCE_CODE_URL"] = (os.environ.get('SOURCE_CODE_URL', 'https://github.com/geohyd/kpi'),
                        'URL of source code repository. When empty, a link '
                        'will not be shown in the user interface')


CONSTANCE_CONFIG["SUPPORT_URL"] = (os.environ.get('KOBO_SUPPORT_URL',''),
                    'URL of user support portal. When empty, a link will not '
                    'be shown in the user interface')

CONSTANCE_CONFIG["SUPPORT_EMAIL"] = (os.environ.get('KOBO_SUPPORT_EMAIL') or
                        os.environ.get('DEFAULT_FROM_EMAIL',
                                       ''),
                      'Email address for users to contact, e.g. when they '
                      'encounter unhandled errors in the application')

CONSTANCE_CONFIG["HOOK_FORCE_FAILED_WITH_STATUS_CODE"] = (
        500,
        'If the hook service receive this status code'
        'Set automaticaly to HOOK_LOG_FAILED the hook instance (without retries)',
        int
    )

# END ANTEA
ENV = 'prod'

