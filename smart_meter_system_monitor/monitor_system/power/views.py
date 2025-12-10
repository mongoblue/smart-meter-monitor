import time
import calendar
from datetime import date, datetime, timedelta
from django.core.paginator import Paginator
from django.db import models
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import (Meter, DailyUsage, MonthlyUsage, ClientMeterSnapshot, HourlyUsage, RealtimeAlert)
from .serializers import MonthlyUsageSerializer

def get_user_meter(request):
    meter_id = request.GET.get("meter_id")
    qs = request.user.meters  # 通过 related_name="meters"

    if meter_id:
        meter = qs.filter(meter_id=meter_id).first()
        if not meter:
            raise PermissionDenied("无权访问该电表")
        return meter

    # 未指定 meter_id → 默认使用第一个
    meter = qs.first()
    if not meter:
        raise PermissionDenied("用户未绑定任何电表")
    return meter


def process_meter_update(meter, power_w):
    now_ts = time.time()
    now_day = date.today()

    if meter.last_ts == 0:
        meter.last_ts = now_ts
        meter.last_power_w = power_w
        meter.save()
        return 0

    # ------ ⭐ 检查是否跨天了 -------
    last_day = datetime.fromtimestamp(meter.last_ts).date()
    if last_day != now_day:
        process_new_day(meter, last_day)

    # ------ 正常增量计算 -------
    delta = now_ts - meter.last_ts
    if delta <= 0:
        return 0

    added_kwh = power_w * (delta / 3600.0)

    meter.energy_today += added_kwh
    meter.last_ts = now_ts
    meter.last_power_w = power_w
    meter.save()

    return added_kwh

def process_new_day(meter, last_day):
    """处理跨天事件：将 meter.energy_today 写入昨日的 DailyUsage"""

    # ---- 写入昨日 DailyUsage ----
    daily, _ = DailyUsage.objects.get_or_create(
        meter=meter,
        day=last_day,
        defaults={"kwh": 0}
    )
    daily.kwh = meter.energy_today
    daily.save()

    # ---- 写 MonthlyUsage ----
    month_obj, _ = MonthlyUsage.objects.get_or_create(
        meter=meter,
        year=last_day.year,
        month=last_day.month,
        defaults={"kwh": 0}
    )

    total_month = (
        DailyUsage.objects.filter(
            meter=meter,
            day__year=last_day.year,
            day__month=last_day.month
        ).aggregate(total=models.Sum("kwh"))["total"] or 0
    )

    month_obj.kwh = total_month
    month_obj.save()

    # ---- 第二天清零 ----
    meter.energy_today = 0
    meter.save()


def update_usages(meter):
    today = date.today()

    # Daily
    daily, _ = DailyUsage.objects.get_or_create(
        meter=meter,
        day=today,
        defaults={"kwh": 0}
    )
    daily.kwh = meter.energy_today
    daily.save()

    # Monthly
    month_obj, _ = MonthlyUsage.objects.get_or_create(
        meter=meter,
        year=today.year,
        month=today.month,
        defaults={"kwh": 0}
    )

    this_month_kwh = (
        DailyUsage.objects
        .filter(meter=meter, day__year=today.year, day__month=today.month)
        .aggregate(total=models.Sum("kwh"))["total"] or 0
    )

    month_obj.kwh = this_month_kwh
    month_obj.save()


class TodayUsageView(APIView):
    def get(self, request):
        meter_id = request.GET.get("meter_id")
        meter = Meter.objects.get(meter_id=meter_id)

        return Response({
            "meter_id": meter_id,
            "kwh_today": meter.energy_today
        })


class TrendDayView(APIView):
    def get(self, request):
        meter_id = request.GET.get("meter_id")
        meter = Meter.objects.filter(meter_id=meter_id).first()

        if not meter:
            return Response({"error": "meter not found"}, status=404)

        date_str = request.GET.get("date")
        if date_str:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            day = date.today()

        # ⭐ 查询当天每小时的用电量
        hourly_qs = HourlyUsage.objects.filter(
            meter=meter,
            day=day
        )

        # key = hour, value = kwh
        usage_map = {h.hour: h.kwh for h in hourly_qs}

        # 24小时 x/y
        x = [f"{h:02d}:00" for h in range(24)]
        y = [round(usage_map.get(h, 0), 4) for h in range(24)]

        return Response({
            "meter_id": meter_id,
            "x": x,
            "y": y
        })

class TrendWeekView(APIView):
    def get(self, request):
        meter_id = request.GET.get("meter_id")
        meter = Meter.objects.filter(meter_id=meter_id).first()

        if not meter:
            return Response({"error": "meter not found"}, status=404)

        end_str = request.GET.get("end")

        if end_str:
            end_day = datetime.strptime(end_str, "%Y-%m-%d").date()
        else:
            end_day = date.today()

        start_day = end_day - timedelta(days=6)

        qs = DailyUsage.objects.filter(
            meter=meter,
            day__range=(start_day, end_day)
        )

        usage_map = {d.day: d.kwh for d in qs}

        x = []
        y = []

        curr = start_day
        while curr <= end_day:
            x.append(curr.strftime("%Y-%m-%d"))
            y.append(round(usage_map.get(curr, 0), 4))
            curr += timedelta(days=1)

        return Response({
            "meter_id": meter_id,
            "x": x,
            "y": y
        })


