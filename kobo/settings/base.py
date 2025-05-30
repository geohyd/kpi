# coding: utf-8
import logging
import os
import re
import string
import subprocess
from datetime import datetime
from mimetypes import add_type
from urllib.parse import quote_plus

import django.conf.locale
import environ
from celery.schedules import crontab
from django.conf.global_settings import LOGIN_URL
from django.urls import reverse_lazy
from django.utils.translation import get_language_info, gettext_lazy as t
from pymongo import MongoClient

from kpi.utils.json import LazyJSONSerializable
from kobo.apps.stripe.constants import FREE_TIER_NO_THRESHOLDS, FREE_TIER_EMPTY_DISPLAY
from ..static_lists import EXTRA_LANG_INFO, SECTOR_CHOICE_DEFAULTS

env = environ.Env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
settings_dirname = os.path.dirname(os.path.abspath(__file__))
parent_dirname = os.path.dirname(settings_dirname)
BASE_DIR = os.path.abspath(os.path.dirname(parent_dirname))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('DJANGO_SECRET_KEY', '@25)**hc^rjaiagb4#&q*84hr*uscsxwr-cv#0joiwj$))obyk')

# Optionally treat proxied connections as secure.
# See: https://docs.djangoproject.com/en/1.8/ref/settings/#secure-proxy-ssl-header.
# Example environment: `export SECURE_PROXY_SSL_HEADER='HTTP_X_FORWARDED_PROTO, https'`.
# SECURITY WARNING: If enabled, outer web server must filter out the `X-Forwarded-Proto` header.
SECURE_PROXY_SSL_HEADER = env.tuple("SECURE_PROXY_SSL_HEADER", str, None)

if env.str('PUBLIC_REQUEST_SCHEME', '').lower() == 'https' or SECURE_PROXY_SSL_HEADER:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', False)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', 0)

# Make Django use NginX $host. Useful when running with ./manage.py runserver_plus
# It avoids adding the debugger webserver port (i.e. `:8000`) at the end of urls.
USE_X_FORWARDED_HOST = env.bool("USE_X_FORWARDED_HOST", False)

# Domain must not exclude KoBoCAT when sharing sessions
SESSION_COOKIE_DOMAIN = env.str('SESSION_COOKIE_DOMAIN', None)
if SESSION_COOKIE_DOMAIN:
    SESSION_COOKIE_NAME = env.str('SESSION_COOKIE_NAME', 'kobonaut')
    # The trusted CSRF origins must encompass Enketo's subdomain. See
    # https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS
    CSRF_TRUSTED_ORIGINS = [SESSION_COOKIE_DOMAIN]
ENKETO_CSRF_COOKIE_NAME = env.str('ENKETO_CSRF_COOKIE_NAME', '__csrf')

# Limit sessions to 1 week (the default is 2 weeks)
SESSION_COOKIE_AGE = env.int('DJANGO_SESSION_COOKIE_AGE', 604800)

# Set language cookie age to same value as session cookie
LANGUAGE_COOKIE_AGE = SESSION_COOKIE_AGE

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env.str('DJANGO_ALLOWED_HOSTS', '*').split(' ')

LOGIN_REDIRECT_URL = 'kpi-root'
LOGOUT_REDIRECT_URL = 'kobo_login'  # Use URL pattern instead of hard-coded value

# Application definition

# The order of INSTALLED_APPS is important for template resolution. When two
# apps both define templates for the same view, the first app listed receives
# precedence
INSTALLED_APPS = (
    # Always put `contenttypes` before `auth`; see
    # https://code.djangoproject.com/ticket/10827
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_prometheus',
    'reversion',
    'private_storage',
    'kobo.apps.KpiConfig',
    'kobo.apps.accounts',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.microsoft',
    'allauth.socialaccount.providers.openid_connect',
    'hub.HubAppConfig',
    'loginas',
    'webpack_loader',
    'django_extensions',
    'django_filters',
    'taggit',
    'rest_framework',
    'rest_framework.authtoken',
    'oauth2_provider',
    'django_digest',
    'kobo.apps.organizations',
    'kobo.apps.superuser_stats.SuperuserStatsAppConfig',
    'kobo.apps.service_health',
    'kobo.apps.subsequences',
    'constance',
    'constance.backends.database',
    'kobo.apps.hook',
    'django_celery_beat',
    'corsheaders',
    'kobo.apps.external_integrations.ExternalIntegrationsAppConfig',
    'markdownx',
    'kobo.apps.help',
    'kobo.apps.shadow_model.ShadowModelAppConfig',
    'trench',
    'kobo.apps.accounts.mfa.apps.MfaAppConfig',
    'kobo.apps.languages.LanguageAppConfig',
    'kobo.apps.project_views.ProjectViewAppConfig',
    'kobo.apps.audit_log.AuditLogAppConfig',
    'kobo.apps.trackers.TrackersConfig',
    'kobo.apps.trash_bin.TrashBinAppConfig',
    'kobo.apps.markdownx_uploader.MarkdownxUploaderAppConfig',
    'kobo.apps.form_disclaimer.FormDisclaimerAppConfig',
)

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'hub.middleware.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'hub.middleware.UsernameInResponseHeaderMiddleware',
    'django_userforeignkey.middleware.UserForeignKeyMiddleware',
    'django_request_cache.middleware.RequestCacheMiddleware',
]

if os.environ.get('DEFAULT_FROM_EMAIL'):
    DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Configuration options that superusers can modify in the Django admin
