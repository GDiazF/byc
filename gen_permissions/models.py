# ============================================================================
# MODELOS PARA EL SISTEMA DE ROLES Y PERMISOS
# ============================================================================
# Este modulo define los modelos necesarios para gestionar roles y permisos:
# - Rol: Agrupa permisos que pueden asignarse a usuarios
# - UserProfile: Extiende el modelo User de Django con relacion a Rol
# - PermisoVista: Permisos para vistas que no tienen modelo asociado
# - PermisoModelo: Catalogo de permisos por modelo (documentacion)
# - PermisoAccion: Permisos personalizados para acciones especificas dentro de un modelo
# ============================================================================

from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver


class Rol(models.Model):
    # Roles del sistema que agrupan permisos.
    # Ejemplos: 'Administrador', 'Jefe de RRHH', 'Trabajador de RRHH', etc.
    # Al asignar un rol a un usuario, este hereda automaticamente todos los permisos del rol.
    nombre = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='Nombre del Rol',
        help_text='Nombre único del rol (ej: Jefe de RRHH)'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripcion',
        help_text='Descripcion del rol y sus responsabilidades'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si el rol esta activo y puede asignarse a usuarios'
    )
    # Relacion Many-to-Many con Permission de Django
    # Esto permite que un rol tenga multiples permisos y un permiso pueda estar en multiples roles
    permisos = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name='Permisos',
        help_text='Permisos que tendrán todos los usuarios con este rol'
    )
    
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def get_permisos_count(self):
        # Retorna la cantidad de permisos asignados al rol
        return self.permisos.count()
    
    def get_usuarios_count(self):
        # Retorna la cantidad de usuarios que tienen este rol
        return self.userprofile_set.count()


class UserProfile(models.Model):
    # Perfil extendido del usuario con relacion a Rol.
    # Este modelo extiende el modelo User de Django agregando:
    # - Relacion con Rol (un usuario tiene un rol)
    # - Fechas de asignacion y modificacion del rol
    # - Asignacion automatica de permisos cuando se asigna un rol
    # Cuando se asigna un rol a un usuario, automaticamente se le asignan
    # todos los permisos de ese rol mediante el metodo asignar_permisos_del_rol().
    # Relacion OneToOne: cada usuario tiene un solo perfil y viceversa
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name='Usuario',
        help_text='Usuario asociado a este perfil'
    )
    # Relacion ForeignKey: un usuario tiene un rol, pero un rol puede tener muchos usuarios
    rol = models.ForeignKey(
        Rol, 
        on_delete=models.SET_NULL,  # Si se elimina el rol, el usuario queda sin rol (no se elimina)
        null=True, 
        blank=True,
        verbose_name='Rol',
        help_text='Rol asignado al usuario. Al asignar un rol, se asignan automáticamente todos sus permisos'
    )
    fecha_asignacion_rol = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Asignacion de Rol',
        help_text='Fecha en que se asigno el rol al usuario'
    )
    fecha_modificacion_rol = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Modificacion de Rol',
        help_text='Fecha de ultima modificacion del rol del usuario'
    )
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        ordering = ['user__username']
    
    def __str__(self):
        rol_nombre = self.rol.nombre if self.rol else 'Sin rol'
        return f"{self.user.username} - {rol_nombre}"
    
    def asignar_permisos_del_rol(self):
        # Asigna automaticamente los permisos del rol al usuario.
        # Este metodo se llama automaticamente cuando se guarda el UserProfile.
        # Si el usuario tiene un rol, se le asignan todos los permisos de ese rol.
        # Si no tiene rol, se eliminan todos sus permisos.
        # IMPORTANTE: Despues de asignar permisos, se refresca el objeto User desde la BD
        # y se limpia la cache de permisos para que los cambios se reflejen inmediatamente.
        if self.rol:
            # Obtener todos los permisos del rol
            permisos_del_rol = list(self.rol.permisos.all())
            # Asignar todos los permisos del rol al usuario
            self.user.user_permissions.set(permisos_del_rol)
        else:
            # Si no tiene rol, eliminar todos los permisos
            self.user.user_permissions.clear()
        
        # Refrescar el objeto User desde la BD para limpiar caché de permisos
        # Esto asegura que los permisos se reflejen inmediatamente
        self.user.refresh_from_db()
        
        # Limpiar caché de permisos de Django
        # Esto fuerza a Django a recargar los permisos desde la BD
        if hasattr(self.user, '_perm_cache'):
            delattr(self.user, '_perm_cache')
        if hasattr(self.user, '_user_perm_cache'):
            delattr(self.user, '_user_perm_cache')
    
    def save(self, *args, **kwargs):
        # Sobrescribe el metodo save para asignar permisos automaticamente.
        # Cada vez que se guarda el UserProfile (incluyendo cuando se cambia el rol),
        # se actualizan automaticamente los permisos del usuario.
        # IMPORTANTE: Se usa update_fields para evitar loops infinitos con signals.
        # Guardar primero el objeto
        super().save(*args, **kwargs)
        
        # Asignar permisos automáticamente al guardar
        # Usar una transacción para asegurar que se ejecute después del save
        from django.db import transaction
        transaction.on_commit(lambda: self.asignar_permisos_del_rol())