class TrendMonthView(APIView):
    def get(self, request):
        meter_id = request.GET.get("meter_id")
        year = request.GET.get("year")
        month = request.GET.get("month")

        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month
        else:
            year = int(year)
            month = int(month)

        meter = Meter.objects.filter(meter_id=meter_id).first()
        if not meter:
            return Response({"error": "meter not found"}, status=404)

        days_in_month = calendar.monthrange(year, month)[1]

        qs = DailyUsage.objects.filter(
            meter=meter,
            day__year=year,
            day__month=month
        )

        usage_map = {d.day.day: d.kwh for d in qs}

        x = []
        y = []

        for d in range(1, days_in_month + 1):
            dt = date(year, month, d)
            x.append(dt.strftime("%Y-%m-%d"))
            y.append(round(usage_map.get(d, 0), 4))

        return Response({
            "meter_id": meter_id,
            "x": x,
            "y": y
        })


class UserUsageView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MonthlyUsageSerializer

    def get_queryset(self):
        user = self.request.user
        meter = Meter.objects.filter(user=user).first()
        if not meter:
            return MonthlyUsage.objects.none()

        return (
            MonthlyUsage.objects
            .filter(meter=meter)
            .order_by("-year", "-month")[:12]
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        result = []
        for item in queryset:
            result.append({
                "year": item.year,
                "month": item.month,
                "kwh": float(item.kwh),
                "money": float(item.kwh) * 1.5
            })

        return Response(result)

#  前端快照（持久化）
# -------------------------------
class SaveClientDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        meter_id = request.data.get("meter_id")
        if not meter_id:
            return Response({"error": "meter_id missing"}, status=400)

        # 查找电表
        meter = Meter.objects.filter(meter_id=meter_id).first()
        if not meter:
            meter = Meter.objects.create(meter_id=meter_id)

        latest = request.data.get("latest") or {}
        series = request.data.get("realtime_series") or []
        trend = request.data.get("trend") or {}

        snapshot, created = ClientMeterSnapshot.objects.get_or_create(
            user=request.user,
            meter=meter
        )

        snapshot.latest_json = latest
        snapshot.realtime_series = series
        snapshot.trend_day = trend.get("day") or {}
        snapshot.trend_week = trend.get("week") or {}
        snapshot.trend_month = trend.get("month") or {}
        snapshot.save()

        return Response({
            "ok": True,
            "meter_id": meter_id,
            "created": created,
            "updated_at": now().isoformat()
        })

class PowerDetailView(APIView):
    def get(self, request):
        # 1) 获取当前用户允许访问的电表
        meter = get_user_meter(request)

        # 2) 获取查询的日期，没有则默认今天
        day = request.GET.get("date")
        if day:
            try:
                day = datetime.strptime(day, "%Y-%m-%d").date()
            except:
                return Response({"error": "日期格式错误，应为 YYYY-MM-DD"}, status=400)
        else:
            day = date.today()

        # 3) 查询该天所有小时用电数据
        qs = HourlyUsage.objects.filter(
            meter=meter,
            day=day
        ).order_by("hour")

        data = [{
            "time": f"{u.hour:02d}:00",
            "kwh": round(u.kwh, 4)
        } for u in qs]

        return Response({
            "meter_id": meter.meter_id,
            "date": day,
            "data": data,

        })



class BillView(APIView):
    def get(self, request):
        meter = get_user_meter(request)
        if not meter:
            return Response({"error": "No meter found"}, status=404)

        qs = MonthlyUsage.objects.filter(
            meter=meter
        ).order_by("-year", "-month")

        bills = []
        for m in qs:
            price = round(m.kwh * 0.65, 2)

            bills.append({
                "year": m.year,
                "month": m.month,
                "kwh": round(m.kwh, 4),
                "cost": price,
            })

        return Response({"bills": bills})

class AlertPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200

class AlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 分页参数
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))

        # 筛选参数
        alert_type = request.GET.get("type")
        meter_id = request.GET.get("meter_id")

        # 基础 QuerySet
        qs = RealtimeAlert.objects.all().order_by("-ts")

        # 按电表过滤
        if meter_id:
            qs = qs.filter(meter__meter_id=meter_id)
        else:
            # 用户可能拥有多个电表
            user_meters = request.user.meters.all()
            if not user_meters.exists():
                return Response({"count": 0, "results": []})

            qs = qs.filter(meter__in=user_meters)

        # 按类型过滤
        if alert_type:
            qs = qs.filter(type=alert_type)

        # 分页
        paginator = Paginator(qs, page_size)
        page_obj = paginator.get_page(page)

        # 结果
        results = [
            {
                "ts": a.ts.strftime("%Y-%m-%d %H:%M:%S"),
                "meter_id": a.meter.meter_id,
                "type": a.type,
                "desc": a.desc,
            }
            for a in page_obj.object_list
        ]

        return Response({
            "count": paginator.count,
            "results": results
        })