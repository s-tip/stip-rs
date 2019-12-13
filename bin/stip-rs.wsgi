#!/usr/bin/env python3
import os
import sys
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ctirs.settings")
application = get_wsgi_application()
