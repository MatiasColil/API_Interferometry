from django.conf import settings
import numpy as np
import pandas as pd
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework import viewsets
from .serializers import (
    LocationsListSerializer,
    DeviceSerializer,
    AdminSerializer,
    GroupSerializer,
    RefPointSerializer,
    ImagenSerializer,
    ParametersSerializer
)
from .functions import simulation, new_positions
from .models import Device, Admin, Group, RefPoint, Imagen, Parameters
from django.utils import timezone
from rest_framework import status
from firebase_admin import messaging
from django.shortcuts import get_object_or_404
import os



@api_view(["POST"])
def doSimulation(request):
    serializer = LocationsListSerializer(data=request.data)
    if serializer.is_valid():
        locations = serializer.validated_data["locations"]
        reference = serializer.validated_data["reference"]
        parameters = serializer.validated_data["parameter"]
        imagen_instance = get_object_or_404(Imagen, id=parameters["idPath"])
        image_path = './media/'+imagen_instance.archivo.name
        reference2 = np.array(
            [reference["latitude"], reference["longitude"], reference["altitude"]]
        )
        df = pd.DataFrame(locations)
        arr = np.array(df)
        new_pos = new_positions(arr, reference2, parameters["scale"])
        img_dirty, img_coverage, img_sampling, img_psf = simulation(parameters["observationTime"], 
                                                                    parameters["declination"], 
                                                                    parameters["samplingTime"], 
                                                                    image_path, 
                                                                    new_pos, 
                                                                    reference2, 
                                                                    parameters["frequency"])
        return Response([
            {"img": img_dirty},
            {"img": img_coverage},
            {"img": img_sampling},
            {"img": img_psf}
        ],status=200)
    else:
        return Response(serializer.errors, status=400)


class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    queryset = Device.objects.none()

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
                status=400,
            )
        try:
            instance = Device.objects.get(
                actual_group=actual_group, device_id=device_id
            )
        except:
            return Response({"detail": "dispositivo no encontrado."}, status=404)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=False, methods=["delete"], url_name="delete_by_group")
    def delete_by_group(self, request):
        group_id = request.query_params.get("actual_group", None)

        if group_id is None:
            return Response(
                {"detail": "ID de grupo es requerido."},
                status=400,
            )

        devices_to_delete = Device.objects.filter(actual_group=group_id)

        count, _ = devices_to_delete.delete()

        return Response(
            {"detail": f"{count} dispositivos eliminados."},
            status=200,
        )


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
                group.last_time_used = 100
            group.save()
        return groups


class RefPointView(viewsets.ModelViewSet):
    queryset = RefPoint.objects.all()
    serializer_class = RefPointSerializer
    lookup_field = "actual_group"


class MessageView(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    queryset = Device.objects.none()
    
    def get_queryset(self):
        queryset = Device.objects.all()
        group = self.request.query_params.get("actual_group", None)
        devices = Device.objects.filter(actual_group=group)

        return devices

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        token = list(queryset.values_list("tokenFCM", flat=True))

        message = messaging.MulticastMessage(tokens=token)
        response = messaging.send_multicast(message)

        return Response(
            {"enviadas": response.success_count, "fallidas": response.failure_count},
            status=status.HTTP_200_OK,
        )

class ImagenViewSet(viewsets.ModelViewSet):
    queryset = Imagen.objects.all()
    serializer_class = ImagenSerializer

class ParametersViewSet(viewsets.ModelViewSet):
    queryset = Parameters.objects.all()
    serializer_class = ParametersSerializer
    lookup_field= "groupId"