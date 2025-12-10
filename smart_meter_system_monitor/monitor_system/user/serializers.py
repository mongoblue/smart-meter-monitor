from .models import User
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Role

User = get_user_model()

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'date_joined']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        required=True,           # 必填
        write_only=True,
        help_text="角色ID"
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'is_active', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role')      # 取出角色
        # 仍显式指定 username，避免顺序 bug
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            is_active=validated_data.get('is_active', True)
        )
        user.role = role                         # 绑定你的自定义角色
        user.save()
        return user
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
