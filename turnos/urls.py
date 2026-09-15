from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TurnoViewSet, FechaBloqueadaViewSet

router = DefaultRouter()
router.register(r'turnos', TurnoViewSet, basename='turno')
router.register(r'fechas-bloqueadas', FechaBloqueadaViewSet, basename='fecha-bloqueada')

urlpatterns = [
    path('', include(router.urls)),
]