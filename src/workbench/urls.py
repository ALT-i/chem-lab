from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import *

workbench_router = SimpleRouter()


workbench_router.register(r'workbench/apparatus', ApparatusViewSet)
workbench_router.register(r'workbench/substance', SubstanceViewSet)

urlpatterns = [
    path('workbench/calculate-reaction/', CalculateReactionView.as_view(), name='calculate-reaction'),
]