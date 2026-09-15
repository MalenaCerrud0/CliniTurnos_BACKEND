from django.db import models
from users.models import Usuario


class Especialidad(models.Model):

    '''
    Catálogo de especialidades médicas
    'nombre' es único, no se puede repetir.
    '''

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=225, null=True, blank=True)

    class Meta:
        db_table = 'especialidades'
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'

    def __str__(self):
        return self.nombre


class Profesional(models.Model):

    '''
    Perfil médico -> 1 a 1 con el modelo Usuario (para el login)
    al pedir un Profesional (GET), van a llegar anidadas sus especialidades, matrículas y horarios disponibles
    '''

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='profesional'
    )

    class Meta:
        db_table = 'profesional'
        verbose_name = 'Profesional'
        verbose_name_plural = 'Profesionales'

    def __str__(self):
        return f"Dr/a. {self.usuario.nombre} {self.usuario.apellido}"


class ProfesionalEspecialidad(models.Model):

    '''
    TABLA INTERMEDIA (un profesional puede tener varias especialidades)
    OJO: No mandar la misma especialidad dos veces para el mismo profesional porque va a tirar error (tiene un UNIQUE compuesto)
    '''

    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.CASCADE,
        related_name='especialidades'
    )
    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.CASCADE,
        related_name='profesionales'
    )

    class Meta:
        db_table = 'profesional_especialidades'
        unique_together = ('profesional', 'especialidad')
        verbose_name = 'Profesional-Especialidad'
        verbose_name_plural = 'Profesionales-Especialidades'

    def __str__(self):
        return f"{self.profesional} → {self.especialidad}"


class ProfesionalPaciente(models.Model):

    """
    Relación de qué pacientes atiende cada profesional (AGENDA)
    Unique compuesto: (profesional_id, paciente_id), sirve para la vista de "Mis Pacientes" del médico
    """

    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.CASCADE,
        related_name='pacientes'
    )
    paciente = models.ForeignKey(
        'pacientes.Paciente',
        on_delete=models.CASCADE,
        related_name='profesionales'
    )

    class Meta:
        db_table = 'profesional_pacientes'
        unique_together = ('profesional', 'paciente')
        verbose_name = 'Profesional-Paciente'
        verbose_name_plural = 'Profesionales-Pacientes'

    def __str__(self):
        return f"{self.profesional} atiende a {self.paciente}"


class Matricula(models.Model):

    '''
    Matrículas habilitantes del médico

    - tipo_matricula: 'NACIONAL' o 'PROVINCIAL'
    - numero_matricula: único en todo el sistema.
    - activa: Usar para filtrar en la UI y no mostrar matrículas dadas de baja (True por defecto)
    '''

    TIPO_MATRICULA_CHOICES = [
        ('NACIONAL', 'Nacional'),
        ('PROVINCIAL', 'Provincial'),
    ]

    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.CASCADE,
        related_name='matriculas'
    )
    numero_matricula = models.CharField(max_length=50, unique=True)
    tipo_matricula = models.CharField(max_length=15, choices=TIPO_MATRICULA_CHOICES)
    jurisdiccion = models.CharField(max_length=100, null=True, blank=True)
    fecha_emision = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'matriculas'
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'

    def __str__(self):
        return f"{self.numero_matricula} ({self.tipo_matricula})"


class HorarioMedico(models.Model):

    '''
    Días y horas en los que atiende el profesional.

    - duracion_turnos_min: define de a cuántos minutos se corta la grilla visual de turnos (ej: 15, 30, o 60).
    - hora_desde / hora_hasta: "HH:MM:SS" (ej: "09:00:00").
    '''

    DIA_SEMANA_CHOICES = [
        ('LUNES', 'Lunes'),
        ('MARTES', 'Martes'),
        ('MIERCOLES', 'Miércoles'),
        ('JUEVES', 'Jueves'),
        ('VIERNES', 'Viernes'),
    ]

    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.CASCADE,
        related_name='horarios'
    )
    dia_semana = models.CharField(max_length=10, choices=DIA_SEMANA_CHOICES)
    hora_desde = models.TimeField()
    hora_hasta = models.TimeField()
    duracion_turnos_min = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'horarios_medico'
        verbose_name = 'Horario Médico'
        verbose_name_plural = 'Horarios Médicos'

    def __str__(self):
        return f"{self.profesional} - {self.dia_semana} {self.hora_desde}-{self.hora_hasta}"