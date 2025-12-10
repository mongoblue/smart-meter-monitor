from django.db import models

class Meter(models.Model):
    user = models.ForeignKey(
        "user.User",
        null=True, blank=True,  # 先允许为空，防止迁移报错
        on_delete=models.CASCADE,
        related_name="meters"
    )
    meter_id = models.CharField(max_length=50, unique=True)
    last_ts = models.FloatField(default=0)
    energy_today = models.FloatField(default=0)
    last_power_w = models.FloatField(default=0)

    def __str__(self):
        return self.meter_id


class DailyUsage(models.Model):
    meter = models.ForeignKey("Meter", on_delete=models.CASCADE)
    day = models.DateField()
    kwh = models.FloatField(default=0)

    class Meta:
        unique_together = ("meter", "day")


class MonthlyUsage(models.Model):
    meter = models.ForeignKey("Meter", on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    kwh = models.FloatField(default=0)

    class Meta:
        unique_together = ("meter", "year", "month")

    def __str__(self):
        return f"{self.year}-{self.month} Meter={self.meter.meter_id}"

class HourlyUsage(models.Model):
    meter = models.ForeignKey("Meter", on_delete=models.CASCADE)
    day = models.DateField()
    hour = models.IntegerField()  # 0~23
    kwh = models.FloatField(default=0)

    class Meta:
        unique_together = ("meter", "day", "hour")


class ClientMeterSnapshot(models.Model):
    user = models.ForeignKey(
        "user.User",                         # ★ 不会出错
        on_delete=models.CASCADE,
        related_name="client_meter_snapshots"
    )
    meter = models.ForeignKey(
        "power.Meter",
        on_delete=models.CASCADE,
        related_name="client_snapshots"
    )
    latest_json = models.JSONField(default=dict, blank=True)
    realtime_series = models.JSONField(default=list, blank=True)
    trend_day = models.JSONField(default=dict, blank=True)
    trend_week = models.JSONField(default=dict, blank=True)
    trend_month = models.JSONField(default=dict, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "client_meter_snapshot"
        unique_together = ("user", "meter")
        verbose_name = "前端电表快照"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user} - {self.meter.meter_id}"

class RealtimeAlert(models.Model):
    ALERT_TYPES = (
        ("high_power", "功率过高"),
        ("sudden_usage", "用电突增"),
        ("voltage_issue", "电压异常"),
        ("fluctuation", "功率波动异常"),
    )

    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    ts = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50, choices=ALERT_TYPES)
    desc = models.TextField()

    def __str__(self):
        return f"[{self.get_type_display()}] {self.ts}"

class Bill(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    total_kwh = models.FloatField(default=0)
    total_fee = models.FloatField(default=0)

    generate_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("meter", "year", "month")

