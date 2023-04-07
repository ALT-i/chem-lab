from rest_framework import serializers

from .models import Substance, Apparatus

class SubstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Substance
        fields = '__all__'

class ApparatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apparatus
        fields = '__all__'