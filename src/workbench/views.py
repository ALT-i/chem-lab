from django.db.models.expressions import RawSQL
import json
from django.shortcuts import render

from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chempy import balance_stoichiometry

from .models import *
from .serializers import *


# Create your views here.
class SubstanceViewSet(ModelViewSet):
    """
        CRUD operations on Substance objects
    """
    queryset  = Substance.objects.all()
    serializer_class =  SubstanceSerializer
    filterset_fields = ['name']

    def get_queryset(self):                                      
        return super().get_queryset()
    
    def perform_create(self, serializer):
        serializer.save()
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({"message": "Substance created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)
    
    def list(self, request):
        filter_obj = request.query_params.get('name')
        queryset = self.get_queryset()
        if filter_obj:
            queryset = self.queryset.filter(name__contains = filter_obj)
        try:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({"message": "Substance retrived successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({"message":"Substance retrived successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def perform_update(self, serializer):
        serializer.save()
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response({"message": "Substance updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)        
        
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class ApparatusViewSet(ModelViewSet):
    """
        CRUD operations on Apparatus objects
    """
    queryset  = Apparatus.objects.all().order_by('name')
    serializer_class =  ApparatusSerializer
    filterset_fields = ['name', 'type', 'category', 'material']

    def get_queryset(self):                                      
        return super().get_queryset()
    
    def perform_create(self, serializer):
        serializer.save()
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({"message": "Apparatus created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED, headers=headers)
    
    def list(self, request):
        filter_obj = request.query_params.get('name')
        queryset = self.get_queryset()
        if filter_obj:
            queryset = self.queryset.filter(name__contains = filter_obj)
        try:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({"message": "Apparatus retrived successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({"message":"Apparatus retrived successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def perform_update(self, serializer):
        serializer.save()
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response({"message": "Apparatus updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)        
        
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)