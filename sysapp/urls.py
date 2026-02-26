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
    path('alumnos/<uuid:alumno_uuid>/', views.detalle_alumno, name='detalle_alumno'),
    path('alumnos/<uuid:alumno_uuid>/editar/', views.editar_alumno, name='editar_alumno'),
    path('alumnos/<uuid:alumno_uuid>/canjear-estrellas/', views.canjear_estrellas, name='canjear_estrellas'),
    path('buscar-alumno/', views.buscar_alumno, name='buscar_alumno'),
    path('alumno/<uuid:alumno_uuid>/ficha/', views.ficha_alumno, name='ficha_alumno'),
    path('alumno/<uuid:alumno_uuid>/ficha/editar/', views.editar_datos_ficha, name='editar_datos_ficha'),

    # Caja (Ingresos y Egresos)
    path('caja/', views.lista_caja, name='lista_caja'),
    path('caja/informe/', views.informe_caja, name='informe_caja'),

    # Egresos
    path('egresos/', views.lista_egresos, name='lista_egresos'),
    path('egresos/registrar/', views.registrar_egreso, name='registrar_egreso'),
    path('egresos/<uuid:egreso_uuid>/', views.detalle_egreso, name='detalle_egreso'),
    path('egresos/<uuid:egreso_uuid>/editar/', views.editar_egreso, name='editar_egreso'),
    path('egresos/<uuid:egreso_uuid>/eliminar/', views.eliminar_egreso, name='eliminar_egreso'),

    # Pagos
    path('pagos/', views.lista_pagos, name='lista_pagos'),
    path('pagos/registrar/', views.registrar_pago, name='registrar_pago'),
    path('pagos/<uuid:pago_uuid>/', views.detalle_pago, name='detalle_pago'),
    path('pagos/<uuid:pago_uuid>/editar/', views.editar_pago, name='editar_pago'),
    path('pagos/<uuid:pago_uuid>/eliminar/', views.eliminar_pago, name='eliminar_pago'),
    path('cuentas-bancarias/', views.cuentas_bancarias, name='cuentas_bancarias'),

    # Funcionarios
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/crear/', views.crear_funcionario, name='crear_funcionario'),
    path('funcionarios/asistencia/', views.registrar_asistencia, name='registrar_asistencia'),
    path('funcionarios/asistencias/', views.lista_asistencias, name='lista_asistencias'),
    path('funcionarios/<int:funcionario_id>/', views.detalle_funcionario, name='detalle_funcionario'),
    path('funcionarios/<int:funcionario_id>/editar/', views.editar_funcionario, name='editar_funcionario'),

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
    path('materias/<int:materia_id>/asignar-fechas/', views.asignar_fechas, name='asignar_fechas'),

    # Usuarios
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/solicitudes-eliminacion/', views.lista_solicitudes_eliminacion, name='lista_solicitudes_eliminacion'),
    path('usuarios/solicitudes-eliminacion/<int:solicitud_id>/procesar/', views.procesar_solicitud_eliminacion, name='procesar_solicitud_eliminacion'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/perfil/', views.mi_perfil, name='mi_perfil'),
    path('usuarios/configuracion/', views.configuracion, name='configuracion'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/cambiar-estado/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),


]