from django.test import TestCase
from .models import Device, Group, Admin, RefPoint, Imagen, Parameters
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from .functions import *
import unittest


class DeviceModelTestCase(TestCase):
    def setUp(self):
        self.group = Group.objects.create(Group="Grupo de prueba")
        self.device = Device.objects.create(
            device_id="12345",
            tokenFCM="token12345",
            latitude=10.0,
            longitude=20.0,
            altitude=30.0,
            distance=40.0,
            actual_group=self.group,
        )

    def test_device_creation(self):
        # Se verifica que el dispositivo se haya creado correctamente
        self.assertTrue(isinstance(self.device, Device))
        self.assertEqual(self.device.device_id, "12345")
        self.assertEqual(self.device.tokenFCM, "token12345")
        self.assertEqual(self.device.latitude, 10.0)
        self.assertEqual(self.device.longitude, 20.0)
        self.assertEqual(self.device.altitude, 30.0)
        self.assertEqual(self.device.distance, 40.0)
        self.assertEqual(self.device.actual_group, self.group)

    def test_device_with_group(self):
        # Se verifica la relación
        self.assertEqual(self.device.actual_group, self.group)

class GroupModelTestCase(TestCase):
    def setUp(self):
        self.group = Group.objects.create(Group="Grupo A")

    def test_group_creation(self):
        # Se verifica que se haya creado correctamente
        group = Group.objects.get(Group="Grupo A")
        self.assertTrue(isinstance(group, Group))
        self.assertEqual(self.group.Group, "Grupo A")

    def test_group_unique(self):
        # Se verifica que el grupo sea unico
        Group.objects.create(Group="Grupo B")
        with self.assertRaises(ValidationError):
            group = Group(Group="Grupo A")
            group.full_clean()  # Falla porque el grupo A ya existe

    def test_last_time_used_float(self):
        # Se verifica que last time used almacena un flotante
        group = Group.objects.get(Group="Grupo A")
        group.last_time_used = 123.456
        group.save()
        self.assertEqual(group.last_time_used, 123.456)

class AdminModelTestCase(TestCase):
    def setUp(self):
        Admin.objects.create(username="admin_user", password="pass1")

    def test_admin_creation(self):
        # Se verifica que se haya creado correctamente
        admin = Admin.objects.get(username="admin_user")
        self.assertTrue(isinstance(admin, Admin))
        self.assertEqual(admin.username, "admin_user")

class RefPointModelTestCase(TestCase):
    def setUp(self):
        self.group = Group.objects.create(Group="Grupo de Prueba")

    def test_refpoint_creation(self):
        ref_point = RefPoint.objects.create(
            latitude=10.0,
            longitude=20.0, 
            altitude=30.0, 
            actual_group=self.group
        )

        self.assertTrue(isinstance(ref_point, RefPoint))
        self.assertEqual(ref_point.latitude, 10.0)
        self.assertEqual(ref_point.longitude, 20.0)
        self.assertEqual(ref_point.altitude, 30.0)
        self.assertEqual(ref_point.actual_group, self.group)

class ImagenModelTestCase(TestCase):
    def setUp(self):
        self.image = SimpleUploadedFile(
            name="test_image_MODEL_.png",
            content=open("./media/img/cat.png", "rb").read(),
            content_type="image/png",
        )

    def test_imagen_creation(self):
        # Crear una instancia de imagen
        imagen = Imagen.objects.create(archivo=self.image)
        self.assertTrue(isinstance(imagen, Imagen))
        self.assertTrue(imagen.archivo.url, "./media/img/test_image.jpg")


    def tearDown(self):
        # Se limpia la db de prueba
        try:
            self.image.close()
        except:
            pass

