from rest_framework.routers import SimpleRouter

from .views import *

workspace_router = SimpleRouter()

workspace_router.register(r'workspace/lesson', LessonViewSet)