from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import *
from .serializers import *

# Create your views here.

class LessonViewSet(ModelViewSet):
    """
        CRUD operations on Lesson objects
    """
    queryset  = Lesson.objects.all().order_by('title')
    serializer_class =  LessonSerializer

    def get_queryset(self):                                      
        return super().get_queryset()