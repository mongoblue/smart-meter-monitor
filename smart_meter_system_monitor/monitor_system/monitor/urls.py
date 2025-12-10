from django.urls import path
from .views import RealtimeCollectView

urlpatterns = [
    path("realtime/collect/", RealtimeCollectView.as_view()),
]
