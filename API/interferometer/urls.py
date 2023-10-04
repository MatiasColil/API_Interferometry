from django.urls import path
from . import views

urlpatterns = [
    path('matrix_sum/', views.calculate_centroid),
]
