from rest_framework import serializers
from .models import Count

class CountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Count
        fields = ('id', 'name', 'count')