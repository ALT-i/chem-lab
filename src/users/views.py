from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from src.users.models import User
from src.users.permissions import IsUserOrReadOnly
from src.users.serializers import CreateUserSerializer, UserSerializer

# view for registering users
class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    # def post(self, request, format=None):
    #     serializer = CreateUserSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,  viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    queryset = User.objects.all()
    serializers = {'default': UserSerializer}
    permissions = {'default': (IsUserOrReadOnly,)}

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def get_user_data(self, instance):
        try:
            return Response(UserSerializer(self.request.user, context={'request': self.request}).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Wrong auth token' + e}, status=status.HTTP_400_BAD_REQUEST)
