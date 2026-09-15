from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet, RolViewSet, UsuarioRolViewSet,
    MeView, RegistroPacienteView,
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'roles', RolViewSet, basename='rol')
router.register(r'usuario-roles', UsuarioRolViewSet, basename='usuario-rol')

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('registro/', RegistroPacienteView.as_view(), name='registro-paciente'),
    path('', include(router.urls)),
]