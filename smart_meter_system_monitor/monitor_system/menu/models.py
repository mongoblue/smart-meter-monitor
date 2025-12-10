from django.db import models
from user.models import Role   # 根据实际应用调整

class Menu(models.Model):
    """标准菜单模型：与 Role 多对多，支持多级/权重/是否显示"""
    TYPE_CHOICES = (
        (1, '目录'),
        (2, '菜单'),
        (3, '按钮'),
    )

    name = models.CharField(verbose_name='名称', max_length=32)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='父级'
    )
    type = models.PositiveSmallIntegerField(
        verbose_name='类型',
        choices=TYPE_CHOICES,
        default=2
    )
    path = models.CharField(verbose_name='路由/URL', max_length=128, blank=True)
    component = models.CharField(verbose_name='前端组件', max_length=128, blank=True)
    icon = models.CharField(verbose_name='图标', max_length=32, blank=True)
    weight = models.PositiveSmallIntegerField(verbose_name='排序', default=100)
    is_show = models.BooleanField(verbose_name='是否显示', default=True)
    perms = models.CharField(verbose_name='权限标识', max_length=128, blank=True)

    # 通过 related_name 实现双向快捷查询：
    #   角色查菜单 → role.menus.all()
    #   菜单查角色 → menu.roles.all()
    roles = models.ManyToManyField(
        Role,
        blank=True,
        verbose_name='可见角色',
        related_name='menus'  # 这里就绑定了
    )

    class Meta:
        ordering = ['weight', 'id']
        verbose_name = '菜单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name