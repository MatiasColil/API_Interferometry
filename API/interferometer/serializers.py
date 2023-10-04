from rest_framework import serializers

class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    altitude = serializers.FloatField()

class LocationsListSerializer(serializers.Serializer):
    locations = LocationSerializer(many=True)
    reference = LocationSerializer()