# interface. Please note that it's not as simple as moving a setting into the
# `CONSTANCE_CONFIG` dictionary: each place where the setting's value is needed
# must use `constance.config.THE_SETTING` instead of
# `django.conf.settings.THE_SETTING`
CONSTANCE_CONFIG = {
    'REGISTRATION_OPEN': (
        True,
        'Allow new users to register accounts for themselves',
    ),
    'REGISTRATION_ALLOWED_EMAIL_DOMAINS': (
        '',
        'Email domains allowed to register new accounts, one per line, '
        'or blank to allow all email domains'
    ),
    'REGISTRATION_DOMAIN_NOT_ALLOWED_ERROR_MESSAGE': (
        'This email domain is not allowed to create an account',
        'Error message for emails not listed in REGISTRATION_ALLOWED_EMAIL_DOMAINS '
        'if field is not blank'
    ),
    'TERMS_OF_SERVICE_URL': ('', 'URL for terms of service document'),
    'PRIVACY_POLICY_URL': ('', 'URL for privacy policy'),
    'SOURCE_CODE_URL': (
        'https://github.com/kobotoolbox/',
        'URL of source code repository. When empty, a link will not be shown '
        'in the user interface',
    ),
    'SUPPORT_EMAIL': (
        env.str('KOBO_SUPPORT_EMAIL', env.str('DEFAULT_FROM_EMAIL', 'help@kobotoolbox.org')),
        'Email address for users to contact, e.g. when they encounter '
        'unhandled errors in the application',
    ),
    'SUPPORT_URL': (
        env.str('KOBO_SUPPORT_URL', 'https://support.kobotoolbox.org/'),
        'URL for "KoboToolbox Help Center"',
    ),
    'COMMUNITY_URL': (
        env.str(
            'KOBO_COMMUNITY_URL', 'https://community.kobotoolbox.org/'
        ),
        'URL for "KoboToolbox Community Forum"',
    ),
    'SYNCHRONOUS_EXPORT_CACHE_MAX_AGE': (
        300,
        'A synchronous export request will return the last export generated '
        'with the same settings unless it is older than this value (seconds)'
    ),
    'ALLOW_UNSECURED_HOOK_ENDPOINTS': (
        True,
        'Allow the use of unsecured endpoints for hooks. '
        '(e.g http://hook.example.com)',
    ),
    'HOOK_MAX_RETRIES': (
        3,
        'Number of times the system will retry to send data to remote server '
        'before giving up',
    ),
    'SSRF_ALLOWED_IP_ADDRESS': (
        '',
        'Whitelisted IP addresses to bypass SSRF protection\nOne per line',
    ),
    'SSRF_DENIED_IP_ADDRESS': (
        '',
        'Blacklisted IP addresses to bypass SSRF protection\nOne per line',
    ),
    'EXPOSE_GIT_REV': (
        False,
        'Display information about the running commit to non-superusers',
    ),
    'FRONTEND_MIN_RETRY_TIME': (
        2,
        'Minimum number of seconds the front end waits before retrying a '
        'failed request to the back end',
        int,
    ),
    'FRONTEND_MAX_RETRY_TIME': (
        120,
        'Maximum number of seconds the front end waits before retrying a '
        'failed request to the back end',
        int,
    ),
    'MFA_ISSUER_NAME': (
        'KoboToolbox',
        'Issuer name displayed in multi-factor applications'
    ),
    'MFA_ENABLED': (
        True,
        'Enable two-factor authentication'
    ),
    'MFA_LOCALIZED_HELP_TEXT': (
        LazyJSONSerializable({
            'default': t(
                'If you cannot access your authenticator app, please enter one '
                'of your backup codes instead. If you cannot access those '
                'either, then you will need to request assistance by '
                'contacting [##support email##](mailto:##support email##).'
            ),
            'some-other-language': (
                'This will never appear because `some-other-language` is not '
                'a valid language code, but this entry is here to show you '
                'an example of adding another message in a different language.'
            )
        }),
        (
            'Guidance message presented when users click the '
            '"Problems with the token" link.\n\n'
            '`##support email##` is a placeholder for the `SUPPORT_EMAIL` '
            'setting.\n'
            'Markdown syntax is supported.\n'
            'The “default” message will be used if no translations are provided.'
            ' The “default” should be in English.\n'
            'To add messages in other languages, follow the example of '
            '“some-other-language“, but replace “some-other-language“ with a '
            'valid language code (e.g. “fr“ for French).'

        ),
        # Use custom field for schema validation
        'i18n_text_jsonfield_schema'
    ),
    'ASR_MT_INVITEE_USERNAMES': (
        '',
        'List of invited usernames, one per line, who will have access to NLP '
        'ASR/MT processing via external (costly) APIs.\nEnter * to invite '
        'all users.'
    ),
    'ASR_MT_GOOGLE_CREDENTIALS': (
        '',
        'The JSON content of a private key file generated by the Google Cloud '
        'IAM & Admin console.\nLeave blank to use a different Google '
        'authentication mechanism.'
    ),
    'USER_METADATA_FIELDS': (
        LazyJSONSerializable([
            {'name': 'name', 'required': True},
            {'name': 'organization', 'required': False},
            {'name': 'organization_website', 'required': False},
            {'name': 'sector', 'required': False},
            {'name': 'gender', 'required': False},
            {'name': 'bio', 'required': False},
            {'name': 'city', 'required': False},
            {'name': 'country', 'required': False},
            {'name': 'twitter', 'required': False},
            {'name': 'linkedin', 'required': False},
            {'name': 'instagram', 'required': False},
        ]),
        # The available fields are hard-coded in the front end
        'Display (and optionally require) these metadata fields for users.\n'
        "Possible fields are:\n"
        "'organization', 'organization_website', 'sector', 'gender', 'bio', "
        "'city', 'country', 'twitter', 'linkedin', and 'instagram'.\n\n"
        'To add another language, follow the example below.\n\n'
        '{"name": "name", "required": False, "label": '
        '{"default": "Full Name", "fr": "Nom Complet"}}\n'
        "'default' is a required field within the 'label' dict, but 'label' is optional.",
        # Use custom field for schema validation
        'long_metadata_fields_jsonschema'
    ),
    'PROJECT_METADATA_FIELDS': (
        LazyJSONSerializable([
            {'name': 'sector', 'required': False},
            {'name': 'country', 'required': False},
            {'name': 'description', 'required': False},
        ]),
        # The available fields are hard-coded in the front end
        'Display (and optionally require) these metadata fields for projects.\n'
        "Possible fields are:\n"
        "'sector', 'country', 'operational_purpose', 'collects_pii', "
        "and 'description'\n\n"
        'To add another language, follow the example below.\n\n'
        '{"name": "sector", "required": False, "label": '
        '{"default": "Sector", "fr": "Secteur"}}\n'
        "'default' is a required field within the 'label' dict, but 'label' is optional.",
        # Use custom field for schema validation
        'metadata_fields_jsonschema'
    ),
    'SECTOR_CHOICES': (
        '\n'.join((s[0] for s in SECTOR_CHOICE_DEFAULTS)),
        "Options available for the 'sector' metadata field, one per line.",
        'long_textfield'
    ),
    'OPERATIONAL_PURPOSE_CHOICES': (
        '',
        "Options available for the 'operational purpose of data' metadata "
        'field, one per line.'
    ),
    'ASSET_SNAPSHOT_DAYS_RETENTION': (
        30,
        'Number of days to keep asset snapshots',
        'positive_int'
    ),
    'FREE_TIER_THRESHOLDS': (
        LazyJSONSerializable(FREE_TIER_NO_THRESHOLDS),
        'Free tier thresholds: storage in kilobytes, '
        'data (number of submissions), '
        'minutes of transcription, '
        'number of translation characters',
        # Use custom field for schema validation
        'free_tier_threshold_jsonschema',
    ),
    'FREE_TIER_DISPLAY': (
        LazyJSONSerializable(FREE_TIER_EMPTY_DISPLAY),
        'Free tier frontend settings: name to use for the free tier, '
        'array of text strings to display on the feature list of the Plans page',
        'free_tier_display_jsonschema',
    ),
    'FREE_TIER_CUTOFF_DATE': (
        datetime(2050, 1, 1).date(),
        'Users on the free tier who registered before this date will\n'
        'use the custom plan defined by FREE_TIER_DISPLAY and FREE_TIER_LIMITS.',
    ),
    'PROJECT_TRASH_GRACE_PERIOD': (
        7,
        'Number of days to keep projects in trash after users (soft-)deleted '
        'them and before automatically hard-deleting them by the system',
        'positive_int',
    ),
    'ACCOUNT_TRASH_GRACE_PERIOD': (
        30 * 6,
        'Number of days to keep deactivated accounts in trash before '
        'automatically hard-deleting all their projects and data.\n'
        'Use -1 to require a superuser to empty the trash manually instead of '
        'having the system empty it automatically.',
        'positive_int_minus_one',
    ),
    # Toggle for ZXCVBN
    'ENABLE_PASSWORD_ENTROPY_METER': (
        True,
        'Display an entropy meter and password quality suggestions whenever users change their passwords.',
    ),
    'ENABLE_PASSWORD_MINIMUM_LENGTH_VALIDATION': (
        False,
        'Enable minimum length validation',
    ),
    'MINIMUM_PASSWORD_LENGTH': (
        10,
        'Minimum length for all passwords.',
        int,
    ),
    'ENABLE_PASSWORD_USER_ATTRIBUTE_SIMILARITY_VALIDATION': (
        False,
        'Enable user attribute similarity validation. '
        'See `PASSWORD_USER_ATTRIBUTES` below for customization.',
    ),
    'PASSWORD_USER_ATTRIBUTES': (
        (
            'username\n'
            'full_name\n'
            'email'
        ),
        'List (one per line) all user attributes for similarity validation.\n'
        "Possible attributes are 'username', 'full_name', 'email', 'organization'."
    ),
    'ENABLE_COMMON_PASSWORD_VALIDATION': (
        False,
        'Enable common password validation.\n'
        'To customize the list, go to Configuration file section and add common password file.\n'
        'Django default list is based on https://tinyurl.com/django3-2-common-passwords.',
    ),
    'ENABLE_PASSWORD_CUSTOM_CHARACTER_RULES_VALIDATION': (
        False,
        'Enable custom character rules',
    ),
    'PASSWORD_CUSTOM_CHARACTER_RULES': (
        (
            '[[:lower:]]\n'
            '[[:upper:]]\n'
            '\d\n'
            '[\W_]'
        ),
        'List all custom character rules as regular expressions supported '
        'by `regex` python library.\n'
        'One per line.'
        ,
    ),
    'PASSWORD_CUSTOM_CHARACTER_RULES_REQUIRED_TO_PASS': (
        3,
        'The minimum number of character rules to pass.',
        int,
    ),
    'ENABLE_MOST_RECENT_PASSWORD_VALIDATION': (
        False,
        'Enable most recent password validation which will prevent the user from '
        'reusing the most recent password.',
    ),
    'ENABLE_CUSTOM_PASSWORD_GUIDANCE_TEXT': (
        False,
        'Enable custom password guidance text to help users create their passwords.',
    ),
    'CUSTOM_PASSWORD_GUIDANCE_TEXT': (
        LazyJSONSerializable(
            {
                'default': t(
                    'The password must be at least 10 characters long and'
                    ' contain 3 or more of the following: uppercase letters,'
                    ' lowercase letters, numbers, and special characters. It'
                    ' cannot be similar to your name, username, or email'
                    ' address.'
                ),
                'some-other-language': (
                    'This will never appear because `some-other-language` is'
                    ' not a valid language code, but this entry is here to show'
                    ' you an example of adding another message in a different'
                    ' language.'
                ),
            }
        ),
        (
            'Guidance message presented when users create or modify a password. '
            'It should reflect the defined password rules.\n\n'
            'Markdown syntax is supported.\n'
            'The “default” message will be used if no translations are provided.'
            ' The “default” should be in English.\n'
            'To add messages in other languages, follow the example of '
            '“some-other-language“, but replace “some-other-language“ with a '
            'valid language code (e.g. “fr“ for French).'
        ),
        'i18n_text_jsonfield_schema',
    ),
}

