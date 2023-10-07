from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'register',views.DeviceViewSet)

urlpatterns = [
    path('matrix_sum/', views.calculate_centroid),
    path('', include(router.urls)),
]
