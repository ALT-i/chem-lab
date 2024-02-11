from rest_framework import serializers

from .models import Lesson, Reaction

class LessonSerializer(serializers.ModelSerializer):
    tools = serializers.StringRelatedField(many=True)
    substances = serializers.StringRelatedField(many=True)
    instructor = serializers.StringRelatedField()
    video_file = serializers.FileField()
    class Meta:
        model = Lesson
        fields = '__all__'



class ReactionSerializer(serializers.ModelSerializer):
    substance = serializers.ListField(child=serializers.CharField())
    volume = serializers.ListField(child=serializers.FloatField())
    class Meta:
        model = Reaction
        fields = ['substance', 'volume']