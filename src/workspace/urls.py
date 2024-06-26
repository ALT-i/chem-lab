from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

workspace_router = SimpleRouter()

workspace_router.register(r'workspace/lessons', LessonViewSet)
workspace_router.register(r'workspace/reactions', ReactionViewSet)

urlpatterns = [
    # Your other URL patterns
    path('chemical-reaction/', chemical_reaction, name='chemical-reaction'),
    path('', include(workspace_router.urls)),
]
