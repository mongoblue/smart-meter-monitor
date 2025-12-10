from django.urls import path
from .views import TrendDayView, TrendMonthView, SaveClientDataView, TodayUsageView, UserUsageView, TrendWeekView, \
    PowerDetailView, BillView, AlertListView

urlpatterns = [
    path("usage/lastest-month", UserUsageView.as_view(), name="user-usage"),
    path('trend/day', TrendDayView.as_view()),
    path('trend/week', TrendWeekView.as_view()),
    path("today-usage/", TodayUsageView.as_view()),
    path('trend/month', TrendMonthView.as_view()),
    path('save-client-data', SaveClientDataView.as_view()),
    path("detail/", PowerDetailView.as_view()),
    path("bill/", BillView.as_view()),
    path("alerts/", AlertListView.as_view()),
]
