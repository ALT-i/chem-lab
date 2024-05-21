from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from src.users.models import User
from src.users.permissions import IsUserOrReadOnly
from src.users.serializers import CreateUserSerializer, UserSerializer

# view for registering users
class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    
class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,  viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    queryset = User.objects.all().order_by('-date_joined')
    serializers = {'default': UserSerializer, 'create_official': CreateUserSerializer } 
    # permissions = {'default': (IsUserOrReadOnly,)}
    filterset_fields = ['role']

    def get_queryset(self):                                      
        return super().get_queryset()
    
    def perform_create(self, serializer):
        serializer.save()
    
    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    # def get_permissions(self):
    #     self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
    #     return super().get_permissions()
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({"message":"User retrived successfully", "data": serializer.data}, status=status.HTTP_200_OK)
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
        return Response({"message": "User updated successfully", "data": serializer.data}, status=status.HTTP_200_OK) 
    
    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def get_user_data(self, instance):
        try:
            return Response(UserSerializer(self.request.user, context={'request': self.request}).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Wrong auth token'}, status=status.HTTP_400_BAD_REQUEST) 
        
    def list(self, request): 
        queryset = self.get_queryset()
        queryset = self.queryset.filter(
            Q(first_name__icontains = request.query_params.get('search') if request.query_params.get('search') else '') | 
            Q(last_name__icontains = request.query_params.get('search') if request.query_params.get('search') else '') | 
            Q(email__icontains = request.query_params.get('search') if request.query_params.get('search') else ''), 
            role__contains = request.query_params.get('role') if request.query_params.get('role') else ''
        ).values()
        try:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({"message": "Users retrived successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='official', url_name='official')
    def create_official(self, request):
        """For creating officials like instructors, admins and super-admins
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({"message": "User created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'message': f'{e}'}, status=status.HTTP_400_BAD_REQUEST)
    
