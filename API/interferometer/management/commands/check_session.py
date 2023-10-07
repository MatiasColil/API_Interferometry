from django.core.management.base import BaseCommand
from interferometer.models import Session

class Command(BaseCommand):
    help = 'Comprueba la tabla Session y verifica que tenga un valor numérico, en caso de estar vacio, agrega el valor 1'

    def handle(self, *args, **kwargs):
        try:
            session_count = Session.objects.count()

            # Si no hay registros, insertamos el número 1
            if session_count == 0:
                Session.objects.create(session=1)
                self.stdout.write(self.style.SUCCESS('Número 1 agregado a la tabla Session.'))

            # Si hay más de un registro o el registro no es un número, lanzamos un error
            elif session_count > 1 or not isinstance(Session.objects.first().session, int):
                raise ValueError("Hay más de un registro o el valor no es un número")

            else:
                self.stdout.write(self.style.SUCCESS('Todo está en orden en la tabla Session.'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))

