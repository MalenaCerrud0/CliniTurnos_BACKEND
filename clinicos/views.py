from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from users.permissions import IsAdminOrMedico

from .models import (
    Consulta, HistoriaClinica, Alergia, MedicacionHabitual,
    TipoEstudio, Estudio, EstudioDetalle,
    DocumentoClinico,
)
from .serializers import (
    ConsultaSerializer, HistoriaClinicaSerializer,
    AlergiaSerializer, MedicacionHabitualSerializer,
    TipoEstudioSerializer, EstudioSerializer, EstudioDetalleSerializer,
    DocumentoClinicoSerializer,
)


class ConsultaViewSet(viewsets.ModelViewSet):
    queryset = Consulta.objects.select_related(
        'turno__paciente__usuario',
        'turno__profesional__usuario',
    ).all()
    serializer_class = ConsultaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrMedico]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.roles.filter(rol__nombre='ADMIN').exists():
            return queryset

        if user.roles.filter(rol__nombre='MEDICO').exists():
            try:
                return queryset.filter(turno__profesional=user.profesional)     # MÉDICO solo ve sus propias consultas
            except Exception:
                return queryset.none()

        return queryset.none()

    @action(detail=True, methods=['post'])      # POST /consultas/{id}/finalizar/
    def finalizar(self, request, pk=None):
        consulta = self.get_object()

        if consulta.estado == 'FINALIZADA':
            return Response(
                {'error': 'La consulta ya está finalizada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        consulta.estado = 'FINALIZADA'
        consulta.save()

        turno = consulta.turno
        turno.estado = 'FINALIZADO'     # CIERRE AUTOMÁTICO DE TURNO al finalizar la consulta
        turno.save()

        try:
            historia = consulta.turno.paciente.historia_clinica
            historia.fecha_ult_mod = timezone.now()     # ACTUALIZA FECHA de la historia clínica
            historia.save(update_fields=['fecha_ult_mod'])
        except Exception:
            pass

        serializer = self.get_serializer(consulta)
        return Response({
            'mensaje': 'Consulta y turno finalizados correctamente',
            'consulta': serializer.data,
        })


class HistoriaClinicaViewSet(viewsets.ReadOnlyModelViewSet):    # SOLO GET!! NO enviar POST/PUT a este endpoint
    queryset = HistoriaClinica.objects.select_related(
        'paciente__usuario',
    ).prefetch_related('alergias', 'medicaciones').all()
    serializer_class = HistoriaClinicaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.roles.filter(rol__nombre='ADMIN').exists():
            return queryset

        if user.roles.filter(rol__nombre='MEDICO').exists():
            # MÉDICO solo puede ver las historias de los pacientes que alguna vez atendió
            return queryset.filter(
                paciente__turnos__profesional=user.profesional
            ).distinct()

        if user.roles.filter(rol__nombre='PACIENTE').exists():
            try:
                return queryset.filter(paciente=user.paciente)      # PACIENTE solo ve su propia historia
            except Exception:
                return queryset.none()

        return queryset.none()


class AlergiaViewSet(viewsets.ModelViewSet):
    queryset = Alergia.objects.select_related('historia__paciente__usuario').all()
    serializer_class = AlergiaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrMedico]


class MedicacionHabitualViewSet(viewsets.ModelViewSet):
    queryset = MedicacionHabitual.objects.select_related(
        'historia__paciente__usuario'
    ).all()
    serializer_class = MedicacionHabitualSerializer
    permission_classes = [IsAuthenticated, IsAdminOrMedico]


# ----- ESTUDIOS ----- #

class TipoEstudioViewSet(viewsets.ModelViewSet):
    queryset = TipoEstudio.objects.filter(activo=True).order_by('nombre')   # solo devuelve los que estén ACTIVOS
    serializer_class = TipoEstudioSerializer
    permission_classes = [IsAuthenticated]


class EstudioViewSet(viewsets.ModelViewSet):
    queryset = Estudio.objects.select_related(
        'tipo_estudio', 'paciente__usuario', 'turno'
    ).prefetch_related('detalles').all()
    serializer_class = EstudioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.roles.filter(rol__nombre='ADMIN').exists():
            return qs

        if user.roles.filter(rol__nombre='MEDICO').exists():
            return qs

        if user.roles.filter(rol__nombre='PACIENTE').exists():
            try:
                return qs.filter(paciente=user.paciente)    # PACIENTE solo ve sus propios estudios
            except Exception:
                return qs.none()

        return qs.none()

    def get_permissions(self):
        # PACIENTES solo pueden ver (GET), ADMIN y MÉDICO pueden crear o editar estudios
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrMedico()]

    def perform_update(self, serializer):
        estudio = serializer.save()

        # al marcar estudio como REALIZADO, cierra automáticamente el turno asociado
        if estudio.estado == 'REALIZADO' and estudio.turno_id:
            turno = estudio.turno
            if turno.estado != 'FINALIZADO':
                turno.estado = 'FINALIZADO'
                turno.save(update_fields=['estado'])

#########

class DocumentoClinicoViewSet(viewsets.ModelViewSet):
    queryset = DocumentoClinico.objects.select_related(
        'historia', 'turno', 'consulta', 'estudio'
    ).all()
    serializer_class = DocumentoClinicoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        # FILTROS X QUERY PARAMS: ?consulta=ID - ?estudio=ID - ?turno=ID
        consulta_id = self.request.query_params.get('consulta')
        estudio_id = self.request.query_params.get('estudio')
        turno_id = self.request.query_params.get('turno')
        if consulta_id:
            qs = qs.filter(consulta_id=consulta_id)
        if estudio_id:
            qs = qs.filter(estudio_id=estudio_id)
        if turno_id:
            qs = qs.filter(turno_id=turno_id)

        if user.roles.filter(rol__nombre='ADMIN').exists():
            return qs
        if user.roles.filter(rol__nombre='MEDICO').exists():
            return qs
        if user.roles.filter(rol__nombre='PACIENTE').exists():
            try:
                return qs.filter(
                    historia__paciente=user.paciente
                ) | qs.filter(turno__paciente=user.paciente)
            except Exception:
                return qs.none()
        return qs.none()

    def get_permissions(self):
        # PACIENTES pueden descargar/ver (GET), ADMIN y MÉDICO pueden subir archivos (POST/PUT)
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrMedico()]