"""
WSGI config for frontend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
import sys
import site

site.addsitedir('/scapl_environment/lib/python3.4/site-packages')
sys.path.append('/opt/scapl/scapl-frontend/frontend')
sys.path.append('/scapl_environment/lib/python3.4/site-packages')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.settings.dev")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
