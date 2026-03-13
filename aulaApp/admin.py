from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(TipoUsuario)
admin.site.register(Usuario)
admin.site.register(Asignatura)
admin.site.register(ClasesAgendadas)
admin.site.register(ComprobantePago)