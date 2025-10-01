from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('gallos/ajax/', views.gallo_list_ajax, name='gallo_list_ajax'),
    path('ver/<int:idGallo>/', views.ver, name='ver'),
    path('crear/', views.crear, name='crear'),
    path('editar/<int:idGallo>/', views.editar, name='editar'),
    path('eliminar/<int:idGallo>/', views.eliminar, name='eliminar'),
    path('comprobarNroPLaca/', views.ajax_valida_placa, name='ajax_valida_placa'),
    path('gallo/<int:idGallo>/upload-archivo/', views.upload_archivo_adicional, name='upload_archivo_adicional'),
    path('archivo/<int:archivo_id>/delete/', views.delete_archivo_adicional, name='delete_archivo_adicional'),
    path('ajax/padres/', views.padres_modal_content, name='padres_modal_content'),
    path('ajax/madres/', views.madres_modal_content, name='madres_modal_content'),

    #encuentros
    path('encuentros/', views.listar_encuentros, name='listar_encuentros'),
    path('encuentros/<int:pk>/', views.ver_encuentro, name='ver_encuentro'),
    path('encuentros/nuevo/', views.crear_encuentro, name='crear_encuentro'),
    path('encuentros/editar/<int:pk>/', views.encuentro_form, name='editar_encuentro'),
    path('encuentros/eliminar/<int:pk>/', views.eliminar_encuentro, name='eliminar_encuentro'),
    path('export-db/', views.export_db, name='export_db'),
    path('ajax/participantes/', views.participantes_modal_content, name='participantes_modal_content'),

    #colores
    path('color', views.color_list, name='color_list'),
    path('color/nuevo/', views.color_create, name='color_create'),
    path('color/<int:pk>/editar/', views.color_edit, name='color_edit'),
    path('color/nuevo/ajax/', views.color_create_ajax, name='color_create_ajax'),

    #estados
    path('estado', views.estado_list, name='estado_list'),
    path('estado/nuevo/', views.estado_create, name='estado_create'),
    path('estado/<int:pk>/editar/', views.estado_edit, name='estado_edit'),
    path('estado/nuevo/ajax/', views.estado_create_ajax, name='estado_create_ajax'),

    # Galpones
    path('galpon', views.galpon_list, name='galpon_list'),
    path('galpon/nuevo/', views.galpon_create, name='galpon_create'),
    path('galpon/<int:pk>/editar/', views.galpon_edit, name='galpon_edit'),
    path('galpon/nuevo/ajax/', views.galpon_create_ajax, name='galpon_create_ajax'),

    # URLs para dueños
    #path('dueno', views.dueno_list, name='dueno_list'),
    #path('dueno/nuevo/', views.dueno_create, name='dueno_create'),
    #path('dueno/<int:pk>/editar/', views.dueno_edit, name='dueno_edit'),
    #path('dueno/nuevo/ajax/', views.dueno_create_ajax, name='dueno_create_ajax'),

    # dueños anteriores
    path('duenoanterior/', views.duenoanterior_list, name='duenoanterior_list'),
    path('duenoanterior/nuevo/', views.duenoanterior_create, name='duenoanterior_create'),
    path('duenoanterior/<int:pk>/editar/', views.duenoanterior_edit, name='duenoanterior_edit'),
    path('duenoanterior/nuevo/ajax/', views.duenoanterior_create_ajax, name='duenoanterior_create_ajax'),

    path('export-db/', views.export_db, name='export_db'),

    path('placa/nuevo/ajax/', views.placa_create_ajax, name='placa_create_ajax'),
    path('peso/nuevo/ajax/', views.peso_create_ajax, name='peso_create_ajax'),

    path('filtros/', views.filtros, name='filtros_gallos'),
]
