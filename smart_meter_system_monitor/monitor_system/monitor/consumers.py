import time
import re
from datetime import datetime, date
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.db import models


@sync_to_async
def get_meter(meter_id):
    """异步获取仪表对象"""
    from power.models import Meter
    return Meter.objects.get(meter_id=meter_id)


def make_group_name(meter_id):
    """组名规范化"""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(meter_id))
    return f"meter_{safe}"


# ======================
# 电能计算核心逻辑
# ======================

def process_meter_update(meter, power_w):
    """根据实时功率计算增量电量（kWh）"""
    from power.models import DailyUsage, MonthlyUsage  # 必须放函数内部！

    now_ts = time.time()
    today = date.today()

    # 首次数据直接记录，不计增量
    if meter.last_ts == 0:
        meter.last_ts = now_ts
        meter.last_power_w = power_w
        meter.save()
        return 0

    # 判断是否跨天
    last_day = datetime.fromtimestamp(meter.last_ts).date()
    if last_day != today:
        process_new_day(meter, last_day)

    # 计算时间差（秒）
    delta = now_ts - meter.last_ts
    if delta <= 0:
        return 0

    # ===== 正确的 kWh 计算 =====
    hours = delta / 3600.0          # 秒 → 小时
    power_kw = power_w / 1000.0     # 瓦 → 千瓦
    added_kwh = power_kw * hours    # kW * h = kWh

    # 更新 meter（注意：这里的 energy_today 就是真实的 kWh）
    meter.energy_today += added_kwh
    meter.last_ts = now_ts
    meter.last_power_w = power_w
    meter.save()

    return added_kwh



def process_new_day(meter, last_day):
    from power.models import DailyUsage, MonthlyUsage, HourlyUsage

    # 昨天全部小时的总和
    total = HourlyUsage.objects.filter(
        meter=meter, day=last_day
    ).aggregate(total=models.Sum("kwh"))["total"] or 0

    daily, _ = DailyUsage.objects.get_or_create(
        meter=meter, day=last_day, defaults={"kwh": 0}
    )
    daily.kwh = total
    daily.save()

    # 月总量 = 所有 daily 总和
    month_obj, _ = MonthlyUsage.objects.get_or_create(
        meter=meter, year=last_day.year, month=last_day.month
    )
    month_total = DailyUsage.objects.filter(
        meter=meter,
        day__year=last_day.year,
        day__month=last_day.month
    ).aggregate(total=models.Sum("kwh"))["total"] or 0
    month_obj.kwh = month_total
    month_obj.save()

    # 清空仪表累计
    meter.energy_today = 0
    meter.save()


def record_usage(meter, added_kwh):
    from power.models import HourlyUsage

    now = datetime.now()
    today = now.date()
    hour = now.hour

    hourly, _ = HourlyUsage.objects.get_or_create(
        meter=meter, day=today, hour=hour, defaults={"kwh": 0}
    )
    hourly.kwh += added_kwh
    hourly.save()



class MeterRealtimeConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.meter_id = self.scope["url_route"]["kwargs"]["meter_id"]
        self.group_name = make_group_name(self.meter_id)

        print("WS CONNECT → GROUP =", self.group_name)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def realtime_update(self, event):
        """发送给前端"""
        # print("WS PUSH → FRONTEND:", event["data"])
        await self.send_json(event["data"])

    async def alert_message(self, event):
        """实时异常推送到前端"""
        await self.send_json({
            "type": "alert",
            "alert": event["alert"]
        })
