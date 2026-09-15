from django.db import models
from pacientes.models import Paciente
from profesionales.models import Profesional
from turnos.models import Turno


class HistoriaClinica(models.Model):

    """
    Expediente médico único de un paciente [[ OneToOneField (1 a 1) -> cada Paciente tiene una y solo una Historia Clínica ]]
    Al pedir un Paciente, su historia clínica estará accesible a través de la propiedad 'historia_clinica'
    """

    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.CASCADE,
        related_name='historia_clinica'
    )
    fecha_alta = models.DateField()
    fecha_ult_mod = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'historias_clinicas'
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'

    def __str__(self):
        return f"HC de {self.paciente}"


class Consulta(models.Model):

    """
    Acto médico -> se crea cuando un Turno está en curso
    Los estados posibles para los select/dropdowns son los de ESTADO_CHOICES
    Los campos de texto (diagnostico, plan, etc.) son opcionales (null=True)
    """

    ESTADO_CHOICES = [      # IMPORTANTE FRONTEND: usar estos valores exactos (en mayúsculas) para enviar al backend
        ('PROGRAMADA', 'Programada'),
        ('EN_CURSO', 'En curso'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
        ('NO_ASISTIO', 'No asistió'),
    ]

    turno = models.OneToOneField(
        Turno,
        on_delete=models.CASCADE,
        related_name='consulta'
    )
    diagnostico = models.TextField(max_length=1000, null=True, blank=True)
    plan_tratamiento = models.TextField(max_length=1000, null=True, blank=True)
    indicaciones = models.TextField(max_length=1000, null=True, blank=True)
    observaciones = models.TextField(max_length=1000, null=True, blank=True)
    fecha_consulta = models.DateTimeField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PROGRAMADA')

    class Meta:
        db_table = 'consultas'
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'

    def __str__(self):
        return f"Consulta del turno {self.turno_id}"


class Alergia(models.Model):

    """
    Alergias de un paciente
    Se vincula a la Historia Clínica, un paciente puede tener múltiples alergias
    (llegan como un array/lista en la propiedad 'alergias' de la Historia Clínica)
    """

    historia = models.ForeignKey(
        HistoriaClinica,
        on_delete=models.CASCADE,
        related_name='alergias'
    )
    fecha_registro = models.DateTimeField(null=True, blank=True)
    descripcion = models.CharField(max_length=100)
    severidad = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = 'alergias'
        verbose_name = 'Alergia'
        verbose_name_plural = 'Alergias'

    def __str__(self):
        return self.descripcion


class MedicacionHabitual(models.Model):

    """
    Medicación que el paciente toma regularmente (por ej: anticonceptivas, levotiroxina por tiroides, insulina, etc)
    'activo' (booleano) sirve para filtrar si el paciente la sigue tomando (TRUE) o ya la suspendió (FALSE)
    """

    historia = models.ForeignKey(
        HistoriaClinica,
        on_delete=models.CASCADE,
        related_name='medicaciones'
    )
    medicamento = models.CharField(max_length=100)
    dosis = models.CharField(max_length=50, null=True, blank=True)
    frecuencia = models.CharField(max_length=50, null=True, blank=True)
    fecha_desde = models.DateField(null=True, blank=True)
    fecha_hasta = models.DateField(null=True, blank=True)
    motivo = models.CharField(max_length=200, null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'medicaciones_habituales'
        verbose_name = 'Medicación Habitual'
        verbose_name_plural = 'Medicaciones Habituales'

    def __str__(self):
        return self.medicamento


class TipoEstudio(models.Model):

    """
    Catálogo de estudios médicos disponibles en la clínica (por ej: hemograma, radiografía, etc)
    Usar para poblar los selectores al momento de solicitar un nuevo estudio
    """

    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    duracion_min = models.PositiveIntegerField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'tipos_estudio'
        verbose_name = 'Tipo de Estudio'
        verbose_name_plural = 'Tipos de Estudio'

    def __str__(self):
        return self.nombre


class Estudio(models.Model):

    """
    Solicitud y realización de un estudio específico para un Paciente
    Puede o no estar vinculado a un Turno específico (turno = null/blank es válido)
    Prestar atención a ESTADO_CHOICES para el seguimiento del estudio !!
    """

    ESTADO_CHOICES = [
        ('SOLICITADO', 'Solicitado'),
        ('REALIZADO', 'Realizado'),
        ('INFORMADO', 'Informado'),
        ('CANCELADO', 'Cancelado'),
    ]

    tipo_estudio = models.ForeignKey(
        TipoEstudio,
        on_delete=models.PROTECT,
        related_name='estudios'
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='estudios'
    )
    turno = models.OneToOneField(
        Turno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estudio'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_realizacion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='SOLICITADO')
    observaciones = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'estudios'
        verbose_name = 'Estudio'
        verbose_name_plural = 'Estudios'

    def __str__(self):
        return f"{self.tipo_estudio} - {self.paciente}"


class EstudioDetalle(models.Model):

    """
    Ítems dentro de un Estudio general
    Se envía como un array de objetos anidados dentro de la creación del Estudio
    """

    estudio = models.ForeignKey(
        Estudio,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    descripcion = models.CharField(max_length=200)
    observaciones = models.CharField(max_length=200, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'estudio_detalle'
        verbose_name = 'Detalle de Estudio'
        verbose_name_plural = 'Detalles de Estudio'

    def __str__(self):
        return self.descripcion


class DocumentoClinico(models.Model):

    """
    Gestión de archivos adjuntos (PDFs, imágenes, etc)
    Como contiene un FileField ('archivo'), al enviar datos por POST/PUT se debe usar form-data en lugar de un JSON plano !!
    Puede asociarse opcionalmente a una Historia, Turno, Consulta o Estudio
    """

    TIPO_CHOICES = [
        ('INFORME', 'Informe'),
        ('ESTUDIO', 'Resultado de estudio'),
        ('RECETA', 'Receta'),
        ('OTRO', 'Otro'),
    ]

    historia = models.ForeignKey(
        HistoriaClinica,
        on_delete=models.CASCADE,
        related_name='documentos',
        null=True,
        blank=True,
    )
    turno = models.ForeignKey(
        'turnos.Turno',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos',
    )
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos',
    )
    estudio = models.ForeignKey(
        Estudio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='OTRO')
    nombre = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='documentos/%Y/%m/')
    fecha_carga = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'documentos_clinicos'
        ordering = ['-fecha_carga']

    def __str__(self):
        return self.nombre