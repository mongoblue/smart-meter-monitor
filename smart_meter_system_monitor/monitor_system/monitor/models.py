from django.db import models
from power.models import Meter
from django.conf import settings
User = settings.AUTH_USER_MODEL

class RealtimeUsage(models.Model):
    """
    实时功率备份（可选）。
    主实时数据放 Redis，这里只做部分落盘记录，方便后续趋势分析。
    """
    meter = models.ForeignKey(
        Meter,
        on_delete=models.CASCADE,
        related_name='realtime_records',
        verbose_name='电表'
    )
    timestamp = models.DateTimeField('时间', auto_now_add=True)
    power_usage = models.IntegerField('总功率(W)')

    class Meta:
        db_table = 'realtime_usage'
        ordering = ['-timestamp']
        verbose_name = '实时用电记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.meter.meter_id} - {self.power_usage}W @ {self.timestamp}'

