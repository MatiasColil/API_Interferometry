from rest_framework import serializers
from .models import Device, Admin, Group

class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    altitude = serializers.FloatField()

class LocationsListSerializer(serializers.Serializer):
    locations = LocationSerializer(many=True)
    reference = LocationSerializer()

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