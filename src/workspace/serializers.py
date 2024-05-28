from rest_framework import serializers

from ..workbench.serializers import SubstanceSerializer, ApparatusSerializer
from .models import Lesson, Reaction
from src.users.serializers import UserSerializer

class LessonSerializer(serializers.ModelSerializer):
    tools = ApparatusSerializer(many=True, read_only=True)
    substances = SubstanceSerializer(many=True, read_only=True)
    instructor = UserSerializer(read_only = True)
    video_file = serializers.CharField(required=False, allow_blank=True)
    image = serializers.CharField(required=False, allow_blank=True)
    
    # In the case of add a .create() function method 
    # instructor_id = serializers.PrimaryKeyRelatedField(queryset = User.objects.all(), read_only=False, write_only = True) 
    class Meta:
        model = Lesson
        fields = '__all__'
        
    # Create logic moved into lessons viewset
    # def create(self, validated_data, **args):
    #     validated_data["instructor_id"] = validated_data["instructor_id"].id
    #     lesson = Lesson.objects.create(**validated_data)
    #     return lesson



class ReactionSerializer(serializers.ModelSerializer):
    substance = serializers.ListField(child=serializers.CharField())
    volume = serializers.ListField(child=serializers.FloatField())
    class Meta:
        model = Reaction
        fields = ['substance', 'volume']