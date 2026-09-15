from rest_framework import viewsets, status
from .models import Especialidad, Profesional, Matricula, HorarioMedico, ProfesionalEspecialidad
from .serializers import (
    EspecialidadSerializer, ProfesionalSerializer,
    MatriculaSerializer, HorarioMedicoSerializer,
    ProfesionalEspecialidadSerializer,
    AltaProfesionalSerializer, BajaProfesionalSerializer
)

from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from users.permissions import IsAdmin

from rest_framework.decorators import action
from rest_framework.response import Response


class EspecialidadViewSet(viewsets.ModelViewSet):
    queryset = Especialidad.objects.all().order_by('nombre')
    serializer_class = EspecialidadSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # tods pueden ver las especialidades, pero solo ADMIN puede crear, editar o eliminar
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]


class ProfesionalViewSet(viewsets.ModelViewSet):
    queryset = Profesional.objects.select_related('usuario').prefetch_related(
        'matriculas', 'horarios', 'especialidades__especialidad'
    ).all()
    serializer_class = ProfesionalSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('alta', 'baja', 'reactivar', 'create', 'destroy'):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='alta')
    def alta(self, request):
        """POST /api/profesionales/profesionales/alta/"""
        serializer = AltaProfesionalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profesional = serializer.save()
        return Response(
            AltaProfesionalSerializer().to_representation(profesional),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='baja')
    def baja(self, request, pk=None):
        """
        POST /api/profesionales/profesionales/{id}/baja/
        No borra: pone usuario.estado = INACTIVO (o is_active=False).
        """
        profesional = self.get_object()
        usuario = profesional.usuario
        usuario.estado = 'INACTIVO'
        # Si usás AbstractBaseUser con is_active:
        if hasattr(usuario, 'is_active'):
            usuario.is_active = False
        usuario.save()
        return Response({
            'mensaje': 'Profesional dado de baja',
            'profesional_id': profesional.id,
            'usuario_id': usuario.id,
            'estado': usuario.estado,
        })

    @action(detail=True, methods=['post'], url_path='reactivar')
    def reactivar(self, request, pk=None):
        """POST /api/profesionales/profesionales/{id}/reactivar/"""
        profesional = self.get_object()
        usuario = profesional.usuario
        usuario.estado = 'ACTIVO'
        if hasattr(usuario, 'is_active'):
            usuario.is_active = True
        usuario.save()
        return Response({
            'mensaje': 'Profesional reactivado',
            'profesional_id': profesional.id,
            'estado': usuario.estado,
        })


class MatriculaViewSet(viewsets.ModelViewSet):
    queryset = Matricula.objects.select_related('profesional__usuario').all()
    serializer_class = MatriculaSerializer
    permission_classes = [IsAuthenticated]


class HorarioMedicoViewSet(viewsets.ModelViewSet):
    queryset = HorarioMedico.objects.select_related('profesional__usuario').all()
    serializer_class = HorarioMedicoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.roles.filter(rol__nombre='ADMIN').exists():
            return qs   # ADMIN ve horarios de todos

        if user.roles.filter(rol__nombre='MEDICO').exists():
            try:
                return qs.filter(profesional=user.profesional)  # MÉDICO ve sus horarios
            except Exception:
                return qs.none()

        if self.request.method in SAFE_METHODS:
            return qs   # PACIENTE ve todos los horarios (solo lectura)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        # MEDICO: al crear un horario (POST) el backend le asigna automáticamente su ID
        # ADMIN: sí debe mandar a qué profesional le está cargando el horario
        if user.roles.filter(rol__nombre='MEDICO').exists():
            serializer.save(profesional=user.profesional)
        else:
            serializer.save()


class ProfesionalEspecialidadViewSet(viewsets.ModelViewSet):
    queryset = ProfesionalEspecialidad.objects.select_related(
        'profesional__usuario', 'especialidad'
    ).all()
    serializer_class = ProfesionalEspecialidadSerializer
    permission_classes = [IsAuthenticated]