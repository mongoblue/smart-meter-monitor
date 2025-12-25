import os
import time
import calendar
from datetime import date, datetime, timedelta
from django.core.paginator import Paginator
from django.db import models
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import (Meter, DailyUsage, MonthlyUsage, ClientMeterSnapshot, HourlyUsage, RealtimeAlert)
from .serializers import MonthlyUsageSerializer
from system.utils import get_float_option
from django.http import HttpResponse
from rest_framework.views import APIView
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import os
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
from django.conf import settings
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .models import MonthlyUsage


# ========== 1. 注册中文字体（仿宋） ==========
FONT_PATH = os.path.join(
    settings.BASE_DIR, 'static', 'fonts', 'simfang.ttf'
)
pdfmetrics.registerFont(TTFont('Chinese', FONT_PATH))


# ========== 2. matplotlib 使用同一字体 ==========
font_prop = font_manager.FontProperties(fname=FONT_PATH)
rcParams['font.family'] = font_prop.get_name()
rcParams['axes.unicode_minus'] = False

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

    # ------  检查是否跨天了 -------
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

        total = sum(y)
        avg = total / 24 if total else 0

        peak_kwh = max(y)
        peak_hour = x[y.index(peak_kwh)]

        valley_kwh = min(y)
        valley_hour = x[y.index(valley_kwh)]

        night_kwh = sum(y[0:6])
        night_ratio = night_kwh / total if total else 0

        return Response({
            "meter_id": meter_id,
            "x": x,
            "y": y,
            "analysis": {
                "total_kwh": round(total, 4),
                "avg_kwh": round(avg, 4),
                "peak_hour": peak_hour,
                "peak_kwh": round(peak_kwh, 4),
                "valley_hour": valley_hour,
                "night_ratio": round(night_ratio, 4),
            }
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

        total_kwh = round(sum(y), 4)
        avg_daily_kwh = round(total_kwh / 7, 4) if total_kwh else 0

        max_kwh = max(y)
        min_kwh = min(y)

        max_day = x[y.index(max_kwh)]
        min_day = x[y.index(min_kwh)]

        fluctuation = round(max_kwh - min_kwh, 4)

        workday_values = []
        weekend_values = []

        curr = start_day
        for v in y:
            if curr.weekday() < 5:
                workday_values.append(v)
            else:
                weekend_values.append(v)
            curr += timedelta(days=1)

        workday_avg = round(
            sum(workday_values) / len(workday_values), 4
        ) if workday_values else 0

        weekend_avg = round(
            sum(weekend_values) / len(weekend_values), 4
        ) if weekend_values else 0

        return Response({
            "meter_id": meter_id,
            "x": x,
            "y": y,
            "analysis": {
                "total_kwh": total_kwh,
                "avg_daily_kwh": avg_daily_kwh,
                "max_day": max_day,
                "max_kwh": round(max_kwh, 4),
                "min_day": min_day,
                "min_kwh": round(min_kwh, 4),
                "fluctuation": fluctuation,
                "workday_avg": workday_avg,
                "weekend_avg": weekend_avg,
            }
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

        total_kwh = round(sum(y), 4)
        avg_daily_kwh = round(
            total_kwh / days_in_month, 4
        ) if total_kwh else 0

        max_kwh = max(y)
        min_kwh = min(y)

        max_day = x[y.index(max_kwh)]
        min_day = x[y.index(min_kwh)]

        # top 3 days
        top3_idx = sorted(
            range(len(y)),
            key=lambda i: y[i],
            reverse=True
        )[:3]

        top3_days = [
            {"day": x[i], "kwh": round(y[i], 4)}
            for i in top3_idx
        ]

        mid = days_in_month // 2
        first_half_kwh = round(sum(y[:mid]), 4)
        second_half_kwh = round(sum(y[mid:]), 4)

        half_compare = round(
            second_half_kwh - first_half_kwh, 4
        )

        return Response({
            "meter_id": meter_id,
            "x": x,
            "y": y,
            "analysis": {
                "total_kwh": total_kwh,
                "avg_daily_kwh": avg_daily_kwh,
                "max_day": max_day,
                "max_kwh": round(max_kwh, 4),
                "min_day": min_day,
                "min_kwh": round(min_kwh, 4),
                "top3_days": top3_days,
                "first_half_kwh": first_half_kwh,
                "second_half_kwh": second_half_kwh,
                "half_compare": half_compare,
            }
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
                "money": float(item.kwh) * 0.65
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


class PowerReportExportView(APIView):
    def get(self, request):
        meter = request.user.meters.first()
        months = (
            MonthlyUsage.objects
            .filter(meter=meter)
            .order_by('year', 'month')[:12]
        )

        # ========= 3. 统计数据 =========
        total_kwh = sum(m.kwh for m in months)
        price = 0.65
        total_money = total_kwh * price
        avg_daily = total_kwh / 30 if total_kwh else 0
        avg_month = total_kwh / len(months) if months else 0

        # ========= 4. 生成趋势图 =========
        labels = [f"{m.year}-{m.month:02d}" for m in months]
        values = [m.kwh for m in months]

        fig, ax = plt.subplots(figsize=(8, 4))

        if len(values) < 2:
            ax.scatter(labels, values, s=80)
            ax.set_title("当前月用电量", fontproperties=font_prop)
        else:
            ax.plot(labels, values, marker='o', linewidth=2)
            ax.set_title("最近 12 个月用电量趋势", fontproperties=font_prop)

        ax.set_xlabel("月份", fontproperties=font_prop)
        ax.set_ylabel("用电量 (kWh)", fontproperties=font_prop)
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.xticks(rotation=45)

        img_buf = BytesIO()
        fig.savefig(img_buf, dpi=150, bbox_inches='tight')
        img_buf.seek(0)
        plt.close(fig)

        # ========= 5. PDF 初始化 =========
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="家庭智能用电分析报告.pdf"'

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            topMargin=2 * cm,
            bottomMargin=2 * cm
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='TitleCN', fontName='Chinese',
            fontSize=20, alignment=1, spaceAfter=20
        ))
        styles.add(ParagraphStyle(
            name='NormalCN', fontName='Chinese',
            fontSize=12, leading=18
        ))
        styles.add(ParagraphStyle(
            name='HeadingCN', fontName='Chinese',
            fontSize=14, spaceBefore=12, spaceAfter=8
        ))

        story = []

        # ========= 6. 封面 / 标题 =========
        story.append(Paragraph("家庭智能用电分析报告", styles['TitleCN']))
        story.append(Spacer(1, 30))

        story.append(Paragraph(
            "本报告基于智能电表采集的历史用电数据，"
            "对家庭用电情况进行统计分析与趋势评估，"
            "为用户提供科学的用电决策参考。",
            styles['NormalCN']
        ))
        story.append(PageBreak())

        # ========= 7. 基本信息 =========
        story.append(Paragraph("一、基本用电信息", styles['HeadingCN']))

        info_table = Table([
            ["电表编号", meter.meter_id],
            ["统计周期", "最近 12 个月"],
            ["总用电量", f"{total_kwh:.2f} kWh"],
            ["总电费", f"¥{total_money:.2f}"],
            ["日均用电量", f"{avg_daily:.2f} kWh"],
            ["月均用电量", f"{avg_month:.2f} kWh"],
        ], colWidths=[5 * cm, 9 * cm])

        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ]))

        story.append(info_table)
        story.append(Spacer(1, 20))

        # ========= 8. 趋势分析 =========
        story.append(Paragraph("二、用电趋势分析", styles['HeadingCN']))
        story.append(RLImage(img_buf, width=15 * cm, height=8 * cm))
        story.append(Spacer(1, 12))

        story.append(Paragraph(
            "从用电趋势图可以看出，家庭整体用电情况较为稳定，"
            "未出现明显的异常峰值，说明家庭用电行为相对规律。",
            styles['NormalCN']
        ))

        # ========= 9. 节能建议 =========
        story.append(Spacer(1, 20))
        story.append(Paragraph("三、节能建议", styles['HeadingCN']))

        tips = [
            "合理安排大功率电器的使用时间，避免集中使用。",
            "选用高能效等级家用电器以降低长期用电成本。",
            "夏季空调温度建议不低于 26℃，冬季不高于 20℃。",
            "外出或长期不用时，及时关闭待机电器。"
        ]

        for tip in tips:
            story.append(Paragraph(f"• {tip}", styles['NormalCN']))
            story.append(Spacer(1, 6))

        # ========= 10. 系统说明 =========
        story.append(Spacer(1, 20))
        story.append(Paragraph("四、系统说明", styles['HeadingCN']))
        story.append(Paragraph(
            "本分析报告由家庭智能用电监测系统自动生成，"
            "可辅助用户了解用电行为并优化用电策略。",
            styles['NormalCN']
        ))

        doc.build(story)
        return response