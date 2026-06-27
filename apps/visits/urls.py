from django.urls import path
from . import views

urlpatterns = [
    path('riwayat/', views.riwayat_list_view, name='riwayat_list'),
]
