from django.db import models
from users.models import Usuario

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class ObraSocial(models.Model):

    '''
    Catálogo de obras sociales
    '''

    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'obras_sociales'
        verbose_name = 'Obra Social'
        verbose_name_plural = 'Obras Sociales'

    def __str__(self):
        return self.nombre


class Paciente(models.Model):

    '''
    Perfil médico y de contacto del paciente
    Está vinculado 1 a 1 con el modelo Usuario (que maneja login y contraseña)

    - tipo_identificacion: estrictamente 'DNI' o 'PASAPORTE'
    - num_identificacion: OJO!! combinación de tipo + número no se puede repetir en la BD
    - obra_social: ID numérico de la obra social o null si se atiende de forma particular
    '''

    TIPO_IDENTIFICACION_CHOICES = [
        ('DNI', 'DNI'),
        ('PASAPORTE', 'Pasaporte'),
    ]

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='paciente'
    )
    obra_social = models.ForeignKey(
        ObraSocial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pacientes'
    )
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=50, null=True, blank=True)
    correo = models.EmailField(max_length=100)
    tipo_identificacion = models.CharField(max_length=10, choices=TIPO_IDENTIFICACION_CHOICES)
    num_identificacion = models.CharField(max_length=20)
    grupo_sanguineo = models.CharField(max_length=10, null=True, blank=True)
    contacto_emergencia_nombre = models.CharField(max_length=50, null=True, blank=True)
    contacto_emergencia_numero = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'pacientes'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        unique_together = ('tipo_identificacion', 'num_identificacion') # UNIQUE compuesto

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido} - {self.num_identificacion}"


@receiver(post_save, sender=Paciente)
def crear_historia_clinica(sender, instance, created, **kwargs):
    # NO hace falta hacer un POST manual a /historias-clinicas/ cuando se registra alguien
    # al crear un PACIENTE nuevo exitosamente, el backend le genera su Historia Clínica asociada de forma automática en blanco
    if created:
        from clinicos.models import HistoriaClinica  # import acá adentro
        HistoriaClinica.objects.get_or_create(
            paciente=instance,
            defaults={'fecha_alta': timezone.now().date()},
        )