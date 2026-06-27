from django.urls import path
from . import views

urlpatterns = [
    # Pasien auth
    path('login/', views.login_view, name='login'),
    path('daftar/', views.register_view, name='daftar'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profil_view, name='profil'),

    # Admin auth
    path('admin-panel/login/', views.admin_login_view, name='admin_login'),
    path('admin-panel/logout/', views.admin_logout_view, name='admin_logout'),

    # Admin — kelola user
    path('admin-panel/users/', views.admin_user_list, name='admin_user_list'),
    path('admin-panel/users/tambah/', views.admin_user_create, name='admin_user_create'),
    path('admin-panel/users/<int:pk>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin-panel/users/<int:pk>/hapus/', views.admin_user_delete, name='admin_user_delete'),
]
