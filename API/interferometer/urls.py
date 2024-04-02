from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView

router = DefaultRouter()
router.register(r'register',views.DeviceViewSet, basename="register")
router.register(r'admin', views.AdminViewSet)
router.register(r'groups', views.GroupRetrieveView)
router.register(r'ref', views.RefPointView)
router.register(r'message', views.MessageView, basename="message")
router.register(r'imagenes', views.ImagenViewSet)
router.register(r'parameters', views.ParametersViewSet)

urlpatterns = [
    path('simulation/', views.simuGuest,name="simulation"),
    path('', include(router.urls)),
    path('auth/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('simuadmin/', views.simuAdmin)
]
