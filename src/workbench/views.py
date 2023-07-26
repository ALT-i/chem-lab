from django.db.models.expressions import RawSQL

from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import *
from .serializers import *


# Create your views here.
class SubstanceViewSet(ModelViewSet):
    """
        CRUD operations on Substance objects
    """
    queryset  = Substance.objects.all().order_by('name')
    serializer_class =  SubstanceSerializer

    def get_queryset(self):                                      
        return super().get_queryset().filter()


class ApparatusViewSet(ModelViewSet):
    """
        CRUD operations on Apparatus objects
    """
    queryset  = Apparatus.objects.all().order_by('name')
    serializer_class =  ApparatusSerializer
    filterset_fields = ['type', 'category', 'material']

    def get_queryset(self):                                      
        return super().get_queryset()