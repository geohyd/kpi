# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .base import *


# Add specific VARIABLES for production environment here
# So far, all values are declared in `base.py`

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

if os.environ.get('AUTH_LDAP_1_ACTIVE') and os.environ.get('AUTH_LDAP_1_ACTIVE').lower() == 'true':
    AUTH_LDAP_1_SERVER_URI = os.environ.get('AUTH_LDAP_1_SERVER_URI', '')
    AUTH_LDAP_1_USER_DN_TEMPLATE = os.environ.get('AUTH_LDAP_1_USER_DN_TEMPLATE', '')
    AUTH_LDAP_1_ALWAYS_UPDATE_USER = os.environ.get('AUTH_LDAP_1_ALWAYS_UPDATE_USER', '')
    AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER = os.environ.get('AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER', '')
    if(not AUTH_LDAP_1_BIND_AS_AUTHENTICATING_USER):
        AUTH_LDAP_1_BIND_DN = os.environ.get('AUTH_LDAP_1_BIND_DN', '')
        AUTH_LDAP_1_BIND_PASSWORD = os.environ.get('AUTH_LDAP_1_BIND_PASSWORD', '')
    AUTH_LDAP_1_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP
    AUTHENTICATION_BACKENDS = ("kpi.backends_ldap.LDAPBackend1",) + AUTHENTICATION_BACKENDS

if os.environ.get('AUTH_LDAP_2_ACTIVE') and os.environ.get('AUTH_LDAP_2_ACTIVE').lower() == 'true':
    AUTH_LDAP_2_SERVER_URI = os.environ.get('AUTH_LDAP_2_SERVER_URI', '')
    AUTH_LDAP_2_USER_DN_TEMPLATE = os.environ.get('AUTH_LDAP_2_USER_DN_TEMPLATE', '')
    AUTH_LDAP_2_ALWAYS_UPDATE_USER = os.environ.get('AUTH_LDAP_2_ALWAYS_UPDATE_USER', '')
    AUTH_LDAP_2_BIND_AS_AUTHENTICATING_USER = os.environ.get('AUTH_LDAP_2_BIND_AS_AUTHENTICATING_USER', '')
    if (not AUTH_LDAP_2_BIND_AS_AUTHENTICATING_USER):
        AUTH_LDAP_2_BIND_DN = os.environ.get('AUTH_LDAP_2_BIND_DN', '')
        AUTH_LDAP_2_BIND_PASSWORD = os.environ.get('AUTH_LDAP_2_BIND_PASSWORD', '')
    AUTH_LDAP_2_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP
    AUTHENTICATION_BACKENDS = ("kpi.backends_ldap.LDAPBackend2",) + AUTHENTICATION_BACKENDS

if os.environ.get('AUTH_LDAP_3_ACTIVE') and os.environ.get('AUTH_LDAP_3_ACTIVE').lower() == 'true':
    AUTH_LDAP_3_SERVER_URI = os.environ.get('AUTH_LDAP_3_SERVER_URI', '')
    AUTH_LDAP_3_USER_DN_TEMPLATE = os.environ.get('AUTH_LDAP_3_USER_DN_TEMPLATE', '')
    AUTH_LDAP_3_ALWAYS_UPDATE_USER = os.environ.get('AUTH_LDAP_3_ALWAYS_UPDATE_USER', '')
    AUTH_LDAP_3_BIND_AS_AUTHENTICATING_USER = os.environ.get('AUTH_LDAP_3_BIND_AS_AUTHENTICATING_USER', '')
    if (not AUTH_LDAP_3_BIND_AS_AUTHENTICATING_USER):
        AUTH_LDAP_3_BIND_DN = os.environ.get('AUTH_LDAP_3_BIND_DN', '')
        AUTH_LDAP_3_BIND_PASSWORD = os.environ.get('AUTH_LDAP_3_BIND_PASSWORD', '')
    AUTH_LDAP_3_USER_ATTR_MAP = AUTH_LDAP_USER_ATTR_MAP
    AUTHENTICATION_BACKENDS = ("kpi.backends_ldap.LDAPBackend3",) + AUTHENTICATION_BACKENDS

