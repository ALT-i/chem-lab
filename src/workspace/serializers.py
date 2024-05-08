from rest_framework import serializers

from ..workbench.serializers import SubstanceSerializer, ApparatusSerializer
from .models import Lesson, Reaction

class LessonSerializer(serializers.ModelSerializer):
    tools = ApparatusSerializer(many=True)
    substances = SubstanceSerializer(many=True)
    instructor = serializers.StringRelatedField()
    video_file = serializers.FileField()
    image = serializers.FileField()
    class Meta:
        model = Lesson
        fields = '__all__'



class ReactionSerializer(serializers.ModelSerializer):
    substance = serializers.ListField(child=serializers.CharField())
    volume = serializers.ListField(child=serializers.FloatField())
    class Meta:
        model = Reaction
        fields = ['substance', 'volume']