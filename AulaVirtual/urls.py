from django.contrib import admin
from django.urls import path, include
from aulaApp import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls, name="admin"),
    path('', views.home, name="home"),
    path('nosotros/', views.nosotros, name="nosotros"),
    path('estudiante/', views.panel_estudiante, name="estudiante"),
    path('docente/', views.panel_docente, name="docente"),
    path('sala/<int:clase_id>/', views.sala, name="sala"),
    path('docente/horario/', views.gestionar_horario, name='gestionar_horario'),
    path('docente/horario/eliminar/<int:id>/', views.eliminar_horario, name='eliminar_horario'),
    path('editarMiCuenta/', views.editarMiCuenta, name="editarMiCuenta"),
    path('editarUsuarios/', views.editarUsuarios, name="editarUsuarios"),
    path('editarAgendamiento/', views.editarAgendamiento, name="editarAgendamiento"),
    path('buscarProfesor/', views.buscarProfesor, name="buscarProfesor"),
    path('portalPagos/', views.portalPagos, name="portalPagos"),
    path('listaPagosAdmin/', views.listaPagosAdmin, name="listaPagosAdmin"),
    path('clasesAgendadasAdmin/', views.clasesAgendadasAdmin, name="clasesAgendadasAdmin"),
    path('mis_clases_agendadas/', views.mis_clases_agendadas, name="mis_clases_agendadas"),
    path('eliminarUsuarios/', views.eliminarUsuarios, name="eliminarUsuarios"),
    path('mis_clases_agendadas/cancelar_clase/<int:clase_id>/', views.cancelar_clase, name="cancelar_clase"),
    path('profesor/<int:id>/', views.perfil_profesor, name='perfil_profesor'),
    path('reserva/confirmar/<int:horario_id>/', views.confirmar_reserva, name='confirmar_reserva'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/pizarra/guardar/<int:clase_id>/', views.guardar_pizarra, name='guardar_pizarra'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro, name="registro"),
]
