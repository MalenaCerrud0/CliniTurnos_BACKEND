from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


def enviar_notificacion(notificacion):
    # intenta enviar la notificación por email si el usuario tiene correo
    # actualiza estado a ENVIADA o FALLIDA
    
    usuario = notificacion.usuario
    destino = None

    # busca el correo específico asociado al perfil del paciente
    try:
        if hasattr(usuario, 'paciente') and usuario.paciente and usuario.paciente.correo:
            destino = usuario.paciente.correo
    except Exception:
        pass

    # si el paciente no tiene un correo cargado, aborta y la marca como FALLIDA
    if not destino:
        notificacion.estado = 'FALLIDA'
        notificacion.intentos_reintento = (notificacion.intentos_reintento or 0) + 1
        notificacion.save(update_fields=['estado', 'intentos_reintento'])
        return False

    try:
        send_mail(
            subject=notificacion.asunto,
            message=notificacion.mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destino],
            fail_silently=False,
        )
        notificacion.estado = 'ENVIADA'
        notificacion.fecha_envio = timezone.now()
        notificacion.canal = 'EMAIL'
        notificacion.save(update_fields=['estado', 'fecha_envio', 'canal'])
        return True
    except Exception:
        notificacion.estado = 'FALLIDA'
        notificacion.intentos_reintento = (notificacion.intentos_reintento or 0) + 1    # suma un intento fallido por si reintenta más tarde
        notificacion.save(update_fields=['estado', 'intentos_reintento'])
        return False