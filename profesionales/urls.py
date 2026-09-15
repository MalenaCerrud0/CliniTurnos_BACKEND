from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EspecialidadViewSet, ProfesionalViewSet,
    MatriculaViewSet, HorarioMedicoViewSet,
    ProfesionalEspecialidadViewSet
)

router = DefaultRouter()
router.register(r'especialidades', EspecialidadViewSet, basename='especialidad')
router.register(r'profesionales', ProfesionalViewSet, basename='profesional')
router.register(r'matriculas', MatriculaViewSet, basename='matricula')
router.register(r'horarios', HorarioMedicoViewSet, basename='horario')
router.register(r'profesional-especialidades', ProfesionalEspecialidadViewSet, basename='profesional-especialidad')

urlpatterns = [
    path('', include(router.urls)),
]