CONSTANCE_ADDITIONAL_FIELDS = {
    'free_tier_threshold_jsonschema': [
        'kpi.fields.jsonschema_form_field.FreeTierThresholdField',
        {'widget': 'django.forms.Textarea'},
    ],
    'free_tier_display_jsonschema': [
        'kpi.fields.jsonschema_form_field.FreeTierDisplayField',
        {'widget': 'django.forms.Textarea'},
    ],
    'i18n_text_jsonfield_schema': [
        'kpi.fields.jsonschema_form_field.I18nTextJSONField',
        {'widget': 'django.forms.Textarea'},
    ],
    'long_metadata_fields_jsonschema': [
        'kpi.fields.jsonschema_form_field.UserMetadataFieldsListField',
        {
            'widget': 'django.forms.Textarea',
            'widget_kwargs': {
                'attrs': {'rows': 45}
            }
        },
    ],
    'long_textfield': [
        'django.forms.fields.CharField',
        {
            'widget': 'django.forms.Textarea',
            'widget_kwargs': {
                'attrs': {'rows': 30}
            }
        },
    ],
    'metadata_fields_jsonschema': [
        'kpi.fields.jsonschema_form_field.MetadataFieldsListField',
        {'widget': 'django.forms.Textarea'},
    ],
    'positive_int': ['django.forms.fields.IntegerField', {
        'min_value': 0
    }],
    'positive_int_minus_one': ['django.forms.fields.IntegerField', {
        'min_value': -1
    }],
}

CONSTANCE_CONFIG_FIELDSETS = {
    'General Options': (
        'REGISTRATION_OPEN',
        'REGISTRATION_ALLOWED_EMAIL_DOMAINS',
        'REGISTRATION_DOMAIN_NOT_ALLOWED_ERROR_MESSAGE',
        'TERMS_OF_SERVICE_URL',
        'PRIVACY_POLICY_URL',
        'SOURCE_CODE_URL',
        'SUPPORT_EMAIL',
        'SUPPORT_URL',
        'COMMUNITY_URL',
        'SYNCHRONOUS_EXPORT_CACHE_MAX_AGE',
        'EXPOSE_GIT_REV',
        'FRONTEND_MIN_RETRY_TIME',
        'FRONTEND_MAX_RETRY_TIME',
    ),
    'Rest Services': (
        'ALLOW_UNSECURED_HOOK_ENDPOINTS',
        'HOOK_MAX_RETRIES',
    ),
    'Natural language processing': (
        'ASR_MT_INVITEE_USERNAMES',
        'ASR_MT_GOOGLE_CREDENTIALS',
    ),
    'Security': (
        'SSRF_ALLOWED_IP_ADDRESS',
        'SSRF_DENIED_IP_ADDRESS',
        'MFA_ISSUER_NAME',
        'MFA_ENABLED',
        'MFA_LOCALIZED_HELP_TEXT',
    ),
    'Metadata options': (
        'USER_METADATA_FIELDS',
        'PROJECT_METADATA_FIELDS',
        'SECTOR_CHOICES',
        'OPERATIONAL_PURPOSE_CHOICES',
    ),
    'Password Validation': (
        'ENABLE_PASSWORD_ENTROPY_METER',
        'ENABLE_PASSWORD_MINIMUM_LENGTH_VALIDATION',
        'ENABLE_PASSWORD_USER_ATTRIBUTE_SIMILARITY_VALIDATION',
        'ENABLE_COMMON_PASSWORD_VALIDATION',
        'ENABLE_PASSWORD_CUSTOM_CHARACTER_RULES_VALIDATION',
        'ENABLE_MOST_RECENT_PASSWORD_VALIDATION',
        'ENABLE_CUSTOM_PASSWORD_GUIDANCE_TEXT',
        'MINIMUM_PASSWORD_LENGTH',
        'PASSWORD_USER_ATTRIBUTES',
        'PASSWORD_CUSTOM_CHARACTER_RULES',
        'PASSWORD_CUSTOM_CHARACTER_RULES_REQUIRED_TO_PASS',
        'CUSTOM_PASSWORD_GUIDANCE_TEXT',
    ),
    'Trash bin': (
        'ASSET_SNAPSHOT_DAYS_RETENTION',
        'ACCOUNT_TRASH_GRACE_PERIOD',
        'PROJECT_TRASH_GRACE_PERIOD',
    ),
    'Tier settings': (
        'FREE_TIER_THRESHOLDS',
        'FREE_TIER_DISPLAY',
        'FREE_TIER_CUTOFF_DATE',
    ),
}

# Tell django-constance to use a database model instead of Redis
CONSTANCE_BACKEND = 'kobo.apps.constance_backends.database.DatabaseBackend'
CONSTANCE_DATABASE_CACHE_BACKEND = 'default'


