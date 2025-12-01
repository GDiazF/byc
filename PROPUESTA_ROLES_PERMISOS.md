# 🎯 PROPUESTA DE IMPLEMENTACIÓN: ROLES Y PERMISOS

## 📋 RESUMEN EJECUTIVO

Propuesta para implementar un sistema de roles y permisos escalable y mantenible en el proyecto BYC, utilizando el sistema nativo de Django con extensiones personalizadas.

### **Caso de Uso Clave: Permisos Granulares**
Ejemplo: **Jefe de RRHH** puede desactivar personal, pero **Trabajador de RRHH** no puede.
- ✅ **Solución**: Permisos personalizados en el modelo (`desactivar_personal`, `activar_personal`)
- ✅ **Implementación**: Definir en `Meta.permissions` del modelo
- ✅ **Aplicación**: Decoradores en vistas + verificación en templates

**Ver sección completa**: [🎯 Permisos Granulares por Acción](#-permisos-granulares-por-acción-caso-desactivar-personal)

### **Gestión desde Admin: Crear Roles y Asignar Permisos**
- ✅ **SÍ**: Puedes crear roles desde el admin de Django
- ✅ **SÍ**: Puedes asignar permisos a roles desde el admin (con widget mejorado)
- ✅ **SÍ**: Al asignar rol a usuario, hereda automáticamente todos los permisos
- ✅ **SÍ**: Si actualizas permisos de un rol, se actualizan en todos los usuarios

**Ver sección completa**: [🎛️ Gestión de Roles desde el Admin](#️-gestión-de-roles-desde-el-admin-de-django)

---

## 🎯 OBJETIVOS

1. **Control de acceso granular** por vista/función
2. **Roles predefinidos** con permisos agrupados
3. **Implementación incremental** por app
4. **Mantenibilidad** y facilidad de uso
5. **Compatibilidad** con el sistema actual de Django

---

## 🏗️ ARQUITECTURA PROPUESTA

### **OPCIÓN 1: Sistema Híbrido (RECOMENDADA)** ⭐

Combina lo mejor de Django Permissions + Modelos de Permisos Personalizados

#### **Estructura:**

```
gen_permissions/          # Nueva app central para permisos
├── models.py            # Rol, PermisoVista, PermisoModelo
├── decorators.py        # @permission_required_custom
├── mixins.py            # PermissionRequiredMixin
├── utils.py             # Funciones helper
└── management/
    └── commands/
        └── crear_permisos.py  # Comando para crear permisos automáticamente
```

#### **Ventajas:**
- ✅ Usa el sistema nativo de Django (ContentType, Permission)
- ✅ Permisos asociados a modelos cuando existe modelo
- ✅ Permisos asociados a "PermisoVista" cuando no hay modelo
- ✅ Decoradores y mixins reutilizables
- ✅ Fácil de migrar gradualmente
- ✅ Compatible con admin de Django

#### **Modelos Propuestos:**

```python
# gen_permissions/models.py

from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

class Rol(models.Model):
    """Roles del sistema (Admin, RRHH, Operaciones, etc.)"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    permisos = models.ManyToManyField(Permission, blank=True)
    
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class PermisoVista(models.Model):
    """Permisos para vistas que NO tienen modelo asociado"""
    codigo = models.CharField(max_length=100, unique=True)  # ej: 'dashboards.view_dashboard'
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    app_label = models.CharField(max_length=100)  # 'dashboards', 'reportes_auditoria'
    vista_nombre = models.CharField(max_length=200)  # 'dashboard_view', 'auditoria_view'
    activo = models.BooleanField(default=True)
    
    # Permission asociado (se crea automáticamente)
    permission = models.OneToOneField(
        Permission,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permiso_vista'
    )
    
    class Meta:
        verbose_name = "Permiso de Vista"
        verbose_name_plural = "Permisos de Vista"
        ordering = ['app_label', 'vista_nombre']
    
    def __str__(self):
        return f"{self.app_label}.{self.vista_nombre}"


class PermisoModelo(models.Model):
    """Catálogo de permisos por modelo (para referencia y documentación)"""
    modelo = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    app_label = models.CharField(max_length=100)
    modelo_nombre = models.CharField(max_length=100)
    permisos_disponibles = models.JSONField(default=dict)  # {'add', 'change', 'delete', 'view'}
    
    class Meta:
        verbose_name = "Permiso de Modelo"
        verbose_name_plural = "Permisos de Modelo"
        unique_together = ['app_label', 'modelo_nombre']
    
    def __str__(self):
        return f"{self.app_label}.{self.modelo_nombre}"


class PermisoAccion(models.Model):
    """Permisos personalizados para acciones específicas dentro de un modelo"""
    codigo = models.CharField(max_length=100, unique=True)  # ej: 'rrhh_personal.desactivar_personal'
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    modelo = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    accion = models.CharField(max_length=100)  # 'desactivar', 'activar', 'exportar', etc.
    activo = models.BooleanField(default=True)
    
    # Permission asociado (se crea automáticamente)
    permission = models.OneToOneField(
        Permission,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permiso_accion'
    )
    
    class Meta:
        verbose_name = "Permiso de Acción"
        verbose_name_plural = "Permisos de Acción"
        ordering = ['modelo', 'accion']
        unique_together = ['modelo', 'accion']
    
    def __str__(self):
        return f"{self.codigo}"


class UserProfile(models.Model):
    """Perfil extendido del usuario con relación a Rol - Asigna permisos automáticamente"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name='Usuario'
    )
    rol = models.ForeignKey(
        Rol, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Rol',
        help_text='Al asignar un rol, se asignan automáticamente todos sus permisos'
    )
    fecha_asignacion_rol = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Asignación de Rol'
    )
    fecha_modificacion_rol = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Modificación de Rol'
    )
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.rol.nombre if self.rol else 'Sin rol'}"
    
    def asignar_permisos_del_rol(self):
        """Asigna automáticamente los permisos del rol al usuario"""
        if self.rol:
            self.user.user_permissions.set(self.rol.permisos.all())
        else:
            self.user.user_permissions.clear()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Asignar permisos automáticamente al guardar
        self.asignar_permisos_del_rol()


# Signals para automatizar la creación y actualización de permisos
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_user_profile(sender, instance, created, **kwargs):
    """Crea automáticamente un UserProfile cuando se crea un User"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=UserProfile)
def actualizar_permisos_usuario(sender, instance, **kwargs):
    """Actualiza los permisos del usuario cuando cambia su rol"""
    instance.asignar_permisos_del_rol()
```

---

### **OPCIÓN 2: Solo Django Permissions (Más Simple)**

Usar únicamente el sistema nativo de Django sin modelos adicionales.

#### **Ventajas:**
- ✅ Más simple
- ✅ Sin migraciones adicionales
- ✅ Integrado con admin

#### **Desventajas:**
- ❌ Menos documentación de permisos
- ❌ Más difícil de gestionar permisos de vistas sin modelo
- ❌ Menos flexible para casos especiales

---

### **OPCIÓN 3: Django-Guardian (Más Complejo)**

Usar librería externa para permisos por objeto.

#### **Ventajas:**
- ✅ Permisos granulares por instancia
- ✅ Muy potente

#### **Desventajas:**
- ❌ Dependencia externa
- ❌ Más complejo de mantener
- ❌ Overkill para la mayoría de casos

---

## 🚀 IMPLEMENTACIÓN RECOMENDADA: OPCIÓN 1

### **FASE 1: Setup Base (1-2 días)**

1. **Crear app `gen_permissions`**
   ```bash
   python manage.py startapp gen_permissions
   ```

2. **Crear modelos base** (Rol, PermisoVista, PermisoModelo)

3. **Crear decoradores y mixins**
   ```python
   # gen_permissions/decorators.py
   from functools import wraps
   from django.core.exceptions import PermissionDenied
   
   def permission_required_custom(permiso_codigo):
       """
       Decorador para verificar permisos personalizados
       Ejemplo: @permission_required_custom('maquinarias.view_equipo')
       """
       def decorator(view_func):
           @wraps(view_func)
           def wrapper(request, *args, **kwargs):
               if not request.user.has_perm(permiso_codigo):
                   raise PermissionDenied
               return view_func(request, *args, **kwargs)
           return wrapper
       return decorator
   ```

4. **Crear comando de gestión**
   ```python
   # gen_permissions/management/commands/crear_permisos.py
   # Comando para crear permisos automáticamente desde modelos y vistas
   ```

5. **Configurar Admin de Django para gestión fácil**
   ```python
   # gen_permissions/admin.py
   from django.contrib import admin
   from django.contrib.auth.models import Permission
   from django.contrib.contenttypes.models import ContentType
   from django.utils.html import format_html
   from .models import Rol, PermisoVista, PermisoModelo, PermisoAccion, UserProfile
   
   @admin.register(Rol)
   class RolAdmin(admin.ModelAdmin):
       list_display = ('nombre', 'descripcion', 'activo', 'permisos_count', 'usuarios_count')
       list_filter = ('activo',)
       search_fields = ('nombre', 'descripcion')
       filter_horizontal = ('permisos',)  # Widget mejorado para seleccionar permisos
       fieldsets = (
           ('Información Básica', {
               'fields': ('nombre', 'descripcion', 'activo')
           }),
           ('Permisos', {
               'fields': ('permisos',),
               'description': 'Selecciona los permisos que tendrán todos los usuarios con este rol'
           }),
       )
       
       def permisos_count(self, obj):
           return obj.permisos.count()
       permisos_count.short_description = 'Cantidad de Permisos'
       
       def usuarios_count(self, obj):
           return obj.userprofile_set.count()
       usuarios_count.short_description = 'Usuarios con este Rol'
   
   @admin.register(UserProfile)
   class UserProfileAdmin(admin.ModelAdmin):
       list_display = ('user', 'rol', 'fecha_asignacion_rol', 'permisos_count')
       list_filter = ('rol', 'fecha_asignacion_rol')
       search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
       readonly_fields = ('fecha_asignacion_rol', 'fecha_modificacion_rol', 'permisos_list')
       fieldsets = (
           ('Usuario', {
               'fields': ('user',)
           }),
           ('Rol', {
               'fields': ('rol',),
               'description': 'Al asignar un rol, el usuario heredará automáticamente todos sus permisos'
           }),
           ('Información', {
               'fields': ('fecha_asignacion_rol', 'fecha_modificacion_rol', 'permisos_list'),
               'classes': ('collapse',)
           }),
       )
       
       def permisos_count(self, obj):
           if obj.rol:
               return obj.rol.permisos.count()
           return 0
       permisos_count.short_description = 'Permisos del Rol'
       
       def permisos_list(self, obj):
           if obj.rol:
               permisos = obj.rol.permisos.all()[:10]  # Mostrar primeros 10
               lista = '<ul>'
               for perm in permisos:
                   lista += f'<li>{perm.content_type.app_label}.{perm.codename}</li>'
               if obj.rol.permisos.count() > 10:
                   lista += f'<li><em>... y {obj.rol.permisos.count() - 10} más</em></li>'
               lista += '</ul>'
               return format_html(lista)
           return 'Sin rol asignado'
       permisos_list.short_description = 'Permisos Asignados'
   ```

---

### **FASE 2: Implementación por App (Incremental)**

#### **Orden Sugerido:**

1. **`gen_settings`** (Más simple, pocas vistas)
2. **`dashboards`** (Vistas sin modelo)
3. **`reportes_auditoria`** (Vistas sin modelo)
4. **`rrhh_personal`** (Modelos complejos)
5. **`maquinarias`** (Modelos complejos)
6. **`ope_calendario`** (Modelos complejos)

#### **Proceso por App:**

**Paso 1: Identificar vistas y modelos**
```python
# Ejemplo para maquinarias
VISTAS_CON_MODELO = {
    'lista_equipos': ('maquinarias', 'Equipo', 'view'),
    'crear_equipo': ('maquinarias', 'Equipo', 'add'),
    'editar_equipo': ('maquinarias', 'Equipo', 'change'),
    'eliminar_equipo': ('maquinarias', 'Equipo', 'delete'),
}

VISTAS_SIN_MODELO = {
    'calendario_maquinarias': ('maquinarias', 'calendario_maquinarias', 'view'),
    'documentacion_equipo': ('maquinarias', 'documentacion_equipo', 'view'),
}
```

**Paso 2: Crear PermisoVista para vistas sin modelo**
```python
# Ejecutar comando o crear manualmente
python manage.py crear_permisos --app maquinarias
```

**Paso 3: Aplicar decoradores/mixins**
```python
# Antes
@login_required
def lista_equipos(request):
    ...

# Después
@login_required
@permission_required_custom('maquinarias.view_equipo')
def lista_equipos(request):
    ...

# O con mixin para class-based views
class ListaEquiposView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'maquinarias.view_equipo'
    ...
```

**Paso 4: Crear roles y asignar permisos**
```python
# En admin o con comando
rol_admin = Rol.objects.create(nombre='Administrador')
rol_admin.permisos.add(*Permission.objects.all())

rol_rrhh = Rol.objects.create(nombre='RRHH')
rol_rrhh.permisos.add(
    Permission.objects.filter(codename__startswith='view_personal'),
    Permission.objects.filter(codename__startswith='add_personal'),
    ...
)
```

**Paso 5: Asignar roles a usuarios (AUTOMÁTICO)**

El modelo `UserProfile` ya está definido en los modelos propuestos (ver arriba). Ahora solo necesitas usarlo:

**Ejemplo 1: Crear usuario y asignar rol desde código**
```python
from django.contrib.auth.models import User
from gen_permissions.models import Rol, UserProfile

# Crear usuario
usuario = User.objects.create_user(
    username='juan.perez',
    password='password123',
    email='juan@empresa.com'
)

# El UserProfile se crea automáticamente por el signal
# Ahora solo asignas el rol
perfil = usuario.profile
perfil.rol = Rol.objects.get(nombre='Jefe de RRHH')
perfil.save()  # ✅ Automáticamente asigna TODOS los permisos del rol

# Verificar permisos asignados
print(f"Permisos de {usuario.username}:")
for perm in usuario.user_permissions.all():
    print(f"  - {perm.codename}")
```

**Ejemplo 2: Cambiar rol de usuario existente**
```python
# Cambiar de "Trabajador de RRHH" a "Jefe de RRHH"
usuario = User.objects.get(username='maria.garcia')
perfil = usuario.profile
perfil.rol = Rol.objects.get(nombre='Jefe de RRHH')
perfil.save()  # ✅ Automáticamente actualiza los permisos

# Los permisos antiguos se eliminan y se asignan los nuevos
```

**Ejemplo 3: Desde Django Admin**
1. Ir a "Perfiles de Usuario"
2. Seleccionar o crear perfil del usuario
3. Asignar el rol desde el dropdown
4. Guardar → **Los permisos se asignan automáticamente**

**Ejemplo 4: Quitar rol (sin permisos)**
```python
usuario = User.objects.get(username='pedro.lopez')
perfil = usuario.profile
perfil.rol = None  # Quitar rol
perfil.save()  # ✅ Automáticamente elimina todos los permisos
```

**Ventajas del sistema automático:**
- ✅ **Automático**: Al asignar rol, se asignan permisos automáticamente
- ✅ **Sincronizado**: Si cambias el rol, se actualizan los permisos
- ✅ **Simple**: Solo asignas el rol, el resto es automático
- ✅ **Auditable**: Sabes qué rol tiene cada usuario y cuándo se asignó
- ✅ **Sin errores**: No puedes olvidar asignar permisos manualmente
- ✅ **Consistente**: Todos los usuarios con el mismo rol tienen los mismos permisos

---

### **FASE 3: Mejoras y Optimizaciones**

1. **Template tags** para verificar permisos en templates
   ```django
   {% load permissions_tags %}
   {% if user|has_perm:'maquinarias.add_equipo' %}
       <a href="{% url 'crear_equipo' %}">Crear Equipo</a>
   {% endif %}
   ```

2. **Middleware** para logging de accesos denegados

3. **API de permisos** para frontend (si es necesario)

4. **Dashboard de permisos** en admin

---

## 🎯 PERMISOS GRANULARES POR ACCIÓN (Caso: Desactivar Personal)

### **Problema:**
Necesitas permisos más específicos que los básicos (add, change, delete, view). Por ejemplo:
- **Jefe de RRHH**: Puede ver personal Y desactivar personal
- **Trabajador de RRHH**: Puede ver personal PERO NO puede desactivar personal

### **Solución: Permisos Personalizados en el Modelo**

Django permite definir permisos personalizados directamente en el modelo usando `Meta.permissions`.

#### **1. Definir permisos personalizados en el modelo:**

```python
# rrhh_personal/models.py

class Personal(models.Model):
    # ... campos existentes ...
    
    class Meta:
        db_table = 'Personal'
        permissions = [
            # Permisos estándar (add, change, delete, view) se crean automáticamente
            # Permisos personalizados adicionales:
            ('desactivar_personal', 'Puede desactivar personal'),
            ('activar_personal', 'Puede activar personal'),
            ('exportar_personal', 'Puede exportar datos de personal'),
            ('ver_salarios', 'Puede ver información salarial'),
        ]
```

#### **2. Crear los permisos automáticamente:**

```python
# gen_permissions/management/commands/crear_permisos_personalizados.py

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from rrhh_personal.models import Personal

class Command(BaseCommand):
    help = 'Crea permisos personalizados para modelos'

    def handle(self, *args, **options):
        # Obtener ContentType del modelo Personal
        content_type = ContentType.objects.get_for_model(Personal)
        
        # Crear permisos personalizados si no existen
        permisos_personalizados = [
            ('desactivar_personal', 'Puede desactivar personal'),
            ('activar_personal', 'Puede activar personal'),
            ('exportar_personal', 'Puede exportar datos de personal'),
            ('ver_salarios', 'Puede ver información salarial'),
        ]
        
        for codename, name in permisos_personalizados:
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creado permiso: {perm.codename}'))
            else:
                self.stdout.write(f'  Permiso ya existe: {perm.codename}')
```

#### **3. Aplicar en la vista:**

```python
# rrhh_personal/views.py

from gen_permissions.decorators import permission_required_custom

@login_required
@permission_required_custom('rrhh_personal.view_personal')
def table_personal(request):
    """Vista para listar personal - requiere permiso de ver"""
    # ... código existente ...
    context = {
        'puede_desactivar': request.user.has_perm('rrhh_personal.desactivar_personal'),
        'puede_activar': request.user.has_perm('rrhh_personal.activar_personal'),
    }
    return render(request, 'personal/table_personal.html', context)


@login_required
@require_POST
@permission_required_custom('rrhh_personal.desactivar_personal')
def toggle_personal_activo(request):
    """Toggle estado activo/inactivo - requiere permiso específico"""
    try:
        data = json.loads(request.body)
        personal_id = data.get('personal_id')
        
        personal = get_object_or_404(Personal, personal_id=personal_id)
        
        # Verificar permiso según acción
        if personal.activo:
            # Desactivar requiere permiso específico
            if not request.user.has_perm('rrhh_personal.desactivar_personal'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'No tiene permiso para desactivar personal'
                }, status=403)
        else:
            # Activar requiere permiso específico
            if not request.user.has_perm('rrhh_personal.activar_personal'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'No tiene permiso para activar personal'
                }, status=403)
        
        personal.activo = not personal.activo
        personal._current_user = request.user
        personal.save()
        
        estado_texto = "activado" if personal.activo else "desactivado"
        
        return JsonResponse({
            'status': 'success',
            'message': f'Personal {estado_texto} correctamente',
            'activo': personal.activo
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
```

#### **4. En el template (mostrar/ocultar botones):**

```django
{# rrhh_personal/templates/personal/table_personal.html #}

{% load permissions_tags %}

{# Botón de desactivar solo si tiene permiso #}
{% if user|has_perm:'rrhh_personal.desactivar_personal' %}
    <button onclick="toggleEstado({{ personal.personal_id }})" 
            class="btn btn-warning btn-sm">
        Desactivar
    </button>
{% endif %}

{# Botón de activar solo si tiene permiso #}
{% if user|has_perm:'rrhh_personal.activar_personal' %}
    <button onclick="activarPersonal({{ personal.personal_id }})" 
            class="btn btn-success btn-sm">
        Activar
    </button>
{% endif %}
```

#### **5. En JavaScript (validación adicional):**

```javascript
// rrhh_personal/static/js/personal_table.js

function toggleEstado(checkbox) {
    const personalId = checkbox.dataset.personalId;
    const activo = checkbox.checked;
    
    // Verificar permiso antes de enviar (validación adicional)
    const permiso = activo ? 'rrhh_personal.activar_personal' : 'rrhh_personal.desactivar_personal';
    
    // Nota: La validación real se hace en el backend
    // Esto es solo para UX (mostrar mensaje antes de enviar)
    
    if (!confirm(`¿Está seguro de ${activo ? 'activar' : 'desactivar'} este personal?`)) {
        checkbox.checked = !activo; // Revertir checkbox
        return;
    }
    
    // Enviar petición
    fetch('/users/toggle_personal_activo/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ personal_id: personalId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            mostrarExito(data.message);
        } else if (data.status === 'error' && response.status === 403) {
            mostrarError('No tiene permiso para realizar esta acción');
            checkbox.checked = !activo; // Revertir checkbox
        } else {
            mostrarError(data.message || 'Error al cambiar estado');
            checkbox.checked = !activo; // Revertir checkbox
        }
    });
}
```

#### **6. Asignar permisos a roles:**

```python
# En admin o con comando

# Jefe de RRHH - tiene todos los permisos
rol_jefe_rrhh = Rol.objects.get(nombre='Jefe de RRHH')
rol_jefe_rrhh.permisos.add(
    Permission.objects.get(codename='view_personal', content_type__app_label='rrhh_personal'),
    Permission.objects.get(codename='add_personal', content_type__app_label='rrhh_personal'),
    Permission.objects.get(codename='change_personal', content_type__app_label='rrhh_personal'),
    Permission.objects.get(codename='desactivar_personal', content_type__app_label='rrhh_personal'),
    Permission.objects.get(codename='activar_personal', content_type__app_label='rrhh_personal'),
)

# Trabajador de RRHH - solo puede ver y editar, NO desactivar
rol_trabajador_rrhh = Rol.objects.get(nombre='Trabajador de RRHH')
rol_trabajador_rrhh.permisos.add(
    Permission.objects.get(codename='view_personal', content_type__app_label='rrhh_personal'),
    Permission.objects.get(codename='add_personal', content_type__app_label='rrhh_personal'),
    Permission.objects.get(codename='change_personal', content_type__app_label='rrhh_personal'),
    # NO incluye desactivar_personal ni activar_personal
)
```

### **Ejemplos de Permisos Personalizados Comunes:**

```python
# Para modelo Personal
permissions = [
    ('desactivar_personal', 'Puede desactivar personal'),
    ('activar_personal', 'Puede activar personal'),
    ('ver_salarios', 'Puede ver información salarial'),
    ('exportar_personal', 'Puede exportar datos de personal'),
    ('importar_personal', 'Puede importar datos de personal'),
]

# Para modelo Equipo
permissions = [
    ('desactivar_equipo', 'Puede desactivar equipos'),
    ('activar_equipo', 'Puede activar equipos'),
    ('ver_costo_reparacion', 'Puede ver costos de reparación'),
    ('aprobar_ot', 'Puede aprobar órdenes de trabajo'),
    ('cerrar_ot', 'Puede cerrar órdenes de trabajo'),
]

# Para modelo OrdenTrabajo
permissions = [
    ('crear_ot_emergencia', 'Puede crear OTs de emergencia'),
    ('cancelar_ot', 'Puede cancelar órdenes de trabajo'),
    ('reasignar_ot', 'Puede reasignar órdenes de trabajo'),
]
```

### **Ventajas de este Enfoque:**

1. ✅ **Granularidad**: Control fino sobre cada acción
2. ✅ **Nativo de Django**: Usa el sistema estándar de permisos
3. ✅ **Escalable**: Fácil agregar nuevos permisos
4. ✅ **Documentado**: Los permisos están en el modelo
5. ✅ **Admin-friendly**: Se pueden gestionar desde admin
6. ✅ **Testeable**: Fácil de probar

---

## 📝 CONVENCIÓN DE NOMBRES

### **Permisos de Modelo (Automáticos de Django):**
```
{app_label}.{action}_{modelo}
Ejemplos:
- maquinarias.view_equipo
- maquinarias.add_equipo
- maquinarias.change_equipo
- maquinarias.delete_equipo
```

### **Permisos de Acción Personalizados (En el modelo):**
```
{app_label}.{accion_personalizada}_{modelo}
Ejemplos:
- rrhh_personal.desactivar_personal
- rrhh_personal.activar_personal
- rrhh_personal.exportar_personal
- maquinarias.desactivar_equipo
- maquinarias.aprobar_ot
- maquinarias.cerrar_ot
```

**Reglas:**
- Usar verbos en infinitivo: `desactivar`, `activar`, `exportar`, `aprobar`
- Nombre en minúsculas con guiones bajos
- Ser específico: `desactivar_personal` mejor que `cambiar_estado_personal`

### **Permisos de Vista (Personalizados):**
```
{app_label}.{action}_{vista_nombre}
Ejemplos:
- dashboards.view_dashboard_rrhh
- reportes_auditoria.view_auditoria
- maquinarias.view_calendario_maquinarias
```

---

## 🎨 EJEMPLO COMPLETO: App `maquinarias`

### **1. Modelos existentes:**
- `Equipo` → Permisos: `view_equipo`, `add_equipo`, `change_equipo`, `delete_equipo`
- `OrdenTrabajo` → Permisos: `view_ordentrabajo`, `add_ordentrabajo`, etc.

### **2. Vistas sin modelo:**
```python
# Crear PermisoVista para:
- calendario_maquinarias → 'maquinarias.view_calendario_maquinarias'
- documentacion_equipo → 'maquinarias.view_documentacion_equipo'
```

### **3. Aplicar en views.py:**
```python
from gen_permissions.decorators import permission_required_custom

@login_required
@permission_required_custom('maquinarias.view_equipo')
def lista_equipos(request):
    ...

@login_required
@permission_required_custom('maquinarias.add_equipo')
def crear_equipo(request):
    ...

@login_required
@permission_required_custom('maquinarias.view_calendario_maquinarias')
def calendario_maquinarias(request):
    ...
```

### **4. En templates:**
```django
{% load permissions_tags %}

{% if user|has_perm:'maquinarias.add_equipo' %}
    <a href="{% url 'maquinarias:crear_equipo' %}" class="btn btn-primary">
        Crear Equipo
    </a>
{% endif %}
```

---

## 🎛️ GESTIÓN DE ROLES DESDE EL ADMIN DE DJANGO

### **✅ SÍ, puedes crear roles desde el admin y asignar permisos fácilmente**

Con la configuración del admin propuesta arriba, puedes gestionar todo desde la interfaz de Django Admin.

### **Paso a Paso: Crear un Nuevo Rol**

#### **1. Ir al Admin de Django**
- URL: `http://tu-dominio/admin/`
- Iniciar sesión como superusuario

#### **2. Crear Nuevo Rol**
1. Ir a **"Roles"** en el menú lateral
2. Click en **"Añadir Rol"**
3. Completar:
   - **Nombre**: Ej: "Supervisor de Maquinarias"
   - **Descripción**: Ej: "Puede gestionar equipos y aprobar OTs"
   - **Activo**: ✅ Marcado
4. En **"Permisos"**, usar el widget de selección múltiple:
   - Buscar permisos por app o nombre
   - Seleccionar los permisos deseados:
     - `maquinarias.view_equipo`
     - `maquinarias.add_equipo`
     - `maquinarias.change_equipo`
     - `maquinarias.aprobar_ot`
     - `maquinarias.cerrar_ot`
     - etc.
5. Click en **"Guardar"**

#### **3. Asignar Rol a Usuario**
1. Ir a **"Perfiles de Usuario"** en el menú lateral
2. Buscar el usuario o crear uno nuevo
3. En el campo **"Rol"**, seleccionar el rol creado (ej: "Supervisor de Maquinarias")
4. Click en **"Guardar"**
5. ✅ **Automáticamente** el usuario hereda todos los permisos del rol

### **Ejemplo Visual en Admin:**

```
┌─────────────────────────────────────────┐
│ Añadir Rol                              │
├─────────────────────────────────────────┤
│ Nombre: Supervisor de Maquinarias      │
│ Descripción: Puede gestionar equipos... │
│ Activo: ☑                              │
│                                         │
│ Permisos:                               │
│ ┌──────────────┬──────────────────┐   │
│ │ Disponibles   │ Seleccionados    │   │
│ ├──────────────┼──────────────────┤   │
│ │ view_equipo   │ add_equipo       │   │
│ │ change_equipo │ aprobar_ot       │   │
│ │ delete_equipo │ cerrar_ot        │   │
│ │ ...           │ ...              │   │
│ └──────────────┴──────────────────┘   │
│                                         │
│ [Guardar] [Guardar y continuar]        │
└─────────────────────────────────────────┘
```

### **Ventajas del Admin Configurado:**

1. ✅ **Widget mejorado**: `filter_horizontal` para seleccionar múltiples permisos fácilmente
2. ✅ **Búsqueda**: Puedes buscar permisos por nombre o app
3. ✅ **Vista previa**: Muestra cuántos permisos tiene el rol y cuántos usuarios lo usan
4. ✅ **Automático**: Al asignar rol a usuario, se asignan permisos automáticamente
5. ✅ **Auditable**: Fechas de asignación y modificación de roles

### **Filtrar Permisos en el Admin:**

El widget `filter_horizontal` permite:
- **Buscar**: Escribir para filtrar permisos
- **Seleccionar múltiples**: Click para agregar/quitar permisos
- **Ver seleccionados**: Lista de permisos ya asignados al rol
- **Organizar por app**: Los permisos se agrupan por aplicación

### **Ejemplo: Crear Rol "Auditor"**

```python
# Desde admin:
1. Nombre: "Auditor"
2. Descripción: "Solo lectura, puede ver reportes y auditoría"
3. Permisos seleccionados:
   - rrhh_personal.view_personal
   - maquinarias.view_equipo
   - maquinarias.view_ordentrabajo
   - reportes_auditoria.view_auditoria
   - reportes_auditoria.view_reportabilidad
   - (Solo permisos "view", ningún "add", "change" o "delete")
4. Guardar

# Luego asignar a usuario:
1. Ir a Perfiles de Usuario
2. Seleccionar usuario
3. Rol: "Auditor"
4. Guardar
5. ✅ Usuario ahora tiene solo permisos de lectura
```

### **Actualizar Permisos de un Rol Existente:**

1. Ir a **"Roles"**
2. Seleccionar el rol a modificar
3. Agregar o quitar permisos
4. Guardar
5. ✅ **Automáticamente** todos los usuarios con ese rol tienen los nuevos permisos

### **Ver Permisos de un Usuario:**

1. Ir a **"Perfiles de Usuario"**
2. Seleccionar el usuario
3. En la sección **"Permisos Asignados"** verás la lista de permisos del rol
4. También puedes ir directamente a **"Usuarios"** → Seleccionar usuario → Ver permisos

---

## 🔧 COMANDOS ÚTILES

### **Crear permisos automáticamente:**
```bash
# Para una app específica
python manage.py crear_permisos --app maquinarias

# Para todas las apps
python manage.py crear_permisos --all
```

### **Crear roles predefinidos:**
```bash
python manage.py crear_roles_base
```

---

## 📊 ROLES SUGERIDOS

1. **Administrador**
   - Todos los permisos (incluyendo todos los personalizados)

2. **Jefe de RRHH**
   - Personal: view, add, change, **desactivar_personal**, **activar_personal**
   - Documentación: view, add, change
   - Reportes: view, **exportar_personal**
   - Ver salarios: **ver_salarios**

3. **Trabajador de RRHH**
   - Personal: view, add, change
   - Documentación: view, add, change
   - Reportes: view
   - **NO puede**: desactivar_personal, activar_personal, ver_salarios

4. **Jefe de Operaciones**
   - Calendario: view, add, change
   - Faenas: view, add, change, **cerrar_faena**
   - Asignaciones: view, add, change

5. **Operador**
   - Calendario: view
   - Faenas: view
   - Asignaciones: view
   - **NO puede**: crear, modificar, cerrar

6. **Jefe de Maquinarias**
   - Equipos: view, add, change, **desactivar_equipo**, **activar_equipo**
   - OTs: view, add, change, **aprobar_ot**, **cerrar_ot**
   - Calendario: view
   - Ver costos: **ver_costo_reparacion**

7. **Técnico de Maquinarias**
   - Equipos: view
   - OTs: view, change (solo sus asignadas)
   - Calendario: view
   - **NO puede**: crear OTs, aprobar, cerrar, desactivar equipos

8. **Solo Lectura**
   - Todos los permisos view
   - **NO puede**: ninguna acción de modificación

---

## ✅ VENTAJAS DE ESTA PROPUESTA

1. **Escalable**: Fácil agregar nuevos permisos
2. **Mantenible**: Código organizado y documentado
3. **Incremental**: Se puede implementar app por app
4. **Nativo**: Usa Django sin dependencias externas
5. **Flexible**: Soporta vistas con y sin modelo
6. **Testeable**: Fácil de probar
7. **Admin-friendly**: Se puede gestionar desde admin

---

## 🚨 CONSIDERACIONES IMPORTANTES

1. **Migración gradual**: No romper funcionalidad existente
2. **Backward compatibility**: Mantener `@login_required` mientras se migra
3. **Testing**: Probar cada app después de implementar
4. **Documentación**: Documentar cada permiso creado
5. **Rollback plan**: Tener plan B si algo falla

---

## 📅 CRONOGRAMA SUGERIDO

- **Semana 1**: Setup base (gen_permissions)
- **Semana 2**: gen_settings + dashboards
- **Semana 3**: reportes_auditoria
- **Semana 4**: rrhh_personal
- **Semana 5**: maquinarias
- **Semana 6**: ope_calendario + testing general

---

## 🤔 PREGUNTAS PARA DECIDIR

1. ¿Prefieres usar solo Django Permissions o el sistema híbrido?
2. ¿Necesitas permisos por instancia (ej: usuario X solo puede ver equipos de su empresa)?
3. ¿Quieres gestión de permisos desde admin o prefieres comandos?
4. ¿Hay algún rol especial que necesites considerar?

---

## 📚 RECURSOS ADICIONALES

- [Django Permissions Docs](https://docs.djangoproject.com/en/5.2/topics/auth/default/#permissions)
- [Custom Permissions](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#custom-permissions)
- [PermissionRequiredMixin](https://docs.djangoproject.com/en/5.2/topics/auth/default/#the-permissionrequiredmixin-mixin)

