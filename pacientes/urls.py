from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ObraSocialViewSet, PacienteViewSet

router = DefaultRouter()
router.register(r'obras-sociales', ObraSocialViewSet, basename='obra-social')
router.register(r'pacientes', PacienteViewSet, basename='paciente')

urlpatterns = [
    path('', include(router.urls)),
]