from django.db import models
from pacientes.models import Paciente
from profesionales.models import Profesional, Especialidad


class Turno(models.Model):

    '''
    Gestión de agenda y citas médicas

    - tipo_turno: 'CONSULTA' o 'ESTUDIO'
    - estado: turnos libres nacen como 'DISPONIBLE'. Manejar los cambios según las acciones de la UI ('RESERVADO', 'CANCELADO', etc.).
    - paciente: Puede ser null si el turno todavía está 'DISPONIBLE'. Cuando un paciente reserva, se asocia su ID acá.
    - OJO!! No mandar dos veces la misma combinación de 'profesional', 'fecha' y 'fecha_hora_inicio' porque tira error (UNIQUE compuesto).
        Un médico no puede tener dos turnos a la misma hora exacta.
    '''

    TIPO_TURNO_CHOICES = [
        ('CONSULTA', 'Consulta'),
        ('ESTUDIO', 'Estudio'),
    ]

    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('RESERVADO', 'Reservado'),
        ('CANCELADO', 'Cancelado'),
        ('FINALIZADO', 'Finalizado'),
        ('AUSENTE', 'Ausente'),
        ('BLOQUEADO', 'Bloqueado'),
        ('EN_CURSO', 'En curso'),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos'
    )
    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos'
    )
    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos'
    )
    tipo_turno = models.CharField(max_length=10, choices=TIPO_TURNO_CHOICES)
    fecha = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='DISPONIBLE')
    fecha_hora_inicio = models.TimeField()
    fecha_hora_fin = models.TimeField()
    comentario = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'turnos'
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        unique_together = ('profesional', 'fecha', 'fecha_hora_inicio') # UNIQUE compuesto
        ordering = ['fecha', 'fecha_hora_inicio']

    def __str__(self):
        return f"Turno {self.fecha} {self.fecha_hora_inicio} - {self.estado}"


class FechaBloqueada(models.Model):

    '''
    Bloqueos temporales de la agenda (vacaciones, licencia, enfermedad del médico, etc)
    '''

    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.CASCADE,
        related_name='fechas_bloqueadas'
    )
    fecha_desde = models.DateTimeField()
    fecha_hasta = models.DateTimeField()
    motivo = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'fechas_bloqueadas'
        verbose_name = 'Fecha Bloqueada'
        verbose_name_plural = 'Fechas Bloqueadas'

    def __str__(self):
        return f"{self.profesional} bloqueado desde {self.fecha_desde}"