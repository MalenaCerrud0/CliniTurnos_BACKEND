from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta, datetime

from .models import Turno, FechaBloqueada
from .serializers import TurnoSerializer, FechaBloqueadaSerializer
from profesionales.models import HorarioMedico, Profesional
from users.permissions import IsAdminOrMedico


def _puede_modificar_turno(user, turno):
    # Verifica si el usuario puede cancelar/reprogramar este turno
    if user.roles.filter(rol__nombre='ADMIN').exists():
        return True
    if user.roles.filter(rol__nombre='MEDICO').exists():
        try:
            return turno.profesional == user.profesional
        except Exception:
            return False
    if user.roles.filter(rol__nombre='PACIENTE').exists():
        try:
            return turno.paciente == user.paciente
        except Exception:
            return False
    return False


def _faltan_mas_de_24hs(turno):
    # Verifica si faltan más de 24 horas para el turno
    inicio_turno = timezone.make_aware(
        datetime.combine(turno.fecha, turno.fecha_hora_inicio)
    )
    return inicio_turno > timezone.now() + timedelta(hours=24)

def _crear_notificacion(usuario, turno, tipo, asunto, mensaje, canal='SISTEMA'):
    # Notificaciones se disparan solas al reservar/cancelar.
    from notificaciones.models import Notificacion
    from notificaciones.services import enviar_notificacion

    if not usuario:
        return None

    n = Notificacion.objects.create(
        usuario=usuario,
        turno=turno,
        tipo=tipo,
        canal=canal,
        asunto=asunto,
        mensaje=mensaje,
        estado='PENDIENTE',
        fecha_programada=timezone.now(),
    )

    # Intento de envío inmediato
    enviar_notificacion(n)
    return n

