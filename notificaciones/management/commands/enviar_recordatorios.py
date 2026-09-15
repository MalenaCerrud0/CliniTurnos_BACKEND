from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from turnos.models import Turno
from notificaciones.models import Notificacion
from notificaciones.services import enviar_notificacion


class Command(BaseCommand):
    # IMPORTANTE: Esto NO es un endpoint (no se pega por HTTP)
    # Es un script interno del backend que corre automáticamente cada cierto tiempo (cron job)
    # para generar las notificaciones de los turnos que están por venir.
    help = (
        'Envía recordatorios de turnos RESERVADOS a 48 hs y 24 hs del inicio. '
        'Pensado para ejecutarse cada hora (cron / Task Scheduler).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué enviaría, sin crear ni mandar nada',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        ahora = timezone.now()

        # Define las ventanas de tiempo: busca turnos que falten entre 47-49 horas o 23-25 horas.
        ventanas = [
            ('48hs', timedelta(hours=47), timedelta(hours=49)),   # ~48 hs
            ('24hs', timedelta(hours=23), timedelta(hours=25)),   # ~24 hs
        ]

        total = 0

        for etiqueta, delta_min, delta_max in ventanas:
            inicio_ventana = ahora + delta_min
            fin_ventana = ahora + delta_max

            # Filtra solo los turnos en estado RESERVADO y que tengan un paciente asignado
            candidatos = Turno.objects.filter(
                estado='RESERVADO',
                paciente__isnull=False,
            ).select_related('paciente__usuario', 'profesional__usuario')

            for turno in candidatos:
                inicio = timezone.make_aware(
                    datetime.combine(turno.fecha, turno.fecha_hora_inicio)
                )

                # Si el turno no cae dentro de la ventana exacta de tiempo, lo ignora
                if not (inicio_ventana <= inicio <= fin_ventana):
                    continue

                usuario = turno.paciente.usuario if turno.paciente else None
                if not usuario:
                    continue

                # Acá el backend chequea si ya le generó esta alerta al usuario 
                # para no mandarle 2 veces por el mismo turno
                ya_enviado = Notificacion.objects.filter(
                    usuario=usuario,
                    turno=turno,
                    tipo='RECORDATORIO',
                    asunto__icontains=etiqueta,
                ).exists()

                if ya_enviado:
                    self.stdout.write(
                        f'  [skip] Turno {turno.id} ya tiene recordatorio {etiqueta}'
                    )
                    continue

                asunto = f'Recordatorio de turno ({etiqueta})'
                mensaje = (
                    f'Recordatorio: tenés un turno el {turno.fecha} '
                    f'a las {turno.fecha_hora_inicio} '
                    f'(faltan aproximadamente {etiqueta}).'
                )

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [dry-run] Turno {turno.id} → {asunto}'
                        )
                    )
                    total += 1
                    continue

                # Si pasó todos los filtros, crea la Notificación en la BD y la dispara por email/sistema
                n = Notificacion.objects.create(
                    usuario=usuario,
                    turno=turno,
                    tipo='RECORDATORIO',
                    canal='SISTEMA',
                    asunto=asunto,
                    mensaje=mensaje,
                    estado='PENDIENTE',
                    fecha_programada=ahora,
                )
                enviar_notificacion(n)
                total += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  [ok] Turno {turno.id} → {asunto}')
                )

        self.stdout.write(self.style.SUCCESS(f'Listo. Procesados: {total}'))