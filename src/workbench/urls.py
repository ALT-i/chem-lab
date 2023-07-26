from rest_framework.routers import SimpleRouter

from .views import *

workbench_router = SimpleRouter()


workbench_router.register(r'workbench/apparatus', ApparatusViewSet)
workbench_router.register(r'workbench/substance', SubstanceViewSet)