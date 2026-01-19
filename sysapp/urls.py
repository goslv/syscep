# sysapp/urls.py

from django.urls import path

from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Alumnos
    path('alumnos/', views.lista_alumnos, name='lista_alumnos'),
    path('alumnos/crear/', views.crear_alumno, name='crear_alumno'),
    path('alumnos/<int:alumno_id>/', views.detalle_alumno, name='detalle_alumno'),
    path('alumnos/<int:alumno_id>/editar/', views.editar_alumno, name='editar_alumno'),
    path('buscar-alumno/', views.buscar_alumno, name='buscar_alumno'),

    # Pagos
    path('pagos/', views.lista_pagos, name='lista_pagos'),
    path('pagos/registrar/', views.registrar_pago, name='registrar_pago'),
    path('detalle/<int:id>/', views.detalle_pago, name='detalle_pago'),
    path('editar/<int:id>/', views.editar_pago, name='editar_pago'),
    path('eliminar/<int:id>/', views.eliminar_pago, name='eliminar_pago'),

    # Funcionarios
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/crear/', views.crear_funcionario, name='crear_funcionario'),
    path('funcionarios/asistencia/', views.registrar_asistencia, name='registrar_asistencia'),
    path('funcionarios/asistencias/', views.lista_asistencias, name='lista_asistencias'),

    # Sedes
    path('sedes/', views.lista_sedes, name='lista_sedes'),
    path('sedes/crear/', views.crear_sede, name='crear_sede'),
    path('sedes/<int:sede_id>/rendicion/', views.rendicion_sede, name='rendicion_sede'),

    # Carreras y Materias
    path('carreras/', views.lista_carreras, name='lista_carreras'),
    path('carreras/crear/', views.crear_carrera, name='crear_carrera'),
    path('carreras/<int:carrera_id>/', views.detalle_carrera, name='detalle_carrera'),
    path('carreras/<int:carrera_id>/materias/crear/', views.crear_materia, name='crear_materia'),
    path('materias/<int:materia_id>/editar/', views.editar_materia, name='editar_materia'),
    path('materias/<int:materia_id>/asignar-docente/', views.asignar_docente, name='asignar_docente'),

    # Usuarios
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/cambiar-estado/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
]