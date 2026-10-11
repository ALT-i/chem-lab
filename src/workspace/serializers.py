from rest_framework import serializers

from ..workbench.serializers import SubstanceSerializer, ApparatusSerializer
from .models import Lesson, LessonSession, Reaction
from .grading import calculate_session_grade
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


class LessonSessionSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    grade_evaluation = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LessonSession
        fields = [
            'id',
            'lesson',
            'student',
            'measurements',
            'lesson_title',
            'student_email',
            'grade_evaluation',
        ]
        extra_kwargs = {
            'id': {'required': False},
            'student': {'required': False},
            'measurements': {'required': False},
        }

    def get_grade_evaluation(self, obj):
        if obj.measurements:
            return calculate_session_grade(obj.measurements)
        return None