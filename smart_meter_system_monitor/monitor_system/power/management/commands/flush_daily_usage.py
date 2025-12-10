# power/management/commands/flush_daily_usage.py
import re
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from redis import Redis
from power.models import Meter, DailyUsage

r = Redis(host="127.0.0.1", port=6379, decode_responses=True)

class Command(BaseCommand):
    help = "Flush redis minute buckets into DailyUsage (today & yesterday by default)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=2, help="how many days back (default 2)")

    def handle(self, *args, **opts):
        days = int(opts["days"])
        today = timezone.localdate()

        for meter in Meter.objects.all():
            for i in range(days):
                d = today - timedelta(days=i)
                prefix = d.strftime("%Y%m%d")
                pattern = f"agg:min:{meter.meter_id}:{prefix}????"

                total = 0.0
                for key in r.scan_iter(match=pattern, count=500):
                    total += float(r.hget(key, "kwh") or 0.0)

                DailyUsage.objects.update_or_create(
                    meter=meter,
                    day=d,
                    defaults={"kwh": Decimal(str(round(total, 6)))}
                )

        self.stdout.write(self.style.SUCCESS("flush_daily_usage done"))
