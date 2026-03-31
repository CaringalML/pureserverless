import os
import django
from django.core.wsgi import get_wsgi_application
from mangum import Mangum

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

django.setup()

application = get_wsgi_application()

# Mangum wraps the Django WSGI app so API Gateway can invoke it as a Lambda handler
handler = Mangum(application, lifespan="off")
