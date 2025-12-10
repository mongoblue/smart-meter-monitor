from django.contrib.auth.hashers import check_password
from django.views import View
import json
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import  RefreshToken
from .models import User
from menu.models import Menu
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .serializers import UserListSerializer, UserCreateSerializer
from rest_framework.generics import get_object_or_404
from .models import Role

@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    def post(self,request):
        try:
          if  request.content_type == 'application/json':
                data =json.loads(request.body)
                username = data.get('username')
                password =data.get('password')
          else:
                username = request.POST.get('username')
                password = request.POST.get('password')
          if not username or not password:
                return JsonResponse({'code': 400,'info':'账号密码不能为空'})

          try:
                user = User.objects.get(username = username)
                serializer = UserSerializer(user)
                user_role = user.role
                roles = ','.join([r.name for r in [user_role] if user_role])
                menus = user_role.menus.filter(is_show=True)
                serialized_menus = [
                    {
                        'id': menu.id,
                        'name': menu.name,
                        'type': menu.type,
                        'path': menu.path,
                        'component': menu.component,
                        'icon': menu.icon,
                        'weight': menu.weight,
                        'is_show': menu.is_show,
                        'perms': menu.perms,
                    }
                    for menu in menus
                ]
          except User.DoesNotExist:
              return JsonResponse({'code':401,'info':'账号或密码错误'})
          if not check_password(password,user.password):
              return JsonResponse({'code': 401, 'info': '账号或密码错误'})
          refresh = RefreshToken.for_user(user)
          access = refresh.access_token
          return JsonResponse(
              {
                  'code':200,
                  'token':{
                      'access': str(access),      # 前端使用它访问接口
                      'refresh': str(refresh)},
                  'info':'登录成功',
                  'user':serializer.data,
                  'menu_list':serialized_menus,
                  'roles':roles
              }
          )

        except json.JSONDecodeError:
            return JsonResponse({'code': 400, 'info': '请求格式错误'})

        except Exception as e:
            print(f"登录异常：{e}")
            return JsonResponse({'code': 500, 'info': '服务器内部错误'})

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return JsonResponse({
            'code': 200,
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'avatar': user.avatar.url if user.avatar else '',
                'phone': user.phone,
                'bio': user.bio
            }
        })

    # ------- 保存（POST） -------
    def post(self, request):
        user = request.user
        body = json.loads(request.body)

        # 只允许改这些字段
        allowed = ['email', 'phone', 'bio']
        for key in body:
            if key in allowed:
                setattr(user, key, body[key])
        user.save()

        return JsonResponse({
            'code': 200,
            'info': '已保存',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'avatar': user.avatar.url if user.avatar else '',
                'phone': user.phone,
                'bio': user.bio
            }
        })

class ChangePwdView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        body = json.loads(request.body)
        old_pwd = body.get('old_password')
        new_pwd = body.get('new_password')

        if not old_pwd or not new_pwd:
            return JsonResponse({'code': 400, 'info': '参数缺失'}, status=400)

        user = request.user
        if not user.check_password(old_pwd):
            return JsonResponse({'code': 400, 'info': '旧密码错误'}, status=400)

        user.set_password(new_pwd)
        user.save()
        return JsonResponse({'code': 200, 'info': '密码已更新'})

class UserListCreateView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        ser = UserListSerializer(users, many=True)
        return Response(ser.data)

    def post(self, request):
        ser = UserCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)

class UserToggleActiveView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        user = User.objects.get(pk=pk)
        if user.is_superuser:
            return Response({'info':'管理员不允许禁用'}, status=status.HTTP_403_FORBIDDEN)
        user.is_active = not user.is_active
        user.save()
        return Response({'id': user.id, 'is_active': user.is_active})

class UserDeleteView(APIView):
    permission_classes = [IsAdminUser]  # 仅管理员

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            return Response({"detail": "管理员不允许删除"}, status=status.HTTP_403_FORBIDDEN)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleListView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        qs = Role.objects.all()
        return Response([{'id': r.id, 'name': r.name} for r in qs])