# Warn developers to use `pytest` instead of `./manage.py test`
class DoNotUseRunner:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError('Please run tests with `pytest` instead')


TEST_RUNNER = __name__ + '.DoNotUseRunner'

# The backend that handles user authentication must match KoBoCAT's when
# sharing sessions. ModelBackend does not interfere with object-level
# permissions: it always denies object-specific requests (see
# https://github.com/django/django/blob/1.7/django/contrib/auth/backends.py#L44).
# KoBoCAT also lists ModelBackend before
# guardian.backends.ObjectPermissionBackend.
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'kpi.backends.ObjectPermissionBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

ROOT_URLCONF = 'kobo.urls'

WSGI_APPLICATION = 'kobo.wsgi.application'

# What User object should be mapped to AnonymousUser?
ANONYMOUS_USER_ID = -1
# Permissions assigned to AnonymousUser are restricted to the following
ALLOWED_ANONYMOUS_PERMISSIONS = (
    'kpi.view_asset',
    'kpi.discover_asset',
    'kpi.view_submissions',
)

# run heavy migration scripts by default
# NOTE: this should be set to False for major deployments. This can take a long time
SKIP_HEAVY_MIGRATIONS = env.bool('SKIP_HEAVY_MIGRATIONS', False)

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASES = {
    'default': env.db_url(
        'KPI_DATABASE_URL' if 'KPI_DATABASE_URL' in os.environ else 'DATABASE_URL',
        default='sqlite:///%s/db.sqlite3' % BASE_DIR
    ),
}

if 'KC_DATABASE_URL' in os.environ:
    DATABASES['kobocat'] = env.db_url('KC_DATABASE_URL')

DATABASE_ROUTERS = ['kpi.db_routers.DefaultDatabaseRouter']

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

django.conf.locale.LANG_INFO.update(EXTRA_LANG_INFO)

DJANGO_LANGUAGE_CODES = env.str(
    'DJANGO_LANGUAGE_CODES',
    default=(
        'am '  # Amharic
        'ar '  # Arabic
        'bn '  # Bengali
        'cs '  # Czech
        'de '  # German
        'en '  # English
        'es '  # Spanish
        'fa '  # Persian/Farsi
        'fr '  # French
        'hi '  # Hindi
        'hu '  # Hungarian
        'id '  # Indonesian
        'ja '  # Japanese
        'ku '  # Kurdish
        'ln '  # Lingala
        'my '  # Burmese/Myanmar
        'ny '  # Chewa/Chichewa/Nyanja
        'ne '  # Nepali
        'pl '  # Polish
        'pt '  # Portuguese
        'ru '  # Russian
        'th '  # Thai
        'tr '  # Turkish
        'uk '  # Ukrainian
        'vi '  # Vietnamese
        'zh-hans'  # Chinese Simplified
    )
)
LANGUAGES = [
    (lang_code, get_language_info(lang_code)['name_local'])
    for lang_code in DJANGO_LANGUAGE_CODES.split(' ')
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)

USE_I18N = True

USE_L10N = True

USE_TZ = True

CAN_LOGIN_AS = lambda request, target_user: request.user.is_superuser

# Impose a limit on the number of records returned by the submission list
# endpoint. This overrides any `?limit=` query parameter sent by a client
SUBMISSION_LIST_LIMIT = 30000

# uWSGI, NGINX, etc. allow only a limited amount of time to process a request.
# Set this value to match their limits
SYNCHRONOUS_REQUEST_TIME_LIMIT = 120  # seconds

# REMOVE the oldest if a user exceeds this many exports for a particular form
MAXIMUM_EXPORTS_PER_USER_PER_FORM = 10

# Private media file configuration
PRIVATE_STORAGE_ROOT = os.path.join(BASE_DIR, 'media')
PRIVATE_STORAGE_AUTH_FUNCTION = \
    'kpi.utils.private_storage.superuser_or_username_matches_prefix'

# django-markdownx, for in-app messages
MARKDOWNX_UPLOAD_URLS_PATH = reverse_lazy('markdownx-uploader-image-upload')
MARKDOWNX_UPLOAD_CONTENT_TYPES = [
    'image/jpeg',
    'image/png',
    'image/svg+xml',
    'image/gif',
    'image/webp',
]
# Github-flavored Markdown from `py-gfm`,
# ToDo Uncomment when it's compatible with Markdown 3.x
# MARKDOWNX_MARKDOWN_EXTENSIONS = ['mdx_gfm']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/' + os.environ.get('KPI_MEDIA_URL', 'media').strip('/') + '/'

# `PUBLIC_MEDIA_PATH` sets the `upload_to` attribute of explicitly-public
# `FileField`s, e.g. in `ConfigurationFile`. The corresponding location on the
# file system (usually `MEDIA_ROOT + PUBLIC_MEDIA_PATH`) should be exposed to
# everyone via NGINX. For more information, see
# https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.FileField.upload_to
PUBLIC_MEDIA_PATH = '__public/'

# Following the uWSGI mountpoint convention, this should have a leading slash
# but no trailing slash
KPI_PREFIX = env.str('KPI_PREFIX', 'False')
if KPI_PREFIX.lower() == 'false':
    KPI_PREFIX = False
else:
    KPI_PREFIX = '/' + KPI_PREFIX.strip('/')

# KPI_PREFIX should be set in the environment when running in a subdirectory
if KPI_PREFIX and KPI_PREFIX != '/':
    STATIC_URL = KPI_PREFIX + '/' + STATIC_URL.lstrip('/')
    MEDIA_URL = KPI_PREFIX + '/' + MEDIA_URL.lstrip('/')
    LOGIN_URL = KPI_PREFIX + '/' + LOGIN_URL.lstrip('/')
    LOGIN_REDIRECT_URL = KPI_PREFIX + '/' + LOGIN_REDIRECT_URL.lstrip('/')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'jsapp'),
    os.path.join(BASE_DIR, 'static'),
    ('mocha', os.path.join(BASE_DIR, 'node_modules', 'mocha'),),
    ('chai', os.path.join(BASE_DIR, 'node_modules', 'chai'),),
)

if os.path.exists(os.path.join(BASE_DIR, 'dkobo', 'jsapp')):
    STATICFILES_DIRS = STATICFILES_DIRS + (
        os.path.join(BASE_DIR, 'dkobo', 'jsapp'),
        os.path.join(BASE_DIR, 'dkobo', 'dkobo', 'static'),
    )

REST_FRAMEWORK = {
    'URL_FIELD_NAME': 'url',
    'DEFAULT_PAGINATION_CLASS': 'kpi.paginators.Paginated',
    'PAGE_SIZE': 100,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # SessionAuthentication and BasicAuthentication would be included by
        # default
        'rest_framework.authentication.SessionAuthentication',
        'kpi.authentication.BasicAuthentication',
        'kpi.authentication.TokenAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
       'rest_framework.renderers.JSONRenderer',
       'rest_framework.renderers.BrowsableAPIRenderer',
       'kpi.renderers.XMLRenderer',
    ],
    'DEFAULT_VERSIONING_CLASS': 'kpi.versioning.APIVersioning',
    # Cannot be placed in kpi.exceptions.py because of circular imports
    'EXCEPTION_HANDLER': 'kpi.utils.drf_exceptions.custom_exception_handler',
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Default processors per
                # https://docs.djangoproject.com/en/1.8/ref/templates/upgrading/#the-templates-settings
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                # Additional processors
                'kpi.context_processors.custom_password_guidance_text',
                'kpi.context_processors.external_service_tokens',
                'kpi.context_processors.email',
                'kpi.context_processors.sitewide_messages',
                'kpi.context_processors.config',
                'kpi.context_processors.mfa',
                'kpi.context_processors.django_settings',
            ],
            'debug': os.environ.get('TEMPLATE_DEBUG', 'False') == 'True',
        },
    },
]

