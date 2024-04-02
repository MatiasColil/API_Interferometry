from django.core.management.base import BaseCommand
from django.core.files import File
import os
from interferometer.models import Imagen

class Command (BaseCommand):
    help = "Verifica si las imagenes modelo están subidas, en caso contrario las sube"

    def handle(self, *args, **kwargs):
        try:
            img_count = Imagen.objects.count()

            #Si no hay imagenes en la db
            if img_count == 0:
                for filename in os.listdir("./img/"):
                    if filename.endswith('.jpg') or filename.endswith('.png'):
                        image_path = os.path.join( "./img/", filename)
                        imagen = Imagen()
                        imagen.archivo.save(filename, File(open(image_path, 'rb')))
                        self.stdout.write(self.style.SUCCESS(f'Imagen {filename} subida'))

            else:
                self.stdout.write(self.style.SUCCESS('Todo está en orden en la tabla Imagen.'))
        
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))

    