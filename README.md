# Desplegar en modo desarrollo
1. Requisitos.
    - Pip
    - Python >= 3.11
    - PostgreSQL

2. Instalar librerias necesarias del archivo requirements.txt del directorio `\API\`.

    `pip install -r requirements.txt`
    
3. Instalar psycopg2.

    `pip install psycopg2`

4. Descomentar la siguiente linea en el archivo url.py del directorio `\API\API\` para que se sirvan las imagenes modelo.

    ```bash
   + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```
    
5. Crear base de datos con nombre `interferometry`. En caso de tener un distinto "user", "password", "host" o "port", realizar los cambios pertinentes al apartado "DATABASES" del archivo settings.py que se encuentra en `\API\API\`
   
6. Realizar migraciones en el directorio `\API\ `.

   `python manage.py makemigrations`
   
   `python manage.py migrate`

7. Desplegar

    `python manage.py runserver`

# Desplegar en producción SO Linux

1. Requisitos.
    - Pip
    - Python >= 3.10
    - PostgreSQL
    - Nginx

2. Instalar el paquete libgl1-mesa-glx. Proporciona la implementación de OpenGL para sistemas basados en Linux.

    `sudo apt-get install libgl1-mesa-glx`

3. Instalar el paquete libpq-dev. Relevante para poder instalar la libreria de python psycopg2

    `sudo apt-get install libpq-dev`

4. Instalar PostgreSQL y configurar la DB

    - Instalar con comando: `sudo apt install postgresql`
    - Iniciar consola: `sudo -u postgres psql`
    - Cambiar contraseña del usuario "postgres": `ALTER USER postgres WITH PASSWORD 'superadmin';`
    - Crear la base de datos: `CREATE DATABASE interferometry;`

5. Permitir acceso remoto a la DB

    - Abrir el archivo de configuración ph_hba.conf `sudo nano /etc/postgresql/version/main/pg_hba.conf` y agregamos la siguiente linea:
    ```
   # Acceso remoto
    host    all             all             all                     scram-sha-256
   ```
   - Abrir el archivo de configuración postgresql.conf `sudo nano /etc/postgresql/version/main/postgresql.conf` y buscamos la siguiente linea
   ```
        #listen_addresses = 'localhost'         # what IP address(es) to listen on;
   ```
    la descomentamos y cambiamos su valor
    ```
        listen_addresses = '*'         # what IP address(es) to listen on;
    ```
6. Reiniciamos el servicio

    `sudo systemctl restart postgresql`  

7. Instalar librerias necesarias del archivo requirements.txt del directorip `\API_Interferometry\API\`.

    `pip install -r requirements.txt`
       
8. Realizar migraciones en el directorio `\API_Interferometry\API\ `.

   `python3 manage.py makemigrations`
   
   `python3 manage.py migrate`

9. Configurar nginx
    
    - crear archivo `sudo nano /etc/nginx/sites-available/interferometer`
    - copiar y pegar el contenido del archivo nginx_config.txt en el archivo creado. Realizar cambios si es pertinente.
    - crear enlace `sudo ln -s /etc/nginx/sites-available/interferometer /etc/nginx/sites-enabled`
    - eliminar archivo "default" de `/etc/nginx/sites-enabled/` y `/etc/nginx/sites-available/`
    - reiniciar nginx `sudo service nginx restart`

10. Desplegar con comando: `gunicorn -c gunicorn_config.py API.wsgi:application > salida.log 2> error.log &`

11. Para ver logs en tiempo real `tail -f /var/log/nginx/access.log` o `tail -f salida.log`

12. Para ver logs de error en tiempo real `tail -f /var/log/nginx/error.log` o `tail -f error.log`

13. Recordar habilitar los puertos HTTP en el Firewall.