import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import monitor.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitor_system.settings')
django.setup()

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(monitor.routing.websocket_urlpatterns)
    ),
})
