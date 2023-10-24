from django.db import models


class Device(models.Model):
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
    Group = models.CharField(unique=True, max_length=255)
    last_time_used = models.FloatField(blank=True, null=True)


class Admin(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=100)


class RefPoint(models.Model):
    latitude= models.FloatField(blank=True, null=True)
    longitude= models.FloatField(blank=True, null=True)
    altitude= models.FloatField(blank=True, null=True)
    actual_group = models.OneToOneField(
        "Group", on_delete=models.SET_NULL, blank=True, null=True, max_length=255
    )