DEFAULT_SUBMISSIONS_COUNT_NUMBER_OF_DAYS = 31
GOOGLE_ANALYTICS_TOKEN = os.environ.get('GOOGLE_ANALYTICS_TOKEN')
RAVEN_JS_DSN_URL = env.url('RAVEN_JS_DSN', default=None)
RAVEN_JS_DSN = None
if RAVEN_JS_DSN_URL:
    RAVEN_JS_DSN = RAVEN_JS_DSN_URL.geturl()

# replace this with the pointer to the kobocat server, if it exists
KOBOCAT_URL = os.environ.get('KOBOCAT_URL', 'http://kobocat')

# In case server must serve two KoBoCAT domain names (e.g. during a
# domain name transfer), `settings.KOBOCAT_OLD_URL` adds support for
# the domain name.
KOBOCAT_OLD_URL = os.environ.get('KOBOCAT_OLD_URL')

KOBOCAT_INTERNAL_URL = os.environ.get('KOBOCAT_INTERNAL_URL',
                                      'http://kobocat')

KOBOFORM_URL = os.environ.get('KOBOFORM_URL', 'http://kpi')

if 'KOBOCAT_URL' in os.environ:
    DEFAULT_DEPLOYMENT_BACKEND = 'kobocat'
else:
    DEFAULT_DEPLOYMENT_BACKEND = 'mock'


''' Stripe configuration intended for kf.kobotoolbox.org only, tracks usage limit exceptions '''
STRIPE_ENABLED = False
if env.str('STRIPE_TEST_SECRET_KEY', None) or env.str('STRIPE_LIVE_SECRET_KEY', None):
    STRIPE_ENABLED = True


def dj_stripe_request_callback_method():
    # This method exists because dj-stripe's documentation doesn't reflect reality.
    # It claims that DJSTRIPE_SUBSCRIBER_MODEL no longer needs a request callback but
    # this error occurs without it: `DJSTRIPE_SUBSCRIBER_MODEL_REQUEST_CALLBACK must
    # be implemented if a DJSTRIPE_SUBSCRIBER_MODEL is defined`
    # It doesn't need to do anything other than exist
    # https://github.com/dj-stripe/dj-stripe/issues/1900
    pass


DJSTRIPE_SUBSCRIBER_MODEL = "organizations.Organization"
DJSTRIPE_SUBSCRIBER_MODEL_REQUEST_CALLBACK = dj_stripe_request_callback_method
DJSTRIPE_FOREIGN_KEY_TO_FIELD = 'id'
DJSTRIPE_USE_NATIVE_JSONFIELD = True
STRIPE_LIVE_MODE = env.bool('STRIPE_LIVE_MODE', False)
STRIPE_TEST_PUBLIC_KEY = env.str('STRIPE_TEST_PUBLIC_KEY', "pk_test_qliDXQRyVGPWmsYR69tB1NPx00ndTrJfVM")
STRIPE_LIVE_PUBLIC_KEY = "pk_live_7JRQ5elvhnmz4YuWdlSRNmMj00lhvqZz8P"
if STRIPE_ENABLED:
    INSTALLED_APPS += ('djstripe', "kobo.apps.stripe")
    STRIPE_LIVE_SECRET_KEY = env.str('STRIPE_LIVE_SECRET_KEY', None)
    STRIPE_TEST_SECRET_KEY = env.str('STRIPE_TEST_SECRET_KEY', None)
    DJSTRIPE_WEBHOOK_SECRET = env.str('DJSTRIPE_WEBHOOK_SECRET', None)
    DJSTRIPE_WEBHOOK_VALIDATION = env.str('DJSTRIPE_WEBHOOK_VALIDATION', 'verify_signature')
STRIPE_PUBLIC_KEY = STRIPE_LIVE_PUBLIC_KEY if STRIPE_LIVE_MODE else STRIPE_TEST_PUBLIC_KEY


''' Enketo configuration '''
ENKETO_URL = os.environ.get('ENKETO_URL') or os.environ.get('ENKETO_SERVER', 'https://enketo.org')
ENKETO_URL = ENKETO_URL.rstrip('/')  # Remove any trailing slashes
ENKETO_VERSION = os.environ.get('ENKETO_VERSION', 'Legacy').lower()
ENKETO_INTERNAL_URL = os.environ.get('ENKETO_INTERNAL_URL', ENKETO_URL)
ENKETO_INTERNAL_URL = ENKETO_INTERNAL_URL.rstrip('/')  # Remove any trailing slashes

ENKETO_API_TOKEN = os.environ.get('ENKETO_API_TOKEN', 'enketorules')
# http://apidocs.enketo.org/v2/
ENKETO_SURVEY_ENDPOINT = 'api/v2/survey/all'
ENKETO_PREVIEW_ENDPOINT = 'api/v2/survey/preview/iframe'
ENKETO_EDIT_INSTANCE_ENDPOINT = 'api/v2/instance'
ENKETO_VIEW_INSTANCE_ENDPOINT = 'api/v2/instance/view'
ENKETO_FLUSH_CACHE_ENDPOINT = 'api/v2/survey/cache'
# How long to wait before flushing an individual preview from Enketo's cache
ENKETO_FLUSH_CACHED_PREVIEW_DELAY = 1800  # seconds

# Content Security Policy (CSP)
# CSP should "just work" by allowing any possible configuration
# however CSP_EXTRA_DEFAULT_SRC is provided to allow for custom additions
if env.bool("ENABLE_CSP", False):
    MIDDLEWARE.append('csp.middleware.CSPMiddleware')
local_unsafe_allows = [
    "'unsafe-eval'",
    'http://localhost:3000',
    'http://kf.kobo.local:3000',
    'ws://kf.kobo.local:3000'
]
CSP_DEFAULT_SRC = env.list('CSP_EXTRA_DEFAULT_SRC', str, []) + ["'self'", KOBOCAT_URL, ENKETO_URL]
if env.str("FRONTEND_DEV_MODE", None) == "host":
    CSP_DEFAULT_SRC += local_unsafe_allows
CSP_CONNECT_SRC = CSP_DEFAULT_SRC
CSP_SCRIPT_SRC = CSP_DEFAULT_SRC
CSP_STYLE_SRC = CSP_DEFAULT_SRC + ["'unsafe-inline'"]
CSP_IMG_SRC = CSP_DEFAULT_SRC + [
    'data:',
    'https://*.openstreetmap.org',
    'https://*.openstreetmap.fr',  # Humanitarian OpenStreetMap Team
    'https://*.opentopomap.org',
    'https://*.arcgisonline.com'
]
CSP_FRAME_SRC = CSP_DEFAULT_SRC

if GOOGLE_ANALYTICS_TOKEN:
    # Taken from https://developers.google.com/tag-platform/tag-manager/csp#google_analytics_4_google_analytics
    CSP_SCRIPT_SRC.append('https://*.googletagmanager.com')
    CSP_CONNECT_SRC.extend(['https://*.google-analytics.com', 'https://*.analytics.google.com', 'https://*.googletagmanager.com'])
    CSP_IMG_SRC.extend(['https://*.google-analytics.com', 'https://*.googletagmanager.com'])
