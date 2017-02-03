"""
WSGI config for diris project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

from diris.boot import fix_path
fix_path()

import os
from django.core.wsgi import get_wsgi_application
from djangae.environment import is_production_environment
from djangae.wsgi import DjangaeApplication

from djangae.contrib.consistency.signals import connect_signals
connect_signals()

settings = "diris.settings_live" if is_production_environment() else "diris.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

application = DjangaeApplication(get_wsgi_application())
