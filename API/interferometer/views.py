from django.conf import settings
import numpy as np
import pandas as pd
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework import viewsets
from .serializers import (
    DeviceSerializer,
    AdminSerializer,
    GroupSerializer,
    RefPointSerializer,
    ImagenSerializer,
    ParametersSerializer,
    ParameterGroupSerializer,
)
from .functions import simulation, new_positions
from .models import Device, Admin, Group, RefPoint, Imagen, Parameters
from django.utils import timezone
from rest_framework import status
from firebase_admin import messaging
from django.shortcuts import get_object_or_404


@api_view(["GET"])
def simuGuest(request):

    id_group = request.query_params.get("actual_group")
    locations = Device.objects.filter(actual_group=id_group)
    refpoint = RefPoint.objects.filter(actual_group=id_group)
    parameters = Parameters.objects.filter(groupId=id_group)
    locations_serializer = DeviceSerializer(locations, many=True)
    refpoint_serializer = RefPointSerializer(refpoint, many=True)
    parameters_serializer = ParametersSerializer(parameters, many=True)
    refpoint_data = refpoint_serializer.data
    parameters_data = parameters_serializer.data
    dvice = pd.DataFrame(locations_serializer.data)
    imagen_instance = get_object_or_404(Imagen, id=parameters_data[0]["idPath"])
    image_path = "./media/" + imagen_instance.archivo.name
    dvice = dvice.drop(
        ["id", "device_id", "actual_group", "modified_at", "tokenFCM"], axis=1
    )
    array = np.array(dvice)
    reference = np.array(
        [
            refpoint_data[0]["latitude"],
            refpoint_data[0]["longitude"],
            refpoint_data[0]["altitude"],
        ]
    )
    new_pos = new_positions(array, reference, parameters_data[0]["scale"])
    img_dirty, img_coverage, img_sampling, img_psf = simulation(
        parameters_data[0]["observationTime"],
        parameters_data[0]["declination"],
        parameters_data[0]["samplingTime"],
        image_path,
        new_pos,
        reference,
        parameters_data[0]["frequency"],
        parameters_data[0]["scheme"],
        parameters_data[0]["robust_param"]
    )
    return Response(
        [
            {"img": img_dirty},
            {"img": img_coverage},
            {"img": img_sampling},
            {"img": img_psf},
        ],
        status=200,
    )


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
            device = Device.objects.filter(actual_group=group).order_by("-modified_at").first()
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
        print(token)

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
    lookup_field = "groupId"


@api_view(["POST"])
def simuAdmin(request):
    data = ParameterGroupSerializer(data=request.data)
    if data.is_valid():
        parameters = data.validated_data["parameter"]
        id_group = request.data.get("actual_group")
        locations = Device.objects.filter(actual_group=id_group)
        refpoint = RefPoint.objects.filter(actual_group=id_group)
        locations_serializer = DeviceSerializer(locations, many=True)
        refpoint_serializer = RefPointSerializer(refpoint, many=True)
        refpoint_data = refpoint_serializer.data
        dvice = pd.DataFrame(locations_serializer.data)
        imagen_instance = get_object_or_404(Imagen, id=parameters["idPath"])
        image_path = "./media/" + imagen_instance.archivo.name
        tokenFCM = list(dvice["tokenFCM"])
        dvice = dvice.drop(
            ["id", "device_id", "actual_group", "modified_at", "tokenFCM"], axis=1
        )
        array = np.array(dvice)
        reference = np.array(
            [
                refpoint_data[0]["latitude"],
                refpoint_data[0]["longitude"],
                refpoint_data[0]["altitude"],
            ]
        )
        new_pos = new_positions(array, reference, parameters["scale"])
        img_dirty, img_coverage, img_sampling, img_psf = simulation(
            parameters["observationTime"],
            parameters["declination"],
            parameters["samplingTime"],
            image_path,
            new_pos,
            reference,
            parameters["frequency"],
            parameters["scheme"],
            parameters["robust_param"]
        )

        message = messaging.MulticastMessage(tokens=tokenFCM)
        response = messaging.send_each_for_multicast(message)
        print(response.responses[0].exception)
        print("enviadas: ", response.success_count, "fallidas:", response.failure_count)
        return Response(
            [
                {"img": img_dirty},
                {"img": img_coverage},
                {"img": img_sampling},
                {"img": img_psf},
            ],
            status=200,
        )
    else:
        return Response(data.errors, status=400)
