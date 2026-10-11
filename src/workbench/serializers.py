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


class ReactantItemSerializer(serializers.Serializer):
    formula = serializers.CharField(max_length=50)
    volume = serializers.FloatField(required=False, default=0.0)
    molarity = serializers.FloatField(required=False, allow_null=True)
    mass = serializers.FloatField(required=False, allow_null=True)
    moles = serializers.FloatField(required=False, allow_null=True)


class ReactionCalculationSerializer(serializers.Serializer):
    reactants = ReactantItemSerializer(many=True)
    products = serializers.ListField(child=serializers.CharField(max_length=50))
    reaction_type = serializers.CharField(required=False, allow_blank=True, default='neutralization')