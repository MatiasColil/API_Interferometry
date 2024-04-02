from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Comprueba la tabla auth_user y verifica que al menos exista un usuario administrador, en caso contrario se crea.'

    def handle(self, *args, **kwargs):
        try:
            admin_count = User.objects.filter(is_superuser=True).count()

            # Si no hay usuarios administradores, se inserta uno
            if admin_count == 0:
                user = User(username="DivulgadorInt")
                user.set_password("Interferometer20XX")
                user.is_staff= True
                user.is_superuser= True
                user.save()
                self.stdout.write(self.style.SUCCESS('Usuario administrador agregado a la tabla auth_user.'))
            else:
                self.stdout.write(self.style.SUCCESS('Todo está en orden en la tabla auth_user.'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))