if RAVEN_JS_DSN_URL and RAVEN_JS_DSN_URL.scheme:
    raven_js_url = RAVEN_JS_DSN_URL.scheme + '://' + RAVEN_JS_DSN_URL.hostname
    CSP_SCRIPT_SRC.append('https://cdn.ravenjs.com')
    CSP_SCRIPT_SRC.append(raven_js_url)
    CSP_CONNECT_SRC.append(raven_js_url)
if STRIPE_ENABLED:
    stripe_domain = "https://js.stripe.com"
    CSP_SCRIPT_SRC.append(stripe_domain)
    CSP_FRAME_SRC.append(stripe_domain)

csp_report_uri = env.url('CSP_REPORT_URI', None)
if csp_report_uri:  # Let environ validate uri, but set as string
    CSP_REPORT_URI = csp_report_uri.geturl()
CSP_REPORT_ONLY = env.bool("CSP_REPORT_ONLY", False)

''' Celery configuration '''
# Celery 4.0 New lowercase settings.
# Uppercase settings can be used when using a PREFIX
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#new-lowercase-settings
# http://docs.celeryproject.org/en/4.0/whatsnew-4.0.html#step-2-update-your-configuration-with-the-new-setting-names

CELERY_TIMEZONE = "UTC"

if os.environ.get('SKIP_CELERY', 'False') == 'True':
    # helpful for certain debugging
    CELERY_TASK_ALWAYS_EAGER = True

# Replace a worker after it completes 7 tasks by default. This allows the OS to
# reclaim memory allocated during large tasks
CELERY_WORKER_MAX_TASKS_PER_CHILD = int(os.environ.get(
    'CELERYD_MAX_TASKS_PER_CHILD', 7))

# Default to a 30-minute soft time limit and a 35-minute hard time limit
CELERY_TASK_TIME_LIMIT = int(
    os.environ.get('CELERYD_TASK_TIME_LIMIT', 2100)  # seconds
)

CELERY_TASK_SOFT_TIME_LIMIT = int(
    os.environ.get('CELERYD_TASK_SOFT_TIME_LIMIT', 1800)  # seconds
)

CELERY_BEAT_SCHEDULE = {
    # Schedule every day at midnight UTC. Can be customized in admin section
    'send-hooks-failures-reports': {
        'task': 'kobo.apps.hook.tasks.failures_reports',
        'schedule': crontab(hour=0, minute=0),
        'options': {'queue': 'kpi_low_priority_queue'}
    },
    # Schedule every 30 minutes
    'trash-bin-garbage-collector': {
        'task': 'kobo.apps.trash_bin.tasks.garbage_collector',
        'schedule': crontab(minute=30),
        'options': {'queue': 'kpi_low_priority_queue'}
    },
    # Schedule every monday at 00:30
    'markdown-images-garbage-collector': {
        'task': 'kobo.apps.markdownx_upload.tasks.remove_unused_markdown_files',
        'schedule': crontab(hour=0, minute=30, day_of_week=0),
        'options': {'queue': 'kpi_low_priority_queue'}
    },
}

CELERY_BROKER_TRANSPORT_OPTIONS = {
    "fanout_patterns": True,
    "fanout_prefix": True,
    # http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#redis-visibility-timeout
    # TODO figure out how to pass `Constance.HOOK_MAX_RETRIES` or `HookLog.get_remaining_seconds()
    # Otherwise hardcode `HOOK_MAX_RETRIES` in Settings
    "visibility_timeout": 60 * (10 ** 3)  # Longest ETA for RestService (seconds)
}

CELERY_TASK_DEFAULT_QUEUE = "kpi_queue"

if 'KOBOCAT_URL' in os.environ:
    SYNC_KOBOCAT_PERMISSIONS = (
        os.environ.get('SYNC_KOBOCAT_PERMISSIONS', 'True') == 'True')

CELERY_BROKER_URL = os.environ.get('KPI_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Increase limits for long-running tasks
# Notes: They are custom name, not part of `CELERY_*` namespace.
CELERY_LONG_RUNNING_TASK_TIME_LIMIT = int(
    os.environ.get('CELERY_LONG_RUNNING_TASK_TIME_LIMIT', 4260)  # seconds
)

CELERY_LONG_RUNNING_TASK_SOFT_TIME_LIMIT = int(
    os.environ.get('CELERY_LONG_RUNNING_TASK_SOFT_TIME_LIMIT', 4200)  # seconds
)

''' Django allauth configuration '''
# User.email should continue to be used instead of the EmailAddress model
ACCOUNT_ADAPTER = 'kobo.apps.accounts.adapter.AccountAdapter'
ACCOUNT_USERNAME_VALIDATORS = 'kobo.apps.accounts.validators.username_validators'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = env.str('ACCOUNT_EMAIL_VERIFICATION', 'mandatory')
ACCOUNT_FORMS = {
    'login': 'kobo.apps.accounts.mfa.forms.MfaLoginForm',
    'signup': 'kobo.apps.accounts.forms.SignupForm',
}
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
ACCOUNT_UNIQUE_EMAIL = False
ACCOUNT_SESSION_REMEMBER = True
SOCIALACCOUNT_EMAIL_VERIFICATION = env.str('SOCIALACCOUNT_EMAIL_VERIFICATION', 'none')
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_FORMS = {
    'signup': 'kobo.apps.accounts.forms.SocialSignupForm',
}
# For SSO, the signup form is prepopulated with the account email
# If set True, the email field in the SSO signup form will be readonly
UNSAFE_SSO_REGISTRATION_EMAIL_DISABLE = env.bool(
    "UNSAFE_SSO_REGISTRATION_EMAIL_DISABLE", False
)

# See https://django-allauth.readthedocs.io/en/latest/configuration.html
# Map env vars to upstream dict values, include exact case. Underscores for delimiter.
# Example: SOCIALACCOUNT_PROVIDERS_provider_SETTING
# Use numbers for arrays such as _1_FOO, _1_BAR, _2_FOO, _2_BAR
SOCIALACCOUNT_PROVIDERS = {}
if MICROSOFT_TENANT := env.str('SOCIALACCOUNT_PROVIDERS_microsoft_TENANT', None):
    SOCIALACCOUNT_PROVIDERS['microsoft'] = {'TENANT': MICROSOFT_TENANT}
# Parse oidc settings as nested dict in array. Example:
# SOCIALACCOUNT_PROVIDERS_openid_connect_SERVERS_0_id: "google" # Must be unique
# SOCIALACCOUNT_PROVIDERS_openid_connect_SERVERS_0_server_url: "https://accounts.google.com"
# SOCIALACCOUNT_PROVIDERS_openid_connect_SERVERS_0_name: "Kobo Google Apps"
# Only OIDC supports multiple providers. For example, to add two Google Apps sign ins - use
# OIDC and assign them a different server number. Do not use the allauth google provider.
oidc_prefix = "SOCIALACCOUNT_PROVIDERS_openid_connect_SERVERS_"
oidc_pattern = re.compile(r"{prefix}\w+".format(prefix=oidc_prefix))
oidc_servers = {}
oidc_nested_keys = ['APP', 'SCOPE', 'AUTH_PARAMS']

for key, value in {
    key.replace(oidc_prefix, ""): val
    for key, val in os.environ.items()
    if oidc_pattern.match(key)
}.items():
    number, setting = key.split("_", 1)
    parsed_key = None
    nested_key = filter(lambda setting_key : setting.startswith(setting_key), oidc_nested_keys)
    nested_key = list(nested_key)
    if len(nested_key):
        _, parsed_key = setting.split(nested_key[0] + "_", 1)
        setting = nested_key[0]
    if number in oidc_servers:
        if parsed_key:
            if setting in oidc_servers[number]:
                if parsed_key.isdigit():
                    oidc_servers[number][setting].append(value)
                else:
                    oidc_servers[number][setting][parsed_key] = value
            else:
                if parsed_key.isdigit():
                    oidc_servers[number][setting] = [value]
                else:
                    oidc_servers[number][setting] = {parsed_key: value}
        else:
            oidc_servers[number][setting] = value
    else:
        if parsed_key:
            if parsed_key.isdigit():
                oidc_servers[number] = {setting: [value]}
            else:
                oidc_servers[number] = {setting: {parsed_key: value}}
        else:
            oidc_servers[number] = {setting: value}
oidc_servers = [x for x in oidc_servers.values()]
SOCIALACCOUNT_PROVIDERS["openid_connect"] = {"SERVERS": oidc_servers}

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'jsapp/compiled/',
        'POLL_INTERVAL': 0.5,  # seconds
        'TIMEOUT': 5,  # seconds
    }
}


