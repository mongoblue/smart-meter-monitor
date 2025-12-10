from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

class Role(models.Model):
    name = models.CharField('角色名称', max_length=50, unique=True)
    code = models.CharField('角色编码', max_length=30, unique=True)
    description = models.CharField('描述', max_length=255, blank=True)
    permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='权限',
        blank=True,
        help_text='该角色拥有的 Django 权限',
    )
    created_at  = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'
        ordering = ['code']

    def __str__(self):
        return f'{self.code}({self.name})'

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True, verbose_name="用户名")
    email = models.EmailField(unique=True, verbose_name="邮箱")
    password = models.CharField(max_length=128, verbose_name="密码")
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="上次登录时间")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="注册时间")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    is_staff = models.BooleanField(default=False, verbose_name="是否是员工")
    is_superuser = models.BooleanField(default=False, verbose_name="是否是超级用户")
    avatar = models.ImageField(
        upload_to='avatar/%Y/%m',
        blank=True,
        null=True,
        verbose_name='头像'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='手机号'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='个人简介'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='所属角色',
        related_name='users'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

