from django.db import models

class Device(models.Model):
    device_id = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    actual_session = models.IntegerField(blank=True, null=True)

class Session(models.Model):
    session = models.IntegerField(unique=True)