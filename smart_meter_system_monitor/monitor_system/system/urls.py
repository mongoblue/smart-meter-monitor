from django.urls import path
from .views import OptionListView, OptionUpdateView

urlpatterns = [
    path('', OptionListView.as_view()),
    path('<int:pk>/', OptionUpdateView.as_view()),
]