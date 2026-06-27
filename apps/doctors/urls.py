from django.urls import path
from . import views

urlpatterns = [
    # Pasien
    path('dokter/', views.dokter_list_view, name='dokter_list'),
    path('dokter/<int:pk>/', views.dokter_detail_view, name='dokter_detail'),

    # Admin — Jenis Layanan
    path('admin-panel/jenis-layanan/', views.admin_layanan_list, name='admin_layanan_list'),
    path('admin-panel/jenis-layanan/tambah/', views.admin_layanan_create, name='admin_layanan_create'),
    path('admin-panel/jenis-layanan/<int:pk>/edit/', views.admin_layanan_edit, name='admin_layanan_edit'),
    path('admin-panel/jenis-layanan/<int:pk>/hapus/', views.admin_layanan_delete, name='admin_layanan_delete'),

    # Admin — Dokter
    path('admin-panel/dokter/', views.admin_dokter_list, name='admin_dokter_list'),
    path('admin-panel/dokter/tambah/', views.admin_dokter_create, name='admin_dokter_create'),
    path('admin-panel/dokter/<int:pk>/edit/', views.admin_dokter_edit, name='admin_dokter_edit'),
    path('admin-panel/dokter/<int:pk>/hapus/', views.admin_dokter_delete, name='admin_dokter_delete'),

    # Admin — Jadwal Dokter
    path('admin-panel/dokter/<int:dokter_id>/jadwal/', views.admin_jadwal_list, name='admin_jadwal_list'),
    path('admin-panel/dokter/<int:dokter_id>/jadwal/tambah/', views.admin_jadwal_create, name='admin_jadwal_create'),
    path('admin-panel/dokter/<int:dokter_id>/jadwal/<int:pk>/edit/', views.admin_jadwal_edit, name='admin_jadwal_edit'),
    path('admin-panel/dokter/<int:dokter_id>/jadwal/<int:pk>/hapus/', views.admin_jadwal_delete, name='admin_jadwal_delete'),
]
