from django.contrib import admin
from .models import Personal, Sexo, EstadoCivil, InfoLaboral, Cargo, DeptoEmpresa, Ausentismo, TipoAusentismo, Proveedor, TipoClasificacion, ClasificacionProveedor, TipoExamen, ResultadoExamen, Examen, TipoCertificacion, Certificacion, TipoLicencia, ClaseLicencia, LicenciaPorPersonal


# Register your models here.


admin.site.register(Sexo)
admin.site.register(EstadoCivil)
admin.site.register(Personal)
admin.site.register(InfoLaboral)
admin.site.register(Cargo)
admin.site.register(DeptoEmpresa)
admin.site.register(Ausentismo)
admin.site.register(TipoAusentismo)
admin.site.register(Proveedor)
admin.site.register(TipoClasificacion)
admin.site.register(ClasificacionProveedor)
admin.site.register(TipoExamen)
admin.site.register(ResultadoExamen)
admin.site.register(Examen)
admin.site.register(TipoCertificacion)
admin.site.register(Certificacion)
admin.site.register(TipoLicencia)
admin.site.register(ClaseLicencia)
admin.site.register(LicenciaPorPersonal)