class ParametersModelTestCase(TestCase):
    def test_parameters_creation(self):
        params = Parameters.objects.create(
            observationTime=1.5,
            declination=2.5,
            samplingTime=3.5,
            frequency=4.5,
            idPath=1,
            groupId=10,
            scale=5.5,
        )

        # Verifica que los campos se guarden correctamente
        self.assertEqual(params.observationTime, 1.5)
        self.assertEqual(params.declination, 2.5)
        self.assertEqual(params.samplingTime, 3.5)
        self.assertEqual(params.frequency, 4.5)
        self.assertEqual(params.idPath, 1)
        self.assertEqual(params.scale, 5.5)

    def test_parameters_groupId_unique(self):
        # Se verifica que solo exista una entidad paremeter con un unico groupID
        Parameters.objects.create(groupId=20)

        with self.assertRaises(ValidationError):
            duplicate_params = Parameters(groupId=20)
            duplicate_params.full_clean()

class ParametersViewSetTestCase(APITestCase):
    def setUp(self):
        self.parameter1 = Parameters.objects.create(groupId=100, observationTime=1.5)
        self.parameter2 = Parameters.objects.create(groupId=200, observationTime=2.5)

    def test_get_parameters_list(self):
        # Prueba obtener la lista de Parameters
        url = reverse("parameters-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_parameter_detail(self):
        # Prueba obtener un Parameter
        url = reverse("parameters-detail", kwargs={"groupId": self.parameter1.groupId})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["groupId"], self.parameter1.groupId)

    def test_create_parameter(self):
        # Prueba crear un nuevo Parameter
        url = reverse("parameters-list")
        data = {"groupId": 300, "observationTime": 3.5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Parameters.objects.count(), 3)

    def test_update_parameter(self):
        # Prueba actualizar un Parameter
        url = reverse("parameters-detail", kwargs={"groupId": self.parameter1.groupId})
        data = {"observationTime": 4.5}
        response = self.client.patch(url, data)
        self.parameter1.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.parameter1.observationTime, 4.5)

    def test_delete_parameter(self):
        # Prueba borrar un Parameter
        url = reverse("parameters-detail", kwargs={"groupId": self.parameter1.groupId})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Parameters.objects.filter(groupId=self.parameter1.groupId).exists()
        )

    def tearDown(self):
        pass

