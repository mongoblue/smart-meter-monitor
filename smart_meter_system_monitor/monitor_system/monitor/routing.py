from django.urls import re_path
from .consumers import MeterRealtimeConsumer

websocket_urlpatterns = [
    re_path(r"^/?ws/monitor/meter/(?P<meter_id>[\w.-]+)/?$", MeterRealtimeConsumer.as_asgi()),
]