class PermisoVista(models.Model):
    # Permisos para vistas que NO tienen modelo asociado.
    # Algunas vistas no estan asociadas a un modelo especifico (ej: dashboards, reportes).
    # Este modelo permite crear permisos para esas vistas y asociarlos a un Permission de Django.
    # Ejemplo: 'dashboards.view_dashboard_rrhh' para la vista del dashboard de RRHH
    codigo = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='Codigo del Permiso',
        help_text='Codigo unico del permiso (ej: dashboards.view_dashboard_rrhh)'
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre',
        help_text='Nombre descriptivo del permiso'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripcion',
        help_text='Descripcion detallada del permiso'
    )
    app_label = models.CharField(
        max_length=100,
        verbose_name='App',
        help_text='Nombre de la app donde esta la vista (ej: dashboards)'
    )
    vista_nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Vista',
        help_text='Nombre de la función/vista (ej: dashboard_rrhh)'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si el permiso esta activo'
    )
    # Relacion OneToOne con Permission de Django
    # Cada PermisoVista tiene un Permission asociado que se crea automaticamente
    permission = models.OneToOneField(
        Permission,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permiso_vista',
        verbose_name='Permission de Django',
        help_text='Permission de Django asociado (se crea automaticamente)'
    )
    
    class Meta:
        verbose_name = "Permiso de Vista"
        verbose_name_plural = "Permisos de Vista"
        ordering = ['app_label', 'vista_nombre']
    
    def __str__(self):
        return f"{self.app_label}.{self.vista_nombre}"


class PermisoModelo(models.Model):
    # Catalogo de permisos por modelo (para referencia y documentacion).
    # Este modelo sirve como catalogo/documentacion de que permisos estan disponibles
    # para cada modelo del sistema. No es estrictamente necesario para el funcionamiento,
    # pero ayuda a documentar y gestionar los permisos.
    modelo = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        verbose_name='Modelo',
        help_text='Modelo al que pertenecen los permisos'
    )
    app_label = models.CharField(
        max_length=100,
        verbose_name='App',
        help_text='Nombre de la app del modelo'
    )
    modelo_nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del Modelo',
        help_text='Nombre del modelo'
    )
    # JSONField para almacenar información sobre los permisos disponibles
    # Ejemplo: {'add': True, 'change': True, 'delete': True, 'view': True, 'desactivar': True}
    permisos_disponibles = models.JSONField(
        default=dict,
        verbose_name='Permisos Disponibles',
        help_text='Diccionario con los permisos disponibles para este modelo'
    )
    
    class Meta:
        verbose_name = "Permiso de Modelo"
        verbose_name_plural = "Permisos de Modelo"
        unique_together = ['app_label', 'modelo_nombre']
    
    def __str__(self):
        return f"{self.app_label}.{self.modelo_nombre}"


class PermisoAccion(models.Model):
    # Permisos personalizados para acciones especificas dentro de un modelo.
    # Permite crear permisos mas granulares que los basicos (add, change, delete, view).
    # Por ejemplo: 'desactivar_personal', 'activar_personal', 'exportar_personal', etc.
    # Estos permisos se definen en el Meta.permissions del modelo y luego se registran aqui
    # para facilitar su gestion y documentacion.
    codigo = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='Codigo del Permiso',
        help_text='Codigo unico del permiso (ej: rrhh_personal.desactivar_personal)'
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre',
        help_text='Nombre descriptivo del permiso'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripcion',
        help_text='Descripcion detallada del permiso'
    )
    modelo = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        verbose_name='Modelo',
        help_text='Modelo al que pertenece este permiso de acción'
    )
    accion = models.CharField(
        max_length=100,
        verbose_name='Accion',
        help_text='Nombre de la accion (ej: desactivar, activar, exportar)'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si el permiso esta activo'
    )
    # Relación OneToOne con Permission de Django
    permission = models.OneToOneField(
        Permission,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permiso_accion',
        verbose_name='Permission de Django',
        help_text='Permission de Django asociado (se crea automaticamente)'
    )
    
    class Meta:
        verbose_name = "Permiso de Accion"
        verbose_name_plural = "Permisos de Accion"
        ordering = ['modelo', 'accion']
        unique_together = ['modelo', 'accion']
    
    def __str__(self):
        return f"{self.codigo}"


# ============================================================================
# SIGNALS PARA AUTOMATIZACIÓN
# ============================================================================

@receiver(post_save, sender=User)
def crear_user_profile(sender, instance, created, **kwargs):
    # Signal que crea automaticamente un UserProfile cuando se crea un User.
    # Esto asegura que todos los usuarios tengan un perfil asociado,
    # incluso si se crean desde el admin de Django o desde codigo.
    if created:
        # Crear UserProfile solo si no existe (evitar duplicados)
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=UserProfile)
def actualizar_permisos_usuario(sender, instance, **kwargs):
    # Signal que actualiza los permisos del usuario cuando cambia su rol.
    # Cada vez que se guarda un UserProfile (incluyendo cuando se cambia el rol),
    # se actualizan automaticamente los permisos del usuario.
    # El método asignar_permisos_del_rol() ya se llama en el save() del modelo,
    # pero este signal asegura que también funcione si se modifica desde otros lugares
    instance.asignar_permisos_del_rol()


@receiver(m2m_changed, sender=Rol.permisos.through)
def actualizar_permisos_usuarios_del_rol(sender, instance, action, **kwargs):
    # Signal que actualiza los permisos de TODOS los usuarios que tienen este rol
    # cuando se modifican los permisos del rol (agregar, quitar, limpiar).
    # Esto asegura que si cambias los permisos de un rol, todos los usuarios
    # con ese rol se actualicen automaticamente sin necesidad de guardarlos manualmente.
    # IMPORTANTE: Este signal se ejecuta DESPUES de que se guardan los cambios en la relacion ManyToMany,
    # a diferencia de post_save que se ejecuta antes.
    # Solo procesar cuando se agregan, quitan o limpian permisos (no en pre_add, pre_remove, etc.)
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Obtener todos los usuarios que tienen este rol
        usuarios_con_rol = UserProfile.objects.filter(rol=instance)
        
        # Actualizar permisos de cada usuario
        for user_profile in usuarios_con_rol:
            user_profile.asignar_permisos_del_rol()
