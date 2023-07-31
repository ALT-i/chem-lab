from rest_framework import serializers

from .models import Lesson

class LessonSerializer(serializers.ModelSerializer):
    tools = serializers.StringRelatedField(many=True)
    substances = serializers.StringRelatedField(many=True)
    class Meta:
        model = Lesson
        fields = '__all__'
