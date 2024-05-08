from rest_framework.routers import SimpleRouter

from src.users.views import RegisterViewSet, UserViewSet

users_router = SimpleRouter()
users_router.register(r'register', RegisterViewSet, basename="signup")
users_router.register(r'users', UserViewSet, basename="user")

