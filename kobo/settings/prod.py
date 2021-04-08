# coding: utf-8
from .base import *
import ldap
from django_auth_ldap.config import LDAPSearch

# Add specific VARIABLES for production environment here
# So far, all values are declared in `base.py`

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
    }
}

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

if os.environ.get('AUTH_LDAP_1_ACTIVE') and os.environ.get('AUTH_LDAP_1_ACTIVE').lower() == 'true':
    AUTH_LDAP_1_SERVER_URI = os.environ.get('AUTH_LDAP_1_SERVER_URI', '')
    AUTH_LDAP_1_USER_DN_TEMPLATE = os.environ.get('AUTH_LDAP_1_USER_DN_TEMPLATE', '')
    AUTH_LDAP_1_ALWAYS_UPDATE_USER = os.environ.get('AUTH_LDAP_1_ALWAYS_UPDATE_USER', 'False')
    AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER = os.environ.get('AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER', '')
    if(not AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER):
        AUTH_LDAP_1_BIND_DN = os.environ.get('AUTH_LDAP_1_BIND_DN', '')
        AUTH_LDAP_1_BIND_PASSWORD = os.environ.get('AUTH_LDAP_1_BIND_PASSWORD', '')
    AUTH_LDAP_1_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP
    if os.environ.get('AUTH_LDAP_1_OPT_REFERRALS'):
        AUTH_LDAP_1_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: os.environ.get('AUTH_LDAP_1_OPT_REFERRALS')}
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


CONSTANCE_CONFIG = {
    'REGISTRATION_OPEN': (True, 'Allow new users to register accounts for '
                                'themselves'),
    'TERMS_OF_SERVICE_URL': (os.environ.get('KPI_URL', ''),
                            'URL for terms of service document'),
    'PRIVACY_POLICY_URL': (os.environ.get('KPI_URL', ''),
                          'URL for privacy policy'),
    'SOURCE_CODE_URL': (os.environ.get('KPI_URL', 'SUPPORT_URL'),
                        'URL of source code repository. When empty, a link '
                        'will not be shown in the user interface'),
    'SUPPORT_URL': (os.environ.get('KOBO_SUPPORT_URL',''),
                    'URL of user support portal. When empty, a link will not '
                    'be shown in the user interface'),
    'SUPPORT_EMAIL': (os.environ.get('KOBO_SUPPORT_EMAIL') or
                        os.environ.get('DEFAULT_FROM_EMAIL',
                                       ''),
                      'Email address for users to contact, e.g. when they '
                      'encounter unhandled errors in the application'),
    'ALLOW_UNSECURED_HOOK_ENDPOINTS': (True,
                                       'Allow the use of unsecured endpoints for hooks. '
                                       '(e.g http://hook.example.com)'),
    'HOOK_MAX_RETRIES': (3,
                         'Number of times the system will retry '
                         'to send data to remote server before giving up')
}
ENV = 'prod'