class TurnoViewSet(viewsets.ModelViewSet):
    queryset = Turno.objects.select_related(
        'paciente__usuario', 'profesional__usuario', 'especialidad'
    ).all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Turno.objects.select_related(
            'paciente__usuario',
            'paciente__obra_social',
            'profesional__usuario',
            'especialidad',
        ).all()

        # Filtrar los turnos pasándole estos parámetros en la URL
        # Ej: GET /turnos/?profesional=5&estado=DISPONIBLE o GET /turnos/?proximos=true
        profesional_id = self.request.query_params.get('profesional')
        fecha = self.request.query_params.get('fecha')
        estado = self.request.query_params.get('estado')
        proximos = self.request.query_params.get('proximos')
        pasados = self.request.query_params.get('pasados')

        if profesional_id:
            queryset = queryset.filter(profesional_id=profesional_id)
        if fecha:
            queryset = queryset.filter(fecha=fecha)
        if estado:
            queryset = queryset.filter(estado=estado)

        hoy = timezone.now().date()
        ahora = timezone.now().time()

        if proximos in ('1', 'true', 'True'):
            from django.db.models import Q
            queryset = queryset.filter(
                Q(fecha__gt=hoy) | Q(fecha=hoy, fecha_hora_inicio__gte=ahora)
            ).exclude(
                estado__in=['CANCELADO', 'FINALIZADO', 'AUSENTE']
            ).order_by('fecha', 'fecha_hora_inicio')

        elif pasados in ('1', 'true', 'True'):
            from django.db.models import Q
            queryset = queryset.filter(
                Q(fecha__lt=hoy) |
                Q(fecha=hoy, fecha_hora_inicio__lt=ahora) |
                Q(estado__in=['FINALIZADO', 'AUSENTE', 'CANCELADO'])
            ).order_by('-fecha', '-fecha_hora_inicio')

        # --- Filtro por rol ---
        if user.roles.filter(rol__nombre='ADMIN').exists():
            return queryset

        if user.roles.filter(rol__nombre='MEDICO').exists():
            try:
                return queryset.filter(profesional=user.profesional)
            except Exception:
                return queryset.none()

        if user.roles.filter(rol__nombre='PACIENTE').exists():
            try:
                from django.db.models import Q
                # PACIENTE ve sus turnos + turnos DISPONIBLES (para poder reservar)
                return queryset.filter(
                    Q(paciente=user.paciente) | Q(estado='DISPONIBLE')
                )
            except Exception:
                return queryset.none()

        return queryset.none()

    @action(detail=True, methods=['post'])
    def reservar(self, request, pk=None):
        # POST /turnos/{id}/reservar/
        # PACIENTE hace la reserva sin mandar nada
        # ADMIN y MÉDICO debe mandar { "paciente_id": ID } en el body
        turno = self.get_object()
        user = request.user

        if turno.estado != 'DISPONIBLE':
            return Response(
                {'error': 'El turno no está disponible'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # no reservar horarios pasados
        inicio = timezone.make_aware(
            datetime.combine(turno.fecha, turno.fecha_hora_inicio)
        )
        if inicio <= timezone.now():
            return Response(
                {'error': 'Este turno ya no está disponible (horario pasado)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        paciente_id = request.data.get('paciente_id')

        if not paciente_id and user.roles.filter(rol__nombre='PACIENTE').exists():
            try:
                paciente_id = user.paciente.id
            except Exception:
                return Response(
                    {'error': 'No se encontró el perfil de paciente'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not paciente_id:
            return Response(
                {'error': 'Se requiere paciente_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from pacientes.models import Paciente
        try:
            paciente = Paciente.objects.select_related('obra_social').get(pk=paciente_id)
        except Paciente.DoesNotExist:
            return Response(
                {'error': 'Paciente no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        turno.paciente = paciente
        turno.estado = 'RESERVADO'
        turno.comentario = request.data.get('comentario', turno.comentario)
        turno.save()

        turno.paciente = paciente
        turno.estado = 'RESERVADO'
        turno.comentario = request.data.get('comentario', turno.comentario)
        turno.save()

        # --- notificaciones ---
        if turno.paciente and turno.paciente.usuario:
            _crear_notificacion(
                usuario=turno.paciente.usuario,
                turno=turno,
                tipo='RESERVA',
                asunto='Turno reservado',
                mensaje=(
                    f'Tu turno del {turno.fecha} a las {turno.fecha_hora_inicio} '
                    f'fue reservado correctamente.'
                ),
            )

        if turno.profesional and turno.profesional.usuario:
            _crear_notificacion(
                usuario=turno.profesional.usuario,
                turno=turno,
                tipo='RESERVA',
                asunto='Nuevo turno asignado',
                mensaje=(
                    f'Se te asignó un turno el {turno.fecha} '
                    f'a las {turno.fecha_hora_inicio}.'
                ),
            )

        serializer = self.get_serializer(turno)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        # POST /turnos/{id}/cancelar/ (no hace falta mandar nada en el body)
        # OJO!!
        #   Si faltan > 24hs, el turno pasa a estado 'DISPONIBLE' de nuevo
        #   Si faltan < 24hs, queda 'CANCELADO'
        turno = self.get_object()

        if not _puede_modificar_turno(request.user, turno):
            raise PermissionDenied('No tenés permiso para cancelar este turno')

        if turno.estado not in ['RESERVADO', 'EN_CURSO']:
            return Response(
                {'error': f'No se puede cancelar un turno en estado {turno.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if _faltan_mas_de_24hs(turno):
            turno.paciente = None
            turno.estado = 'DISPONIBLE'
            mensaje = 'Turno cancelado y liberado (vuelve a disponible)'
        else:
            turno.estado = 'CANCELADO'
            mensaje = 'Turno cancelado (dentro de las 24 hs, no se libera)'

        turno.save()

        paciente_usuario = None
        if turno.paciente and turno.paciente.usuario:
            paciente_usuario = turno.paciente.usuario

        profesional_usuario = None
        if turno.profesional and turno.profesional.usuario:
            profesional_usuario = turno.profesional.usuario

        if _faltan_mas_de_24hs(turno):
            turno.paciente = None
            turno.estado = 'DISPONIBLE'
            mensaje = 'Turno cancelado y liberado (vuelve a disponible)'
        else:
            turno.estado = 'CANCELADO'
            mensaje = 'Turno cancelado (dentro de las 24 hs, no se libera)'

        turno.save()

        if paciente_usuario:
            _crear_notificacion(
                usuario=paciente_usuario,
                turno=turno,
                tipo='CANCELACION',
                asunto='Turno cancelado',
                mensaje=(
                    f'Tu turno del {turno.fecha} a las {turno.fecha_hora_inicio} '
                    f'fue cancelado.'
                ),
            )

        if profesional_usuario:
            _crear_notificacion(
                usuario=profesional_usuario,
                turno=turno,
                tipo='CANCELACION',
                asunto='Turno cancelado',
                mensaje=(
                    f'Se canceló el turno del {turno.fecha} '
                    f'a las {turno.fecha_hora_inicio}.'
                ),
            )

        serializer = self.get_serializer(turno)
        return Response({
            'mensaje': mensaje,
            'turno': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reprogramar(self, request, pk=None):
        # POST /turnos/{id}/reprogramar/
        # IMPORTANTE: Mandar en el body { "nuevo_turno_id": ID_DEL_TURNO_LIBRE }
        turno = self.get_object()
        nuevo_turno_id = request.data.get('nuevo_turno_id')

        if not _puede_modificar_turno(request.user, turno):
            raise PermissionDenied('No tenés permiso para reprogramar este turno')

        if turno.estado != 'RESERVADO':
            return Response(
                {'error': 'Solo se pueden reprogramar turnos en estado RESERVADO'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _faltan_mas_de_24hs(turno):
            return Response(
                {'error': 'Solo se puede reprogramar con más de 24 horas de anticipación'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not nuevo_turno_id:
            return Response(
                {'error': 'Se requiere nuevo_turno_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            nuevo_turno = Turno.objects.get(pk=nuevo_turno_id, estado='DISPONIBLE')
        except Turno.DoesNotExist:
            return Response(
                {'error': 'El nuevo turno no existe o no está disponible'},
                status=status.HTTP_400_BAD_REQUEST
            )

        paciente = turno.paciente

        nuevo_turno.paciente = paciente
        nuevo_turno.estado = 'RESERVADO'
        nuevo_turno.save()

        turno.paciente = None
        turno.estado = 'DISPONIBLE'
        turno.save()

        # --- notificaciones ---
        if paciente and paciente.usuario:
            _crear_notificacion(
                usuario=paciente.usuario,
                turno=nuevo_turno,
                tipo='REPROGRAMACION',
                asunto='Turno reprogramado',
                mensaje=(
                    f'Tu turno fue reprogramado al {nuevo_turno.fecha} '
                    f'a las {nuevo_turno.fecha_hora_inicio}.'
                ),
            )

        if nuevo_turno.profesional and nuevo_turno.profesional.usuario:
            _crear_notificacion(
                usuario=nuevo_turno.profesional.usuario,
                turno=nuevo_turno,
                tipo='REPROGRAMACION',
                asunto='Turno reprogramado',
                mensaje=(
                    f'Un turno se reprogramó al {nuevo_turno.fecha} '
                    f'a las {nuevo_turno.fecha_hora_inicio}.'
                ),
            )

        serializer = self.get_serializer(nuevo_turno)
        return Response({
            'mensaje': 'Turno reprogramado correctamente',
            'turno': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrMedico])
    def iniciar(self, request, pk=None):
        # POST /turnos/{id}/iniciar/
        # Mueve el turno a 'EN_CURSO' y le crea una Consulta (o Estudio) automáticamente en el módulo Clínico.
        # Si el turno es ESTUDIO, mandar en el body { "tipo_estudio_id": ID }
        from clinicos.models import Consulta, Estudio, TipoEstudio

        turno = self.get_object()

        if turno.tipo_turno == 'ESTUDIO':
            if not request.user.roles.filter(rol__nombre__in=['ADMIN', 'MEDICO']).exists():
                raise PermissionDenied('No tenés permiso para iniciar este estudio')
        else:
            # CONSULTA: solo el médico dueño o admin
            if not request.user.roles.filter(rol__nombre='ADMIN').exists():
                try:
                    if turno.profesional != request.user.profesional:
                        raise PermissionDenied('Solo el médico del turno puede iniciarlo')
                except Exception:
                    raise PermissionDenied('No tenés permiso')

        if turno.estado not in ['RESERVADO']:
            return Response(
                {'error': f'No se puede iniciar un turno en estado {turno.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        turno.estado = 'EN_CURSO'
        turno.save()

        mensaje = 'Turno iniciado'
        if turno.tipo_turno == 'CONSULTA':
            consulta, created = Consulta.objects.get_or_create(
                turno=turno,
                defaults={
                    'fecha_consulta': timezone.now(),
                    'estado': 'EN_CURSO'
                }
            )
            mensaje = 'Turno iniciado y Consulta creada' if created else 'Turno iniciado'

        elif turno.tipo_turno == 'ESTUDIO':
            tipo_estudio_id = request.data.get('tipo_estudio_id')
            if not tipo_estudio_id:
                return Response(
                    {'error': 'Para un turno ESTUDIO se requiere tipo_estudio_id'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                tipo_estudio = TipoEstudio.objects.get(pk=tipo_estudio_id, activo=True)
            except TipoEstudio.DoesNotExist:
                return Response(
                    {'error': 'Tipo de estudio no encontrado'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not turno.paciente_id:
                return Response(
                    {'error': 'El turno no tiene paciente asignado'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # acá se crea el estudio (con fecha_solicitud)
            estudio, created = Estudio.objects.get_or_create(
                turno=turno,
                defaults={
                    'tipo_estudio': tipo_estudio,
                    'paciente_id': turno.paciente_id,
                    'fecha_solicitud': timezone.now(),
                    'estado': 'SOLICITADO',
                },
            )
            mensaje = (
                'Turno iniciado y Estudio creado'
                if created
                else 'Turno iniciado (el estudio ya existía)'
            )

        serializer = self.get_serializer(turno)
        return Response({
            'mensaje': mensaje,
            'turno': serializer.data
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrMedico])
    def generar_slots(self, request):
        # POST /turnos/generar_slots/
        # Genera automáticamente todos los turnos de la agenda en base al horario configurado del médico
        # Mandar en el body: { "profesional_id": ID, "dias": CANTIDAD_DE_DIAS }
        profesional_id = request.data.get('profesional_id')
        dias = int(request.data.get('dias', 14))

        if not profesional_id:
            return Response(
                {'error': 'Se requiere profesional_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profesional = Profesional.objects.get(pk=profesional_id)
        except Profesional.DoesNotExist:
            return Response(
                {'error': 'Profesional no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        horarios = HorarioMedico.objects.filter(profesional=profesional, activo=True)
        if not horarios.exists():
            return Response(
                {'error': 'El profesional no tiene horarios cargados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dias_map = {
            'LUNES': 0, 'MARTES': 1, 'MIERCOLES': 2,
            'JUEVES': 3, 'VIERNES': 4
        }

        turnos_creados = 0
        hoy = timezone.now().date()

        for i in range(dias):
            fecha = hoy + timedelta(days=i)
            dia_semana_num = fecha.weekday()

            for horario in horarios:
                if dias_map.get(horario.dia_semana) == dia_semana_num:
                    hora_actual = datetime.combine(fecha, horario.hora_desde)
                    hora_fin = datetime.combine(fecha, horario.hora_hasta)
                    duracion = timedelta(minutes=horario.duracion_turnos_min)

                    while hora_actual + duracion <= hora_fin:
                        existe = Turno.objects.filter(
                            profesional=profesional,
                            fecha=fecha,
                            fecha_hora_inicio=hora_actual.time()
                        ).exists()

                        if not existe:
                            Turno.objects.create(
                                profesional=profesional,
                                tipo_turno='CONSULTA',
                                fecha=fecha,
                                estado='DISPONIBLE',
                                fecha_hora_inicio=hora_actual.time(),
                                fecha_hora_fin=(hora_actual + duracion).time()
                            )
                            turnos_creados += 1

                        hora_actual += duracion

        return Response({
            'mensaje': f'Se generaron {turnos_creados} turnos disponibles',
            'profesional_id': profesional_id,
            'dias': dias
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrMedico], url_path='generar-slots-estudio')
    def generar_slots_estudio(self, request):
        # POST /turnos/generar-slots-estudio/
        # Genera turnos libres para estudios médicos (sin asociarlos a un profesional en particular)
        from profesionales.models import Especialidad
        from datetime import time as dt_time

        especialidad_id = request.data.get('especialidad_id')
        dias = int(request.data.get('dias', 14))
        hora_desde_str = request.data.get('hora_desde', '08:00:00')
        hora_hasta_str = request.data.get('hora_hasta', '12:00:00')
        duracion = int(request.data.get('duracion_turnos_min', 30))
        dias_semana = request.data.get(
            'dias_semana',
            ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES'],
        )

        if not especialidad_id:
            return Response(
                {'error': 'Se requiere especialidad_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            especialidad = Especialidad.objects.get(pk=especialidad_id)
        except Especialidad.DoesNotExist:
            return Response(
                {'error': 'Especialidad no encontrada'},
                status=status.HTTP_404_NOT_FOUND,
            )

        def parse_time(s):
            parts = str(s).split(':')
            return dt_time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)

        hora_desde = parse_time(hora_desde_str)
        hora_hasta = parse_time(hora_hasta_str)

        dias_map = {
            'LUNES': 0, 'MARTES': 1, 'MIERCOLES': 2,
            'JUEVES': 3, 'VIERNES': 4, 'SABADO': 5, 'DOMINGO': 6,
        }
        dias_permitidos = {dias_map[d] for d in dias_semana if d in dias_map}

        turnos_creados = 0
        hoy = timezone.now().date()

        for i in range(dias):
            fecha = hoy + timedelta(days=i)
            if fecha.weekday() not in dias_permitidos:
                continue

            hora_actual = datetime.combine(fecha, hora_desde)
            hora_fin = datetime.combine(fecha, hora_hasta)
            step = timedelta(minutes=duracion)

            while hora_actual + step <= hora_fin:
                existe = Turno.objects.filter(
                    profesional__isnull=True,
                    especialidad=especialidad,
                    tipo_turno='ESTUDIO',
                    fecha=fecha,
                    fecha_hora_inicio=hora_actual.time(),
                ).exists()

                if not existe:
                    Turno.objects.create(
                        profesional=None,
                        especialidad=especialidad,
                        tipo_turno='ESTUDIO',
                        fecha=fecha,
                        estado='DISPONIBLE',
                        fecha_hora_inicio=hora_actual.time(),
                        fecha_hora_fin=(hora_actual + step).time(),
                    )
                    turnos_creados += 1

                hora_actual += step

        return Response({
            'mensaje': f'Se generaron {turnos_creados} turnos de estudio',
            'especialidad_id': especialidad_id,
            'especialidad': especialidad.nombre,
            'dias': dias,
        })

    @action(detail=False, methods=['get'], url_path='disponibilidad')
    def disponibilidad(self, request):
        # IMPORTANTE: GET /turnos/disponibilidad/?fecha=YYYY-MM-DD
        # Usar este endpoint en la pantalla de "Sacar turno" para armar la grilla horaria libre
        # Es obligatorio mandar la fecha por URL.
        # Opcionalmente: ?especialidad_id=ID - ?profesional_id=ID
        fecha = request.query_params.get('fecha')
        especialidad_id = request.query_params.get('especialidad_id')
        profesional_id = request.query_params.get('profesional_id')

        if not fecha:
            return Response(
                {'error': 'El parámetro fecha es obligatorio (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Turno.objects.filter(
            estado='DISPONIBLE',
            fecha=fecha,
        ).select_related(
            'profesional__usuario',
            'especialidad',
            'paciente__obra_social',
        ).order_by('fecha_hora_inicio')

        # para borrar los turnos que ya pasaron y quedaron en disponible
        from django.db.models import Q
        ahora = timezone.now()
        queryset = queryset.filter(
            Q(fecha__gt=ahora.date()) |
            Q(fecha=ahora.date(), fecha_hora_inicio__gte=ahora.time())
        )

        tipo_turno = request.query_params.get('tipo_turno')  # CONSULTA | ESTUDIO
        if tipo_turno:
            queryset = queryset.filter(tipo_turno=tipo_turno)

        if especialidad_id:
            queryset = queryset.filter(especialidad_id=especialidad_id)

        if profesional_id:
            queryset = queryset.filter(profesional_id=profesional_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'fecha': fecha,
            'cantidad': queryset.count(),
            'turnos': serializer.data,
        })

    @action(detail=False, methods=['get'], url_path='profesionales-disponibles')
    def profesionales_disponibles(self, request):
        # GET /turnos/profesionales-disponibles/?fecha=YYYY-MM-DD
        fecha = request.query_params.get('fecha')
        especialidad_id = request.query_params.get('especialidad_id')

        if not fecha:
            return Response(
                {'error': 'El parámetro fecha es obligatorio (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        turnos = Turno.objects.filter(estado='DISPONIBLE', fecha=fecha)

        if especialidad_id:
            turnos = turnos.filter(
                profesional__especialidades__especialidad_id=especialidad_id
            )

        profesional_ids = turnos.values_list('profesional_id', flat=True).distinct()

        from profesionales.models import Profesional
        from profesionales.serializers import ProfesionalSerializer

        profesionales = Profesional.objects.filter(
            id__in=profesional_ids
        ).select_related('usuario').prefetch_related(
            'especialidades__especialidad',
            'matriculas',
        )

        serializer = ProfesionalSerializer(profesionales, many=True)
        return Response({
            'fecha': fecha,
            'cantidad': profesionales.count(),
            'profesionales': serializer.data,
        })


class FechaBloqueadaViewSet(viewsets.ModelViewSet):
    queryset = FechaBloqueada.objects.select_related('profesional__usuario').all()
    serializer_class = FechaBloqueadaSerializer
    permission_classes = [IsAuthenticated]