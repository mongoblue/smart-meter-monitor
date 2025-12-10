from power.models import Meter, DailyUsage, MonthlyUsage, HourlyUsage
from datetime import datetime, date
from django.db import models
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .consumers import process_meter_update, make_group_name, record_usage
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from power.models import Meter
from monitor.consumers import process_meter_update, record_usage, make_group_name
from monitor.utils import detect_realtime_alerts

@csrf_exempt
def realtime_collect(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        meter_id = body.get("meter_id")
        payload = body.get("data", {})
        total = payload.get("_TOTAL", {})

        if not meter_id or not total:
            return JsonResponse({"error": "missing fields"}, status=400)

        # 获取电表
        meter, _ = Meter.objects.get_or_create(meter_id=meter_id)

        power_w = float(total.get("power_w", 0))

        # 写入能耗模型
        added = process_meter_update(meter, power_w)
        if added > 0:
            record_usage(meter, added)

        group_name = make_group_name(meter_id)
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "realtime_update",
                "data": body
            }
        )

        return JsonResponse({"ok": True})

    except Exception as e:
        print("collect error:", e)
        return JsonResponse({"error": str(e)}, status=500)

class RealtimeCollectView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        meter_id = request.data.get("meter_id")
        payload = request.data.get("data", {})

        if not meter_id or "_TOTAL" not in payload:
            return Response({"error": "invalid payload"}, status=400)

        total = payload["_TOTAL"]
        power_w = float(total.get("power_w", 0))
        voltage_v = float(total.get("voltage_v", 0))

        # 获取电表
        meter, _ = Meter.objects.get_or_create(meter_id=meter_id)
        last_power = meter.last_power_w
        added = process_meter_update(meter, power_w)
        detect_realtime_alerts(
            meter=meter,
            total_power_w=power_w,
            voltage_v=voltage_v,
            last_power=last_power
        )

        if added > 0:
            record_usage(meter, added)

        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            make_group_name(meter_id),
            {
                "type": "realtime.update",
                "data": {
                    "meter_id": meter_id,
                    "power_w": power_w,
                    "voltage_v": voltage_v,
                    "current_a": total.get("current_a", 0),
                    "devices": payload
                }
            }
        )

        return Response({"ok": True})


