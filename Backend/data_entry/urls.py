from django.urls import path
from . import views

urlpatterns = [
    # Beranda data entry
    path('',                         views.index,           name='data_entry_index'),

    # Pengguna (Parent) CRUD
    path('pengguna/',                views.pengguna_list,   name='pengguna_list'),
    path('pengguna/tambah/',         views.set_pengguna,    name='set_pengguna'),    # sesuai nama di PDF
    path('pengguna/<int:pk>/',       views.detail_pengguna, name='pengguna_detail'),
    path('pengguna/<int:pk>/edit/',  views.edit_pengguna,   name='edit_pengguna'),
    path('pengguna/<int:pk>/hapus/', views.hapus_pengguna,  name='hapus_pengguna'),

    # Content (Child) CRUD
    path('content/',                 views.content_list,    name='content_list'),
    path('content/tambah/',          views.set_content,     name='set_content'),     # sesuai PDF
    path('content/<int:pk>/',        views.detail_content,  name='content_detail'),
    path('content/<int:pk>/edit/',   views.edit_content,    name='edit_content'),
    path('content/<int:pk>/hapus/',  views.hapus_content,   name='hapus_content'),
]
