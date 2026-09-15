from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConsultaViewSet,
    HistoriaClinicaViewSet,
    AlergiaViewSet,
    MedicacionHabitualViewSet,
    TipoEstudioViewSet,
    EstudioViewSet,
    DocumentoClinicoViewSet,
)

router = DefaultRouter()
router.register(r'consultas', ConsultaViewSet, basename='consulta')
router.register(r'historias-clinicas', HistoriaClinicaViewSet, basename='historia-clinica')
router.register(r'alergias', AlergiaViewSet, basename='alergia')
router.register(r'medicaciones', MedicacionHabitualViewSet, basename='medicacion')
router.register(r'tipos-estudio', TipoEstudioViewSet, basename='tipo-estudio')
router.register(r'estudios', EstudioViewSet, basename='estudio')
router.register(r'documentos', DocumentoClinicoViewSet, basename='documento')

urlpatterns = [
    path('', include(router.urls)),
]