class ImagenViewSetTestCase(APITestCase):
    def setUp(self):
        self.image_file = SimpleUploadedFile(
            name="test_image_viewset2_.png",
            content=open("./media/img/cat.png", "rb").read(),
            content_type="image/png",
        )
        self.imagen = Imagen.objects.create(archivo=self.image_file)

    def test_create_image(self):
        # Prueba crear una nueva Imagen
        url = reverse("imagen-list")
        data = {
            "archivo": SimpleUploadedFile(
                name="test_image_viewset2_.png",
                content=open("./media/img/cat.png", "rb").read(),
                content_type="image/png",
            )
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Imagen.objects.count(), 2)

    def test_get_image_list(self):
        # Prueba obtener una lista de Imagenes
        url = reverse("imagen-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) #se verifica cantidad de imagenes

    def test_update_image(self):
        # Prueba actualizar una Imagen existente
        url = reverse("imagen-detail", args=[self.imagen.id])
        data = {
            "archivo": SimpleUploadedFile(
                name="test_image_viewset_RE_.png",
                content=open("./media/img/cat.png", "rb").read(),
                content_type="image/png",
            )
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_image(self):
        # Prueba borrar una Imagen
        url = reverse("imagen-detail", args=[self.imagen.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Imagen.objects.exists())

    def tearDown(self):
        self.imagen.archivo.delete(save=False)

class RefPointViewSetTestCase(APITestCase):

    def setUp(self):
        self.group = Group.objects.create(Group='Grupo de Prueba')

        self.ref_point = RefPoint.objects.create(
            latitude=10.0,
            longitude=20.0,
            altitude=30.0,
            actual_group=self.group
        )

    def test_get_refpoint_list(self):
        # Prueba obtener una lista de refpoint
        url = reverse('refpoint-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) #se verifica cantidad de ref ponts

    def test_get_refpoint_detail(self):
        # Prueba obtener un refpoint
        url = reverse('refpoint-detail', kwargs={'actual_group': self.ref_point.actual_group_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['latitude'], self.ref_point.latitude)

    def test_create_refpoint(self):
        # Prueba crear un nuevo refpoint
        self.group = Group.objects.create(Group='Grupo de Prueba 2')
        url = reverse('refpoint-list')
        data = {
            'latitude': 40.0,
            'longitude': 50.0,
            'altitude': 60.0,
            'actual_group': self.group.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RefPoint.objects.count(), 2)

    def test_update_refpoint(self):
        # Prueba actualizar un refpoint existente
        url = reverse('refpoint-detail', kwargs={'actual_group': self.ref_point.actual_group_id})
        data = {'latitude': 70.0}
        response = self.client.patch(url, data)
        self.ref_point.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ref_point.latitude, 70.0)

    def test_delete_refpoint(self):
        # Prueba borrar un refpoint
        url = reverse('refpoint-detail', kwargs={'actual_group': self.ref_point.actual_group_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RefPoint.objects.filter(actual_group=self.ref_point.actual_group_id).exists())


    def tearDown(self):
        pass

class AdminViewSetTestCase(APITestCase):

    def setUp(self):
        self.admin = Admin.objects.create(username='admin1', password='password1')

    def test_get_admin_list(self):
        # Prueba obtener la lista de admins
        url = reverse('admin-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_admin_detail(self):
        # Prueba obtener un admin
        url = reverse('admin-detail', args=[self.admin.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.admin.username)

    def test_create_admin(self):
        # Prueba crear un nuevo admin
        url = reverse('admin-list')
        data = {'username': 'admin2', 'password': 'password2'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Admin.objects.count(), 2)

    def test_update_admin(self):
        # Prueba actualizar un admin existente
        url = reverse('admin-detail', args=[self.admin.id])
        data = {'username': 'admin_updated'}
        response = self.client.patch(url, data)
        self.admin.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.admin.username, 'admin_updated')

    def test_delete_admin(self):
        # Prueba borrar un admin
        url = reverse('admin-detail', args=[self.admin.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Admin.objects.filter(id=self.admin.id).exists())

    def tearDown(self):
        pass

class GroupRetrieveViewTestCase(APITestCase):

    def setUp(self):
        self.group1 = Group.objects.create(Group='Grupo A')
        self.group2 = Group.objects.create(Group='Grupo B')

        self.device1 = Device.objects.create(device_id='1', actual_group=self.group1, modified_at=timezone.now() - timedelta(hours=2))
        Device.objects.create(device_id='2', actual_group=self.group2, modified_at=timezone.now() - timedelta(days=1, hours=3))

    def test_get_groups_with_last_time_used(self):

        url = reverse('group-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for group_data in response.data:
            group = Group.objects.get(id=group_data['id'])
            expected_last_time_used = 100 if group.device_set.first() is None else (timezone.now() - group.device_set.first().modified_at).total_seconds() / 3600
            self.assertAlmostEqual(group_data['last_time_used'], expected_last_time_used, places=2)

    def tearDown(self):
        pass

class DeviceViewSetTestCase(APITestCase):

    def setUp(self):
        self.group1 = Group.objects.create(Group='Grupo A')
        self.group2 = Group.objects.create(Group='Grupo B')

        self.device1 = Device.objects.create(device_id='1', actual_group=self.group1)
        self.device2 = Device.objects.create(device_id='2', actual_group=self.group2)

    def test_filter_devices_by_group(self):
        # Prueba filtrar dispositivos por grupo
        url = reverse('register-list') + '?actual_group=' + str(self.group1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_device(self):
        # Prueba actualizar un dispositivo
        url = reverse('register-detail', args=[self.device1.id])
        data = {'device_id': '1', 'actual_group': self.group1.id}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.device1.refresh_from_db()

    def test_delete_devices_by_group(self):
        # Prueba eliminar dispositivos por grupo
        url = reverse('register-delete_by_group') + '?actual_group=' + str(self.group1.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Device.objects.filter(actual_group=self.group1).count(), 0)

    def tearDown(self):
        pass

class MessageViewTestCase(APITestCase):

    def setUp(self):
        self.group1 = Group.objects.create(Group='Grupo A')
        self.group2 = Group.objects.create(Group='Grupo B')

        Device.objects.create(device_id='1', tokenFCM='token1', actual_group=self.group1)
        Device.objects.create(device_id='4', tokenFCM='token3', actual_group=self.group1)
        Device.objects.create(device_id='2', tokenFCM='token2', actual_group=self.group2)

    @patch('interferometer.views.MessageView')
    def test_send_message_to_group(self, mock_messaging):

        # Realizar solicitud de prueba
        url = reverse('message-list') + '?actual_group=' + str(self.group1.id)
        response = self.client.get(url)

        # Verificar
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        pass

class DoSimulationTestCase(APITestCase):

    def setUp(self):
        self.image_file = SimpleUploadedFile(
            name='test_image_SIM_.png',
            content=open("./media/img/cat.png", 'rb').read(),
            content_type='image/png'
        )
        self.imagen = Imagen.objects.create(archivo=self.image_file)

    def test_do_simulation_with_valid_data(self):
        url = reverse('simulation')
        data = {
            'locations': [{"latitude": -41.464183, "longitude": -72.919694, "altitude": 0.0, "distance": 0.0},{
                "latitude": -41.464507, "longitude": -72.919898, "altitude": 0.0, "distance": 0.0
            }],
            "reference": {"latitude": -41.463874, "longitude": -72.920166, "altitude": 0.0},
            "parameter": {
                "idPath": self.imagen.id,
                "scale": 1.0,
                "observationTime": 2,
                "declination": 40,
                "samplingTime": 6,
                "frequency": 90
            }
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        self.imagen.archivo.delete(save=False)

class TestCalcRR(unittest.TestCase):

    def test_scalar_input(self):
        H = 0.
        dec = 10
        expected_output = np.array([[[ 0.],[ 1.],[ 0.]],
                                    [[ 0.54402111],[-0.],[-0.83907153]],
                                    [[-0.83907153],[ 0.],[-0.54402111]]])
        result = calc_RR(H, dec)
        np.testing.assert_array_almost_equal(result, expected_output)

    def test_array_input(self):
        H = np.array([1.0, 2.0])
        dec = 10
        expected_output = np.array([[[ 0.84147098,  0.90929743],
        [ 0.54030231, -0.41614684],
        [ 0.        ,  0.        ]],

       [[ 0.29393586, -0.22639266],
        [-0.45777798, -0.494677  ],
        [-0.83907153, -0.83907153]],

       [[-0.45335228,  0.34917696],
        [ 0.70605435,  0.76296558],
        [-0.54402111, -0.54402111]]])
        result = calc_RR(H, dec)
        np.testing.assert_array_almost_equal(result, expected_output)

class TestComputeH(unittest.TestCase):

    def test_compute_h(self):
        hObs = 1
        gradDec = 25
        t_muestreo = 60

        HA, dec = compute_h(hObs, gradDec, t_muestreo)

        expected_HA = np.array([-0.26179939,  0.])
        expected_dec = np.radians(25)

        np.testing.assert_array_almost_equal(HA, expected_HA)
        np.testing.assert_array_almost_equal(dec, expected_dec)

class TestNewPositions(unittest.TestCase):

    def test(self):
        df = np.array([[40.7128, -74.0060, 0], [34.0522, -118.2437, 0]]) 
        reference = [40.7128, -74.0060]  
        scale = 5.0  
        expected_output = np.array([[  40.7128    ,  -74.006     ,    0.        ],
       [ -40.48624954, -250.03289698,    0.        ]]) 
        result = new_positions(df, reference, scale)
        np.testing.assert_array_almost_equal(result, expected_output)

class TestEnuToLocalAltAz(unittest.TestCase):

    def test(self):
        enu_baselines = np.array([10, 10, 5])
        distance = 15

        expected_elevation = np.arctan2(enu_baselines[0], enu_baselines[1])
        expected_azimuth = np.arcsin(enu_baselines[2] / distance)
        elevation, azimuth = enu_to_local_altaz(enu_baselines, distance)
        

        self.assertAlmostEqual(elevation, expected_elevation)
        self.assertAlmostEqual(azimuth, expected_azimuth)

class TestBaselines(unittest.TestCase):

    def test(self):
        base = np.array([[ 3.94325154e+01,  2.23895371e+01],
       [-3.43190792e+01, -7.03039494e+01],
       [ 2.14257584e-04,  4.27596239e-04]])

        expected_output = np.array([[ 1.70429783e+01, -1.70429783e+01],
       [ 3.59848702e+01, -3.59848702e+01],
       [-2.13338655e-04,  2.13338655e-04]])
        result = baselines(base)
        np.testing.assert_array_almost_equal(result, expected_output)

class TestEarthLocationToENU(unittest.TestCase):

    def setUp(self):

        data = [
            [-41.464183, -72.919694, 100],
            [-41.464507, -72.919898, 100],]
        
        data = np.array(data)
        ref = np.array((-41.463874,-72.920166,100))
        self.ant_pos = EarthLocation.from_geodetic(data[:,1], data[:,0], data[:,2])
        self.ref_loc = EarthLocation.from_geodetic(ref[1],ref[0],ref[2])

    def test_earth_location_to_local_enu_integration(self):

        expected_output = np.array([[ 3.94325154e+01,  2.23895371e+01],
                                    [-3.43190792e+01, -7.03039494e+01],
                                    [ 2.14257584e-04,  4.27596239e-04]])

        result = earth_location_to_local_enu(self.ant_pos, self.ref_loc)

        self.assertIsInstance(result, np.ndarray)
        np.testing.assert_array_almost_equal(result, expected_output)

class TestGeodeticToENU(unittest.TestCase):

    def setUp(self):

        data = [[-41.464183, -72.919694, 100],
                [-41.464507, -72.919898, 100],]
        
        self.data = np.array(data)
        self.ref = np.array((-41.463874,-72.920166,100))

    def test_geodetic_to_enu(self):

        expected_output = np.array([[ 3.94325154e+01,  2.23895371e+01],
                                    [-3.43190792e+01, -7.03039494e+01],
                                    [ 2.14257584e-04,  4.27596239e-04]])

        result = geodetic_to_enu(self.data, self.ref)

        self.assertIsInstance(result, np.ndarray)
        np.testing.assert_array_almost_equal(result, expected_output)

class TestBaselinesEquatorial(unittest.TestCase):

    def setUp(self):

        self.base_enu = np.array([[ 1.70429783e+01, -1.70429783e+01],
       [ 3.59848702e+01, -3.59848702e+01],
       [-2.13338654e-04,  2.13338654e-04]])
        
        self.latitude = -41.463874

    def test_baselines_enu_to_equatorial(self):

        expected_output = np.array([[ 23.8271387 , -23.8271387 ],
                                    [ 17.0429783 , -17.0429783 ],
                                    [ 26.96624456, -26.96624456]])

        result = bENU_to_bEquatorial(self.base_enu, self.latitude)

        self.assertIsInstance(result, np.ndarray)
        np.testing.assert_array_almost_equal(result, expected_output)

class TestCoverage(unittest.TestCase):

    def setUp(self):
        self.base_equ = np.array([[ 23.8271387 , -23.8271387 ],
                                  [ 17.0429783 , -17.0429783 ],
                                  [ 26.96624456, -26.96624456]])
        self.H = 0.
        self.dec = 45
        self.wavelength = 0.003199492614727855
    
    def test_coverage(self):
        
        expected_output = np.array([[ 5326.7753202 , -1909.25118752],
                                    [-5326.7753202 ,  1909.25118752]])
        
        result, _ = coverage(self.base_equ, self.H, self.dec, self.wavelength)

        np.testing.assert_array_almost_equal(result, expected_output)

class TestGridSampling(unittest.TestCase):

    def setUp(self):
        self.pixel = 10
        self.max_base_equ = 26.966244558974477
        self.wavelength = 0.003199492614727855
        self.coverage = np.array([[ 5326.7753202 , -1909.25118752],
                                  [-5326.7753202 ,  1909.25118752]])
    
    def test_grid_sampling(self):

        expected_output = np.array([[0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j],
                                    [0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j,0.+0.j, 0.+0.j]])
        
        result, _ ,_ = grid_sampling(self.pixel, self.max_base_equ,self.coverage,self.wavelength)

        np.testing.assert_array_almost_equal(result, expected_output)






