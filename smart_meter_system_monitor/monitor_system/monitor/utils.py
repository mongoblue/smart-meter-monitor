import re
from power.models import RealtimeAlert
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from monitor.consumers import make_group_name

def make_group_name(meter_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(meter_id))[:80]
    return f"meter_{safe}"

def detect_realtime_alerts(meter, total_power_w, voltage_v, last_power=None):
    alerts = []

    # 功率过高
    if total_power_w > 8000:
        alerts.append(("high_power", f"功率过高：{total_power_w:.2f} W"))

    # 用电突增
    if last_power and last_power > 1000:
        if (total_power_w - last_power) / last_power > 1:
            alerts.append(("sudden_usage", f"用电突增：{last_power:.2f} → {total_power_w:.2f} W"))

    # 电压异常
    if voltage_v < 200 or voltage_v > 250:
        alerts.append(("voltage_issue", f"电压异常：{voltage_v:.2f} V"))

    # 波动异常
    if last_power:
        if abs(total_power_w - last_power) > 2000:
            alerts.append(("fluctuation", f"功率波动异常：差值 {abs(total_power_w - last_power):.2f} W"))

    # 写入数据库 + 推送 WebSocket
    layer = get_channel_layer()
    group = make_group_name(meter.meter_id)

    for t, desc in alerts:
        RealtimeAlert.objects.create(
            meter=meter,
            type=t,
            desc=desc
        )

        # 推送 WebSocket
        async_to_sync(layer.group_send)(
            group,
            {
                "type": "alert_message",  # Consumer 中需要实现
                "alert": {
                    "type": t,
                    "desc": desc,
                    "meter_id": meter.meter_id,
                }
            }
        )

    return alerts
