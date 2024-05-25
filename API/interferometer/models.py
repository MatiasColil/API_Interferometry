from django.db import models


class Device(models.Model):
    """
    Modelo que representa la información necesaria de un dispositivo para formar parte de la simulación.

    device_id: Campo de string. Representa el UUID (identificador único universal de un dispositivo). 
    tokenFCM: Campo de string. Representa el token único entregado por Firebase Cloud Messaging para el dispositivo en concreto.
    latitude: Campo flotante. Representa la latitud del dispositivo en el sistema de coordenadas geografico (WSG84).
    longitude: Campo flotante. Representa la longitud del dispositivo en el sistema de coordenadas geografico (WSG84).
    altitude: Campo flotante. Representa la altitud del dispositivo en el sistema de coordenadas geografico (WSG84).
    distance: obsoleto
    actual_group: Campo llave foránea. Representa el ID del grupo asignado al dispositivo.
    modified_at: Campo de fecha. Representa la fecha y hora en la que fueron modificados los datos del dispositivo en la base de datos.

    """
    device_id = models.CharField(max_length=255, blank=True, null=True)
    tokenFCM = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    altitude = models.FloatField(blank=True, null=True)
    distance = models.FloatField(blank=True, null=True)
    actual_group = models.ForeignKey(
        "Group", on_delete=models.SET_NULL, blank=True, null=True, max_length=255
    )
    modified_at = models.DateTimeField(auto_now=True)

class Group(models.Model):
    """
    Modelo que representa la información de un grupo.

    group: Campo de string. Representa el nombre del grupo.
    last_time_used: Campo flotante. Representa el tiempo en horas de la última vez que fue utilizado.

    """
    Group = models.CharField(unique=True, max_length=255)
    last_time_used = models.FloatField(blank=True, null=True)

class Admin(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=100)

class RefPoint(models.Model):
    """
    Modelo que representa la información de un punto referencia o tambien llamado centro del conjunto de radioantenas.
    latitude: Campo flotante. Representa la latitud del punto de referencia en el sistema de coordenadas geografico (WSG84).
    longitude: Campo flotante. Representa la latitud del punto de referencia en el sistema de coordenadas geografico (WSG84).
    altitude: Campo flotante. Representa la latitud del punto de referencia en el sistema de coordenadas geografico (WSG84).
    actual_group: Campo llave foránea. Representa el ID del grupo asignado al cual pertenece el punto de referencia.
    
    """
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    altitude = models.FloatField(blank=True, null=True)
    actual_group = models.OneToOneField(
        "Group", on_delete=models.SET_NULL, blank=True, null=True, max_length=255
    )

class Imagen(models.Model):
    """
    Modelo que representa una imagen.
    
    """
    archivo = models.ImageField()

class Parameters(models.Model):

    """
    Modelo que representa los parametros de la simulación.
    observationTime: Campo flotante. Representa el tiempo de observación total en horas.
    declination: Campo flotante. Representa la declinación a la cual estoy observando.
    samplingTime: Campo flotante. Representa el tiempo de muestreo en minutos.
    frequency: Campo flotante. Representa la frecuencia de observación en Hertz.
    idPath:: Campo entero. Representa el ID de la imagen a utilizar en la base de datos.
    groupId: Campo entero. Representa el ID del grupo al cual pertenece los parametros de simulación
    scale: Campo flotante. Representa el valor, en metros, al cual se va a escalar las distancias del punto de referencia a los puntos de los dispositivos.
    scheme: Campo de string. Representa el modelo de ponderación a utilizar.
    robust_param: Campo flotante. Representa el valor del modelo de ponderación robusto en caso de utilizarse. Varia entre -2 y 2.

    """

    observationTime = models.FloatField( blank=True, null=True)
    declination = models.FloatField( blank=True, null=True)
    samplingTime = models.FloatField( blank=True, null=True)
    frequency = models.FloatField( blank=True, null=True)
    idPath = models.IntegerField( blank=True, null=True)
    groupId = models.IntegerField(unique=True, blank=True, null=True)
    scale = models.FloatField(blank=True, null=True)
    scheme = models.CharField(blank=True, null=True)
    robust_param= models.FloatField(blank=True, null = True)