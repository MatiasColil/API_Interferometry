import numpy as np
import pandas as pd
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets
from .serializers import LocationsListSerializer
from .serializers import DeviceSerializer
from .functions import simulation
from .models import Device

@api_view(['POST'])
def calculate_centroid(request):
    serializer = LocationsListSerializer(data=request.data)
    if serializer.is_valid():
        locations = serializer.validated_data['locations']
        reference = serializer.validated_data['reference']
        reference2 = np.array([reference["latitude"], reference["longitude"], reference["altitude"]])
        df = pd.DataFrame(locations)
        simulation(12, 20 ,0, df, reference2)
    return Response(serializer.errors, status=400)

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    lookup_field = 'device_id'