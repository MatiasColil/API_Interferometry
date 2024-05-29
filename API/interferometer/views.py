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

"""

https://www.django-rest-framework.org/api-guide/views/
"""


@api_view(["GET"])
def simuGuest(request):

    """
    View de simulación para los participantes/invitados.

    Al estar constantemente actualizando la información de los dispositivos participantes 
    no es necesario tener que enviar dicha información a travez de la petición GET,
    sino que solo basta con obtenerla directamente desde la base de datos. Lo anterior 
    se logra recibiendo el grupo al cual pertenecen los dispositivos desde la petición GET
    para así proceder con la obtención de la información.
    
    Por lo tanto, solo se recibe el ID del grupo y se utiliza para filtrar en los objetos/entidades 
    Device, RefPoint y Parameters, para luego utilizar los serializers de cada uno y así obtenerlos en 
    tipos de datos con los que Python pueda trabajar.

    Luego se manejan dichos datos para poder pasarlos como argumentos a las funciones "new_position" y 
    "simulation", finalizando con el envío de los resultados al dispositivo invitado/participante que
    realizó la petición GET.
    
    
    """

    #1
    id_group = request.query_params.get("actual_group")
    locations = Device.objects.filter(actual_group=id_group)
    refpoint = RefPoint.objects.filter(actual_group=id_group)
    parameters = Parameters.objects.filter(groupId=id_group)
    locations_serializer = DeviceSerializer(locations, many=True)
    refpoint_serializer = RefPointSerializer(refpoint, many=True)
    parameters_serializer = ParametersSerializer(parameters, many=True)
    refpoint_data = refpoint_serializer.data
    parameters_data = parameters_serializer.data

    #2
    dvice = pd.DataFrame(locations_serializer.data)
    imagen_instance = get_object_or_404(Imagen, id=parameters_data[0]["idPath"])
    image_path = "./media/" + imagen_instance.archivo.name
    dvice = dvice.drop(
        ["id", "device_id", "actual_group", "modified_at", "tokenFCM", "distance"], axis=1
    )
    array = np.array(dvice).astype(float)
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

    """
    View para los device/dispositivo. Se encuentra modificado el GET, UPDATE y DELETE.

    GET: Filtra por los parametros dado en la query, los cuales son "actual_group" y "device_id"
    devolviendo así la información del dispositivo que solo cumple dichas condiciones.

    UPDATE: Filtra por los parametros dado en la query, los cuales son "actual_group" y "device_id"
    deolviando así un solo objeto/entidad de la base de datos para actualizar su información.
    En caso de no encontrar dicho objeto/entidad se retorna un error. Un caso borde es la posibilidad
    de que el mismo dispositivo este en varios grupos, por lo tanto, se necesita de alguna forma de
    poder diferenciar en cual grupo esta para solo actualizar sus datos para dicho grupo.

    DELETE: En vez de realizar el DELETE de dispositivos teniendo en consideración sus ID's, se realiza
    teniendo en consideración el ID del grupo al cual pertenecen.

    
    """

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
    """
    
    View para el modelo de Group. Solo esta modificado la forma en la que realiza el GET.
    Esta modificación lo que realiza es tomar el primer elemento de la columna 
    "modified_at" del grupo con ID "X" y restarlo al tiempo actual del sistema para así obtener
    la cantidad de horas desde la última vez que se utilizaron los grupos creados.
    
    """
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

    """
    View para el punto de referencia, en donde en lugar de buscar por el ID que le fue asignado al
    momento de crear la entidad en la base de datos, busca por el campo "actual_group"
    """
    queryset = RefPoint.objects.all()
    serializer_class = RefPointSerializer
    lookup_field = "actual_group"

class ImagenViewSet(viewsets.ModelViewSet):
    queryset = Imagen.objects.all()
    serializer_class = ImagenSerializer

class ParametersViewSet(viewsets.ModelViewSet):

    """
    View para los parametros de simulación, en donde en lugar de buscar por el ID que le fue asignado al
    momento de crear la entidad en la base de datos, busca por el campo "groupId"
    """

    queryset = Parameters.objects.all()
    serializer_class = ParametersSerializer
    lookup_field = "groupId"


@api_view(["POST"])
def simuAdmin(request):

    """
    View de simulación para administrador.

    Al estar constantemente actualizando la información de los dispositivos participantes 
    no es necesario tener que enviar dicha información a travez de la petición GET,
    sino que solo basta con obtenerla directamente desde la base de datos. Lo anterior 
    se logra recibiendo el grupo al cual pertenecen los dispositivos desde la petición GET
    para así proceder con la obtención de la información.
    
    Por lo tanto, primero se recibe el ID del grupo y los parametros de simulación
    y se utiliza para filtrar en los objetos/entidades Device, RefPoint, 
    para luego utilizar los serializers de cada uno y así obtenerlos en 
    tipos de datos con los que Python pueda trabajar.

    Luego se manejan dichos datos para poder pasarlos como argumentos a las funciones "new_position" y 
    "simulation", finalizando con el envío de los resultados al dispositivo del administrador y
    el envío de una notificación a los dispositivos de los participantes para que realicen la simulación.
    
    
    """
    data = ParameterGroupSerializer(data=request.data)
    if data.is_valid():
        #1
        parameters = data.validated_data["parameter"]
        id_group = request.data.get("actual_group")
        locations = Device.objects.filter(actual_group=id_group)
        refpoint = RefPoint.objects.filter(actual_group=id_group)
        locations_serializer = DeviceSerializer(locations, many=True)
        refpoint_serializer = RefPointSerializer(refpoint, many=True)
        refpoint_data = refpoint_serializer.data

        #2
        dvice = pd.DataFrame(locations_serializer.data)
        imagen_instance = get_object_or_404(Imagen, id=parameters["idPath"])
        image_path = "./media/" + imagen_instance.archivo.name
        tokenFCM = list(dvice["tokenFCM"])
        dvice = dvice.drop(
            ["id", "device_id", "actual_group", "modified_at", "tokenFCM", "distance"], axis=1
        )
        array = np.array(dvice).astype(float)
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

        #3
        message = messaging.MulticastMessage(tokens=tokenFCM)
        response = messaging.send_each_for_multicast(message)
        #print(response.responses[0].exception)
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
