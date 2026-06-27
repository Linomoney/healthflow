from django.urls import path
from . import views

urlpatterns = [
    # Pasien
    path('reservasi/buat/<int:jadwal_id>/', views.reservasi_create_view, name='reservasi_create'),
    path('antrean/saya/', views.antrean_saya_view, name='antrean_saya'),
    path('antrean/saya/partial/', views.antrean_saya_partial, name='antrean_saya_partial'),
    path('antrean/<int:pk>/batalkan/', views.batalkan_antrean_view, name='batalkan_antrean'),

    # Admin
    path('admin-panel/antrean/', views.admin_antrean_view, name='admin_antrean'),
    path('admin-panel/antrean/partial/', views.admin_antrean_partial, name='admin_antrean_partial'),
    path('admin-panel/antrean/panggil/<int:dokter_id>/', views.admin_panggil_antrean, name='admin_panggil_antrean'),
    path('admin-panel/antrean/<int:pk>/selesai/', views.admin_selesai_antrean, name='admin_selesai_antrean'),
    path('admin-panel/antrean/<int:pk>/reset/', views.admin_reset_antrean, name='admin_reset_antrean'),
    path('admin-panel/antrean/<int:pk>/admin-batalkan/', views.admin_batalkan_antrean, name='admin_batalkan_antrean'),
]
