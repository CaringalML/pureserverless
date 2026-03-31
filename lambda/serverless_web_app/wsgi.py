import os
import django
from django.core.wsgi import get_wsgi_application
from mangum import Mangum

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

django.setup()

application = get_wsgi_application()

handler = Mangum(application, lifespan="off")
