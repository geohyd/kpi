# coding: utf-8
from .base import *

# Add specific VARIABLES for production environment here
# So far, all values are declared in `base.py`

# ANTEA : Add some import
import ldap
from django_auth_ldap.config import LDAPSearch

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',
#         'NAME': os.environ.get('PG_DB_KPI', 'kobo_db'),
#         'USER': os.environ.get('PG_USER', 'kobo'),
#         'PASSWORD': os.environ.get('PG_PASS', 'kobo'),
#         'HOST': os.environ.get('PG_HOST', '127.0.0.1'),
#         'PORT': os.environ.get('PG_PORT', '5432'),
#     },
#     'kobocat': {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',
#         'NAME': os.environ.get('PG_DB_KOBO', 'kobo_db'),
#         'USER': os.environ.get('PG_USER', 'kobo'),
#         'PASSWORD': os.environ.get('PG_PASS', 'kobo'),
#         'HOST': os.environ.get('PG_HOST', '127.0.0.1'),
#         'PORT': os.environ.get('PG_PORT', '5432'),
#     }
# }

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

ENV = os.environ.get('KPI_ENV', 'dev')
