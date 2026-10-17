from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *
from src.common.views_moodle import MoodleConfigurationView, MoodleConnectionTestView

workspace_router = SimpleRouter()

workspace_router.register(r'workspace/lessons', LessonViewSet)
workspace_router.register(r'workspace/sessions', LessonSessionViewSet)
workspace_router.register(r'workspace/lesson-sessions', LessonSessionViewSet)

urlpatterns = [
    # Moodle endpoints
    path('moodle/config/', MoodleConfigurationView.as_view(), name='moodle-config'),
    path('moodle/config/test/', MoodleConnectionTestView.as_view(), name='moodle-config-test'),
    path('moodle/students/', MoodleStudentsView.as_view(), name='moodle-students'),
    path('moodle/user/profile/', MoodleUserProfileView.as_view(), name='moodle-user-profile'),
    path('moodle/grades/assignment/', MoodleAssignmentGradesView.as_view(), name='moodle-grades-assignment'),
    path('', include(workspace_router.urls)),
]
