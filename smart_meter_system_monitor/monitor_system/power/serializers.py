from .models import MonthlyUsage
from rest_framework import serializers
from power.models import RealtimeAlert

class MonthlyUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyUsage
        fields = ('year', 'month', 'kwh', 'money')

class RealtimeAlertSerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source="meter.meter_id")

    class Meta:
        model = RealtimeAlert
        fields = ["id", "meter_id", "type", "desc", "ts"]
