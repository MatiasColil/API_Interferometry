import numpy as np
import pandas as pd
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import LocationsListSerializer
from .functions import simulation

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
