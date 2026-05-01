"""
ASGI config for agende_enginelab project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.a.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agende_enginelab.settings')

application = get_asgi_application()
