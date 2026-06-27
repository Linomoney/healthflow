from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),

    # Admin
    path('admin-panel/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/banner/', views.admin_banner_list, name='admin_banner_list'),
    path('admin-panel/banner/tambah/', views.admin_banner_create, name='admin_banner_create'),
    path('admin-panel/banner/<int:pk>/edit/', views.admin_banner_edit, name='admin_banner_edit'),
    path('admin-panel/banner/<int:pk>/hapus/', views.admin_banner_delete, name='admin_banner_delete'),
    path('admin-panel/klinik/', views.admin_klinik_list, name='admin_klinik_list'),
    path('admin-panel/klinik/tambah/', views.admin_klinik_create, name='admin_klinik_create'),
    path('admin-panel/klinik/<int:pk>/edit/', views.admin_klinik_edit, name='admin_klinik_edit'),
    path('admin-panel/klinik/<int:pk>/hapus/', views.admin_klinik_delete, name='admin_klinik_delete'),
]
