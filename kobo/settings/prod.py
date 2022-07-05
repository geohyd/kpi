# coding: utf-8
from .base import *
# ANTEA : Add some import
import ldap
from django_auth_ldap.config import LDAPSearch
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

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

if os.environ.get('AUTH_LDAP_1_ACTIVE') and os.environ.get('AUTH_LDAP_1_ACTIVE').lower() == 'true':
    AUTH_LDAP_1_SERVER_URI = os.environ.get('AUTH_LDAP_1_SERVER_URI', '')
    AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER = eval(os.environ.get('AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER', 'False'))
    if not AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER:
        AUTH_LDAP_1_BIND_DN = os.environ.get('AUTH_LDAP_1_BIND_DN', '')
        AUTH_LDAP_1_BIND_PASSWORD = os.environ.get('AUTH_LDAP_1_BIND_PASSWORD', '')
    AUTH_LDAP_1_USER_SEARCH = LDAPSearch(
        os.environ.get('AUTH_LDAP_1_BASE_DN', ''), ldap.SCOPE_SUBTREE, os.environ.get('AUTH_LDAP_1_SEARCH_FILTER', '')
    )
    AUTH_LDAP_1_ALWAYS_UPDATE_USER = eval(os.environ.get('AUTH_LDAP_1_ALWAYS_UPDATE_USER', 'False'))
    AUTH_LDAP_1_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP
    AUTHENTICATION_BACKENDS = ("kpi.backends_ldap.LDAPBackend1",) + AUTHENTICATION_BACKENDS

if os.environ.get('AUTH_LDAP_2_ACTIVE') and os.environ.get('AUTH_LDAP_2_ACTIVE').lower() == 'true':
    AUTH_LDAP_2_SERVER_URI = os.environ.get('AUTH_LDAP_2_SERVER_URI', '')
    AUTH_LDAP_2_USER_DN_TEMPLATE = os.environ.get('AUTH_LDAP_2_USER_DN_TEMPLATE', '')
    AUTH_LDAP_2_ALWAYS_UPDATE_USER = os.environ.get('AUTH_LDAP_2_ALWAYS_UPDATE_USER', 'False')
    AUTH_LDAP_2_BIND_AS_AUTHENTICATING_USER = os.environ.get('AUTH_LDAP_2_BIND_AS_AUTHENTICATING_USER', '')
    if (not AUTH_LDAP_2_BIND_AS_AUTHENTICATING_USER):
        AUTH_LDAP_2_BIND_DN = os.environ.get('AUTH_LDAP_2_BIND_DN', '')
        AUTH_LDAP_2_BIND_PASSWORD = os.environ.get('AUTH_LDAP_2_BIND_PASSWORD', '')
    AUTH_LDAP_2_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP
    if os.environ.get('AUTH_LDAP_2_OPT_REFERRALS'):
        AUTH_LDAP_2_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: os.environ.get('AUTH_LDAP_2_OPT_REFERRALS')}
    AUTHENTICATION_BACKENDS = ("kpi.backends_ldap.LDAPBackend2",) + AUTHENTICATION_BACKENDS

if os.environ.get('AUTH_LDAP_3_ACTIVE') and os.environ.get('AUTH_LDAP_3_ACTIVE').lower() == 'true':
    AUTH_LDAP_3_SERVER_URI = os.environ.get('AUTH_LDAP_3_SERVER_URI', '')
    AUTH_LDAP_3_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: 0}
    AUTH_LDAP_3_USER_SEARCH = LDAPSearch(
        os.environ.get('AUTH_LDAP_3_BASE_DN', ''), ldap.SCOPE_SUBTREE, os.environ.get('AUTH_LDAP_3_SEARCH_FILTER', '')
    )
    AUTH_LDAP_3_BIND_DN = os.environ.get('AUTH_LDAP_3_BIND_DN', '')
    AUTH_LDAP_3_BIND_PASSWORD = os.environ.get('AUTH_LDAP_3_BIND_PASSWORD', '')
    AUTH_LDAP_3_BIND_AS_AUTHENTICATING_USER = False
    AUTHENTICATION_BACKENDS = ("kpi.backends_ldap.LDAPBackend3",) + AUTHENTICATION_BACKENDS


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

###################################################
###########   OAUTH2 Authentification   ###########
###################################################
AUTO_AUTH = False
# Need to be ever installed for the views
INSTALLED_APPS = INSTALLED_APPS + (
        'django_auth_adfs',
)

AUTHENTICATION_BACKENDS = AUTHENTICATION_BACKENDS + ('django_auth_adfs.backend.AdfsAuthCodeBackend', )
if AUTO_AUTH:
    MIDDLEWARE.append('django_auth_adfs.middleware.LoginRequiredMiddleware')
    

# TODO : NE PAS POUSSER CA SUR GIT !!
# IL FAUT D ABORD LE METTRE DANS LE FICHIER COMMON.CONF
client_id = os.environ.get('OAUTH2_CLIENT_ID','')
client_secret = os.environ.get('OAUTH2_CLIENT_SECRET','')
tenant_id = os.environ.get('OAUTH2_TENANT_ID','')

AUTH_ADFS = {
    'AUDIENCE': client_id,
    'CLIENT_ID': client_id,
    'CLIENT_SECRET': client_secret,
    'CLAIM_MAPPING': {'first_name': 'given_name',
                      'last_name': 'family_name',
                      'email': 'upn'},
    'GROUPS_CLAIM': 'roles',
    'MIRROR_GROUPS': True,
    #'USERNAME_CLAIM': 'upn',
	'USERNAME_CLAIM': 'name',
    'TENANT_ID': tenant_id,
    'RELYING_PARTY_ID': client_id,
    'DISABLE_SSO' : False,
}
LOGIN_URL = "django_auth_adfs:login"
LOGIN_REDIRECT_URL = "/survea/"

