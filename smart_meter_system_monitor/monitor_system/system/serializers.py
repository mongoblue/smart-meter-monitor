from rest_framework import serializers
from .models import SystemOption

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemOption
        fields = '__all__'