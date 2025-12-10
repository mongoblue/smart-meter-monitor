from django.urls import path
from .views import LoginView, ChangePwdView, UserProfileView, UserListCreateView, UserToggleActiveView, UserDeleteView, \
    RoleListView
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

urlpatterns = [
    path('login/', LoginView.as_view(),name='login'),
    path('profile/', UserProfileView.as_view()),  # GET + POST
    path('changePwd/', ChangePwdView.as_view()),  # POST
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', UserListCreateView.as_view()),  # GET 列表 / POST 新建
    path('<int:pk>/toggle/', UserToggleActiveView.as_view()),  # POST 启用/禁用
    path('<int:pk>/delete/', UserDeleteView.as_view()),
    path('role/', RoleListView.as_view()),
]
