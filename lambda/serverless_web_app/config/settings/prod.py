from .base import *

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Prepends /dev to all {% url %} and redirect() calls so links work correctly
# behind the API Gateway stage prefix.
FORCE_SCRIPT_NAME = f"/{os.environ.get('ENVIRONMENT', 'dev')}"
