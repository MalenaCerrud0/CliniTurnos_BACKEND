from django.db import models
from users.models import Usuario
from turnos.models import Turno


class Notificacion(models.Model):

    '''
    Manejo de alertas y avisos del sistema
    
    - canal: si dice 'SISTEMA' es para mostrar en la UI, si dice 'EMAIL' se manda por correo
    - turno: por si la alerta es de un turno específico o un aviso general
    - asunto: título en la tarjetita de la notificación
    - mensaje: cuerpo/detalle
    - estado: arranca en 'PENDIENTE' hasta que el backend la procesa y la pasa a 'ENVIADA' o 'FALLIDA'
    - intentos_reintento: control interno del backend
    - GET: ya vienen ordenadas de la más nueva a la más vieja por defecto
    '''

    CANAL_CHOICES = [
        ('SISTEMA', 'Sistema'),
        ('EMAIL', 'Email'),
    ]

    ESTADO_CHOICES = [
        ('PROGRAMADA', 'Programada'),
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADA', 'Enviada'),
        ('FALLIDA', 'Fallida'),
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    turno = models.ForeignKey(
        Turno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones'
    )
    tipo = models.CharField(max_length=255)
    canal = models.CharField(max_length=10, choices=CANAL_CHOICES)
    asunto = models.CharField(max_length=255)
    mensaje = models.CharField(max_length=255)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_programada = models.DateTimeField()
    fecha_envio = models.DateTimeField(null=True, blank=True)
    intentos_reintento = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'notificaciones'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_programada']

    def __str__(self):
        return f"{self.asunto} - {self.estado}"