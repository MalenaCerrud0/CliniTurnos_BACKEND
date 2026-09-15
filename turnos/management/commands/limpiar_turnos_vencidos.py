from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from turnos.models import Turno


class Command(BaseCommand):
    help = (
        'Elimina turnos DISPONIBLES cuyo horario de inicio ya pasó '
        '(no se tomaron y ya no tienen sentido).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra cuántos borraría, sin eliminar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        ahora = timezone.now()
        hoy = ahora.date()
        hora = ahora.time()

        # DISPONIBLE y (fecha < hoy) o (fecha == hoy y hora_inicio < ahora)
        qs = Turno.objects.filter(estado='DISPONIBLE').filter(
            Q(fecha__lt=hoy) | Q(fecha=hoy, fecha_hora_inicio__lt=hora)
        )

        total = qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[dry-run] Se borrarían {total} turnos')
            )
            for t in qs[:20]:
                self.stdout.write(
                    f'  id={t.id} {t.fecha} {t.fecha_hora_inicio} tipo={t.tipo_turno}'
                )
            if total > 20:
                self.stdout.write(f'  ... y {total - 20} más')
            return

        borrados, _ = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(f'Eliminados {borrados} turnos DISPONIBLES vencidos')
        )