from rest_framework import serializers
from .models import Device, Admin, Group, RefPoint, Imagen, Parameters

"""
Serializers: Serializers allow complex data such as querysets and model instances to be converted 
to native Python datatypes that can then be easily rendered into JSON, XML or other content types.
https://www.django-rest-framework.org/api-guide/serializers/
"""


class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    altitude = serializers.FloatField()
    distance = serializers.FloatField() 

class ReferenceSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    altitude = serializers.FloatField()
    
class ParametersSerializer(serializers.Serializer):
    observationTime = serializers.FloatField()
    declination = serializers.FloatField()
    samplingTime = serializers.FloatField()
    frequency = serializers.FloatField()
    idPath = serializers.IntegerField()
    scale = serializers.FloatField()
    scheme = serializers.CharField()
    robust_param = serializers.FloatField()
    
class LocationsListSerializer(serializers.Serializer):
    locations = LocationSerializer(many=True)
    reference = ReferenceSerializer()
    parameter = ParametersSerializer()

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class RefPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefPoint
        fields = '__all__'

class ImagenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Imagen
        fields = '__all__'

class ParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameters
        fields = '__all__'

class ParameterGroupSerializer(serializers.Serializer):
    actual_group = serializers.IntegerField()
    parameter = ParametersSerializer()