''' Email configuration '''
# This setting sets the prefix in the subject line of the account activation email
# The default is the URL of the server. Set to blank to fit the email requirements
ACCOUNT_EMAIL_SUBJECT_PREFIX = ''

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND',
                               'django.core.mail.backends.filebased.EmailBackend')

if EMAIL_BACKEND == 'django.core.mail.backends.filebased.EmailBackend':
    EMAIL_FILE_PATH = os.environ.get(
        'EMAIL_FILE_PATH', os.path.join(BASE_DIR, 'emails'))
    if not os.path.isdir(EMAIL_FILE_PATH):
        os.mkdir(EMAIL_FILE_PATH)

if os.environ.get('EMAIL_HOST'):
    EMAIL_HOST = os.environ.get('EMAIL_HOST')

if os.environ.get('EMAIL_HOST_USER'):
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

if os.environ.get('EMAIL_PORT'):
    EMAIL_PORT = os.environ.get('EMAIL_PORT')

if os.environ.get('EMAIL_USE_TLS'):
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS')


''' AWS configuration (email and storage) '''
if env.str('AWS_ACCESS_KEY_ID', False):
    AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY')
    AWS_SES_REGION_NAME = env.str('AWS_SES_REGION_NAME', None)
    AWS_SES_REGION_ENDPOINT = env.str('AWS_SES_REGION_ENDPOINT', None)

    AWS_S3_SIGNATURE_VERSION = env.str('AWS_S3_SIGNATURE_VERSION', 's3v4')
    # Only set the region if it is present in environment.
    if region := env.str('AWS_S3_REGION_NAME', False):
        AWS_S3_REGION_NAME = region


''' Storage configuration '''
if 'KPI_DEFAULT_FILE_STORAGE' in os.environ:
    # To use S3 storage, set this to `kobo.apps.storage_backends.s3boto3.S3Boto3Storage`
    DEFAULT_FILE_STORAGE = os.environ.get('KPI_DEFAULT_FILE_STORAGE')
    if DEFAULT_FILE_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage':
        # Force usage of custom S3 tellable Storage
        DEFAULT_FILE_STORAGE = 'kobo.apps.storage_backends.s3boto3.S3Boto3Storage'
    if 'KPI_AWS_STORAGE_BUCKET_NAME' in os.environ:
        AWS_STORAGE_BUCKET_NAME = os.environ.get('KPI_AWS_STORAGE_BUCKET_NAME')
        AWS_DEFAULT_ACL = 'private'
        # django-private-storage needs its own S3 configuration
        PRIVATE_STORAGE_CLASS = \
            'private_storage.storage.s3boto3.PrivateS3BotoStorage'
            # NB.........There's intentionally no 3 here! ^
        AWS_PRIVATE_STORAGE_BUCKET_NAME = AWS_STORAGE_BUCKET_NAME
        # Proxy S3 through our application instead of redirecting to bucket
        # URLs with query parameter authentication
        PRIVATE_STORAGE_S3_REVERSE_PROXY = True
    if DEFAULT_FILE_STORAGE.endswith("AzureStorage"):
        PRIVATE_STORAGE_CLASS = \
            'kobo.apps.storage_backends.private_azure_storage.PrivateAzureStorage'
        PRIVATE_STORAGE_S3_REVERSE_PROXY = True  # Yes S3
        AZURE_ACCOUNT_NAME = env.str('AZURE_ACCOUNT_NAME')
        AZURE_ACCOUNT_KEY = env.str('AZURE_ACCOUNT_KEY')
        AZURE_CONTAINER = env.str('AZURE_CONTAINER')
        AZURE_URL_EXPIRATION_SECS = env.int('AZURE_URL_EXPIRATION_SECS', None)


if 'KOBOCAT_DEFAULT_FILE_STORAGE' in os.environ:
    # To use S3 storage, set this to `storages.backends.s3boto3.S3Boto3Storage`
    KOBOCAT_DEFAULT_FILE_STORAGE = os.environ.get('KOBOCAT_DEFAULT_FILE_STORAGE')
    if 'KOBOCAT_AWS_STORAGE_BUCKET_NAME' in os.environ:
        KOBOCAT_AWS_STORAGE_BUCKET_NAME = os.environ.get('KOBOCAT_AWS_STORAGE_BUCKET_NAME')
else:
    KOBOCAT_DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    KOBOCAT_MEDIA_PATH = os.environ.get('KOBOCAT_MEDIA_PATH', '/srv/src/kobocat/media')


# Google Cloud Storage
# Not fully supported as a generic storage backend
GS_BUCKET_NAME = env.str('GS_BUCKET_NAME', None)


''' Django error logging configuration '''
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s' +
                      ' %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'console_logger': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': True
        },
    }
}


################################
# Sentry settings              #
################################
sentry_dsn = env.str('SENTRY_DSN', env.str('RAVEN_DSN', None))
if sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    # All of this is already happening by default!
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.WARNING  # Send warnings as events
    )
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            sentry_logging
        ],
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', 0.01),
        send_default_pii=True
    )


if ENABLE_METRICS := env.bool('ENABLE_METRICS', False):
    MIDDLEWARE.insert(0, 'django_prometheus.middleware.PrometheusBeforeMiddleware')
    MIDDLEWARE.append('django_prometheus.middleware.PrometheusAfterMiddleware')
# Workaround https://github.com/korfuri/django-prometheus/issues/34
PROMETHEUS_EXPORT_MIGRATIONS = False
# https://github.com/korfuri/django-prometheus/blob/master/documentation/exports.md#exporting-metrics-in-a-wsgi-application-with-multiple-processes-per-process
if start_port := env.int('METRICS_START_PORT', None):
    PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(
        start_port, env.int('METRICS_END_PORT', start_port + 10)
    )


