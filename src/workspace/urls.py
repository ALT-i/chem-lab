from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import *

workspace_router = SimpleRouter()

workspace_router.register(r'workspace/lessons', LessonViewSet)

urlpatterns = [
    # Moodle endpoints
    path('moodle/students/', MoodleStudentsView.as_view(), name='moodle-students'),
    path('moodle/user/profile/', MoodleUserProfileView.as_view(), name='moodle-user-profile'),
    path('moodle/grades/assignment/', MoodleAssignmentGradesView.as_view(), name='moodle-grades-assignment'),
    path('', include(workspace_router.urls)),
]
