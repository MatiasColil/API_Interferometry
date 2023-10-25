import numpy as np
import pandas as pd
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets
from .serializers import (
    LocationsListSerializer,
    DeviceSerializer,
    AdminSerializer,
    GroupSerializer,
    RefPointSerializer,
)
from .functions import simulation, new_positions
from .models import Device, Admin, Group, RefPoint
from django.utils import timezone
from rest_framework import status
from firebase_admin import messaging
from django.http import FileResponse


@api_view(["POST"])
def doSimulation(request):
    serializer = LocationsListSerializer(data=request.data)
    if serializer.is_valid():
        locations = serializer.validated_data["locations"]
        reference = serializer.validated_data["reference"]
        reference2 = np.array(
            [reference["latitude"], reference["longitude"], reference["altitude"]]
        )
        df = pd.DataFrame(locations)
        arr = np.array(df)
        new = new_positions(arr, reference2)
        img = simulation(12, 20, 0, new, reference2)
        return FileResponse(img, content_type='image/png')
    else:
        return Response(serializer.errors, status=400)


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    lookup_field = "device_id"

    def get_queryset(self):
        queryset = Device.objects.all()
        actual_group = self.request.query_params.get("actual_group", None)
        device_id = self.request.query_params.get("device_id", None)

        if actual_group:
            queryset = queryset.filter(actual_group=actual_group)
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        return queryset

    def update(self, request, *args, **kwargs):
        actual_group = request.data.get("actual_group", None)
        device_id = request.data.get("device_id", None)

        if not all([actual_group, device_id]):
            return Response(
                {"detail": ""},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            instance = Device.objects.get(
                actual_group=actual_group, device_id=device_id
            )
        except:
            return Response(
                {"detail": "Device not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class DeviceViewByGroup(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    lookup_field = "actual_group"


class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer


class GroupRetrieveView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_queryset(self):
        groups = Group.objects.all()
        current_time = timezone.now()
        for group in groups:
            device = Device.objects.filter(actual_group=group).first()
            if device:
                difference = current_time - device.modified_at
                group.last_time_used = difference.total_seconds() / 3600
            else:
                group.last_time_used = 0
            group.save()
        return groups


class RefPointView(viewsets.ModelViewSet):
    queryset = RefPoint.objects.all()
    serializer_class = RefPointSerializer
    lookup_field ='actual_group'

class MessageView(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    def get_queryset(self):
        group = self.request.query_params.get('actual_group', None)
        devices = Device.objects.filter(actual_group=group)

        return devices
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        token = list(queryset.values_list('tokenFCM', flat=True))

        message = messaging.MulticastMessage(tokens=token)
        response = messaging.send_multicast(message)

        return Response({'enviadas': response.success_count, 'fallidas': response.failure_count}, status=status.HTTP_200_OK)
