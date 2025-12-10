from django.urls import path,include



urlpatterns = [
    path('user/', include('user.urls')),
    path('menu/', include('menu.urls')),
    path('monitor/', include('monitor.urls')),
    path('power/',include('power.urls')),
    path('system/',include('system.urls'))
]
