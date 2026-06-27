from django.urls import path
from . import views

urlpatterns = [
    path('admin-panel/laporan/', views.laporan_view, name='admin_laporan'),
    path('admin-panel/laporan/export/excel/', views.export_excel, name='export_excel'),
    path('admin-panel/laporan/export/pdf/', views.export_pdf, name='export_pdf'),
]
