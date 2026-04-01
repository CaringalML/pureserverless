from .base import *

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# API Gateway stage name is part of the URL (e.g. /dev/static/...)
# STATIC_URL must include the stage prefix so {% static %} generates correct URLs
STATIC_URL = f"/{os.environ.get('ENVIRONMENT', 'dev')}/static/"

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
