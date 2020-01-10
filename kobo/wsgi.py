"""
WSGI config for kobo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

# import sys
# # sys.setdefaultencoding() does not exist, here!
# reload(sys)  # Reload does the trick!
# sys.setdefaultencoding('UTF8')

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kobo.settings.prod")
from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise



application = get_wsgi_application()
application = DjangoWhiteNoise(application)
