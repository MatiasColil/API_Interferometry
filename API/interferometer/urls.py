from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView

router = DefaultRouter()
router.register(r'register',views.DeviceViewSet)
router.register(r'admin', views.AdminViewSet)
router.register(r'groups', views.GroupRetrieveView)

urlpatterns = [
    path('matrix_sum/', views.calculate_centroid),
    path('', include(router.urls)),
    path('auth/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