''' Try to identify the running codebase for informational purposes '''
# Based upon https://github.com/tblobaum/git-rev/blob/master/index.js
GIT_REV = {}
for git_rev_key, git_command in (
        ('short', ('git', 'rev-parse', '--short', 'HEAD')),
        ('long', ('git', 'rev-parse', 'HEAD')),
        ('branch', ('git', 'rev-parse', '--abbrev-ref', 'HEAD')),
        ('tag', ('git', 'describe', '--exact-match', '--tags')),
):
    try:
        GIT_REV[git_rev_key] = subprocess.check_output(
            git_command, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as e:
        GIT_REV[git_rev_key] = False
if GIT_REV['branch'] == 'HEAD':
    GIT_REV['branch'] = False


'''
Since this project handles user creation, we must handle the model-level
permission assignment that would've been done by KoBoCAT's user post_save
signal handler. Here we record the content types of the models listed in KC's
set_api_permissions_for_user(). Verify that this list still matches that
function if you experience permission-related problems. See
https://github.com/kobotoolbox/kobocat/blob/master/onadata/libs/utils/user_auth.py.
'''
KOBOCAT_DEFAULT_PERMISSION_CONTENT_TYPES = [
    # Each tuple must be (app_label, model_name)
    ('main', 'userprofile'),
    ('logger', 'xform'),
    ('logger', 'note'),
]

# A flag set by unit tests to bypass KoBoCAT user syncing
TESTING = False


''' Auxiliary database configuration '''
if not (MONGO_DB_URL := env.str('MONGO_DB_URL', False)):
    # ToDo Remove all this block by the end of 2022.
    #   Update kobo-install accordingly
    logging.warning(
        '`MONGO_DB_URL` is not found. '
        '`KPI_MONGO_HOST`, `KPI_MONGO_PORT`, `KPI_MONGO_NAME`, '
        '`KPI_MONGO_USER`, `KPI_MONGO_PASS` '
        'are deprecated and will not be supported anymore soon.'
    )

    MONGO_DATABASE = {
        'HOST': os.environ.get('KPI_MONGO_HOST', 'mongo'),
        'PORT': int(os.environ.get('KPI_MONGO_PORT', 27017)),
        'NAME': os.environ.get('KPI_MONGO_NAME', 'formhub'),
        'USER': os.environ.get('KPI_MONGO_USER', ''),
        'PASSWORD': os.environ.get('KPI_MONGO_PASS', '')
    }

    if MONGO_DATABASE.get('USER') and MONGO_DATABASE.get('PASSWORD'):
        MONGO_DB_URL = "mongodb://{user}:{password}@{host}:{port}/{db_name}".\
            format(
                user=MONGO_DATABASE['USER'],
                password=quote_plus(MONGO_DATABASE['PASSWORD']),
                host=MONGO_DATABASE['HOST'],
                port=MONGO_DATABASE['PORT'],
                db_name=MONGO_DATABASE['NAME']
            )
    else:
        MONGO_DB_URL = "mongodb://%(HOST)s:%(PORT)s/%(NAME)s" % MONGO_DATABASE
    mongo_db_name = MONGO_DATABASE['NAME']
else:
    # Attempt to get collection name from the connection string
    # fallback on MONGO_DB_NAME or 'formhub' if it is empty or None or unable to parse
    try:
        mongo_db_name = env.db_url('MONGO_DB_URL').get('NAME') or env.str('MONGO_DB_NAME', 'formhub')
    except ValueError:  # db_url is unable to parse replica set strings
        mongo_db_name = env.str('MONGO_DB_NAME', 'formhub')

mongo_client = MongoClient(
    MONGO_DB_URL, connect=False, journal=True, tz_aware=True
)
MONGO_DB = mongo_client[mongo_db_name]

# If a request or task makes a database query and then times out, the database
# server should not spin forever attempting to fulfill that query.
MONGO_QUERY_TIMEOUT = SYNCHRONOUS_REQUEST_TIME_LIMIT + 5  # seconds
MONGO_CELERY_QUERY_TIMEOUT = CELERY_TASK_TIME_LIMIT + 10  # seconds

SESSION_ENGINE = 'redis_sessions.session'
# django-redis-session expects a dictionary with `url`
redis_session_url = env.cache_url(
    'REDIS_SESSION_URL', default='redis://redis_cache:6380/2'
)
SESSION_REDIS = {
    'url': redis_session_url['LOCATION'],
    'prefix': env.str('REDIS_SESSION_PREFIX', 'session'),
    'socket_timeout': env.int('REDIS_SESSION_SOCKET_TIMEOUT', 1),
}

CACHES = {
    # Set CACHE_URL to override
    'default': env.cache(default='redis://redis_cache:6380/3'),
}

# How long to retain cached responses for kpi endpoints
ENDPOINT_CACHE_DURATION = env.int('ENDPOINT_CACHE_DURATION', 60 * 15)  # 15 minutes

ENV = None

# The maximum size in bytes that a request body may be before a
# SuspiciousOperation (RequestDataTooBig) is raised
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760

# The maximum size (in bytes) that an upload will be before it gets streamed
# to the file system
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

# OpenRosa setting in bytes
OPEN_ROSA_DEFAULT_CONTENT_LENGTH = 10000000

# Expiration time in sec. after which paired data xml file must be regenerated
# Should match KoBoCAT setting
PAIRED_DATA_EXPIRATION = 300  # seconds

# Minimum size (in bytes) of files to allow fast calculation of hashes
# Should match KoBoCAT setting
HASH_BIG_FILE_SIZE_THRESHOLD = 0.5 * 1024 * 1024  # 512 kB

# Chunk size in bytes to read per iteration when hash of a file is calculated
# Should match KoBoCAT setting
HASH_BIG_FILE_CHUNK = 16 * 1024  # 16 kB

# add some mimetype
add_type('application/wkt', '.wkt')
add_type('application/geo+json', '.geojson')

KOBOCAT_MEDIA_URL = f'{KOBOCAT_URL}/media/'
KOBOCAT_THUMBNAILS_SUFFIX_MAPPING = {
    'original': '',
    'large': '_large',
    'medium': '_medium',
    'small': '_small',
}

TRENCH_AUTH = {
    'USER_MFA_MODEL': 'mfa.MfaMethod',
    'USER_ACTIVE_FIELD': 'is_active',
    'BACKUP_CODES_QUANTITY': 5,
    'BACKUP_CODES_LENGTH': 12,  # keep (quantity * length) under 200
    'BACKUP_CODES_CHARACTERS': (string.ascii_letters + string.digits),
    'DEFAULT_VALIDITY_PERIOD': 30,
    'ENCRYPT_BACKUP_CODES': True,
    'SECRET_KEY_LENGTH': 32,
    'CONFIRM_DISABLE_WITH_CODE': True,
    'CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE': True,
    'ALLOW_BACKUP_CODES_REGENERATION': True,
    'MFA_METHODS': {
        'app': {
            'VERBOSE_NAME': 'app',
            'VALIDITY_PERIOD': env.int(
                'MFA_CODE_VALIDITY_PERIOD', 30  # seconds
            ),
            'USES_THIRD_PARTY_CLIENT': True,
            'HANDLER': 'kobo.apps.accounts.mfa.backends.application.ApplicationBackend',
        },
    },
    'CODE_LENGTH': env.int('MFA_CODE_LENGTH', 6),
}

# Session Authentication is supported by default.
MFA_SUPPORTED_AUTH_CLASSES = [
    'kpi.authentication.TokenAuthentication',
]

MINIMUM_DEFAULT_SEARCH_CHARACTERS = 3

# Django 3.2 required settings
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

SERVICE_ACCOUNT = {
    'BACKEND': env.cache_url(
        'SERVICE_ACCOUNT_BACKEND_URL', default='redis://redis_cache:6380/6'
    ),
    'WHITELISTED_HOSTS': env.list('SERVICE_ACCOUNT_WHITELISTED_HOSTS', default=[]),
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'kpi.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'kpi.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'kpi.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'kpi.password_validation.CustomRulesValidator',
    },
    {
        'NAME': 'kpi.password_validation.MostRecentPasswordValidator',
    },
]
