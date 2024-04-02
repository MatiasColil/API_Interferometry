# Desplegar en modo desarrollo
1. Requisitos.
    - Pip
    - Python >= 3.11
    - PostgreSQL

2. Instalar librerias necesarias del archivo requirements.txt del directorio `\API\`.

    `pip install -r requirements.txt`
    
3. Instalar psycopg2.

    `pip install psycopg2`

4. Descomentar la siguiente linea en el archivo url.py del directorio `\API\API\`.

    ```bash
   + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```
    
5. Crear base de datos con nombre `interferometry`. En caso de tener un distinto "user", "password", "host" o "port", realizar los cambios pertinentes al apartado "DATABASES" del archivo settings.py que se encuentra en `\API\API\`
   
6. Realizar migraciones en el directorio `\API\ `.

   `python manage.py makemigrations`
   
   `python manage.py migrate`

7. Desplegar

    `python manage.py runserver`

# Desplegar en producción

1. Requisitos.
    - Pip
    - Python >= 3.11
    - PostgreSQL
    - Nginx

2. Instalar librerias necesarias del archivo requirements.txt del directorip `\API\`.

    `pip install -r requirements.txt`
    
3. Instalar psycopg2.

    `pip install psycopg2`
    
4. Instalar el paquete libgl1-mesa-glx.

    `sudo apt-get install libgl1-mesa-glx`

5. Crear base de datos con nombre `interferometry` y cambiar "user", "password", "host" y "port" si estima conveniente.
   
6. Realizar migraciones en el directorio `\API\ `.

   `python manage.py makemigrations`
   
   `python manage.py migrate`

7. Configurar nginx
    
    - abrir nginx.conf `sudo nano /etc/nginx/nginx.conf`
    - cambiar linea `user www-data` a `user root`
    - crear archivo `sudo nano /etc/nginx/sites-available/interferometer`
    - copiar y pegar el contenido del archivo nginx_config.txt en el archivo creado. Realizar cambios si es pertinente.
    - crear enlace `sudo ln -s /etc/nginx/sites-available/interferometer /etc/nginx/sites-enabled`
    - reiniciar nginx `sudo service nginx restart
`

