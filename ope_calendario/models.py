# ============================================================================
# MODELOS DE CALENDARIO DE OPERACIONES
# ============================================================================
# Este módulo define los modelos para el sistema de calendario de operaciones,
# incluyendo estados dinámicos, turnos, faenas, asignaciones y estados manuales.

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, CheckConstraint, F
from datetime import datetime, timedelta
from rrhh_personal.models import Personal, DeptoEmpresa, Cargo, InfoLaboral, Ausentismo, TipoAusentismo, LicenciaPorPersonal, Certificacion, Examen, Comuna, Region, EstadoCivil, Sexo, TipoLicenciaMedica, LicenciaMedicaPorPersonal
from gen_settings.models import Empresa

# ============================================================================
# 1. ESTADOS DINÁMICOS
# ============================================================================
# Los estados dinámicos permiten configurar diferentes estados que puede tener
# el personal (Día, Noche, Descanso, Licencia, etc.) sin necesidad de modificar código.
class Estado(models.Model):
    """
    Estado configurable desde admin. Ejemplos: 'Día', 'Noche', 'Descanso',
    'Licencia', 'Permiso', 'Vacaciones', 'Disponible', etc.
    """
    nombre = models.CharField(max_length=100, unique=True)
    nombre_corto = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        help_text="Nombre corto para mostrar en el calendario (ej: 'D' para 'Día', 'N' para 'Noche')"
    )
    color = models.CharField(
        max_length=7,
        help_text="Color HEX para el texto del estado (ej: #0EA5E9)"
    )
    background_color = models.CharField(
        max_length=7,
        help_text="Color HEX para el fondo del estado (ej: #0EA5E9)"
    )
    prioridad = models.PositiveIntegerField(
        default=10,
        help_text="Mayor número => mayor prioridad si hay conflicto"
    )
    es_bloqueante = models.BooleanField(
        default=False,
        help_text="Si es True, este estado siempre sobreescribe cualquier otro que coincida"
    )
    es_predeterminado = models.BooleanField(
        default=False,
        help_text="Si es True, este será el estado por defecto cuando no haya asignaciones"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-activo", "-prioridad", "nombre"]
        verbose_name = "Estado"
        verbose_name_plural = "Estados"
        constraints = [
            CheckConstraint(
                check=Q(es_predeterminado=False) | Q(es_predeterminado=True),
                name='solo_un_estado_predeterminado'
            )
        ]

    def clean(self):
        """
        Validar que solo haya un estado predeterminado activo.
        Este método se ejecuta automáticamente antes de guardar el modelo.
        """
        if self.es_predeterminado:
            # Paso 1: Verificar si ya existe otro estado predeterminado activo
            # Excluir el estado actual (self.pk) para permitir actualizaciones
            otros_predeterminados = Estado.objects.filter(
                es_predeterminado=True,
                activo=True
            ).exclude(pk=self.pk)
            
            # Paso 2: Si existe otro estado predeterminado, lanzar error de validación
            if otros_predeterminados.exists():
                raise ValidationError(
                    'Ya existe otro estado marcado como predeterminado. '
                    'Solo puede haber un estado predeterminado a la vez.'
                )

    def save(self, *args, **kwargs):
        """
        Asegurar que solo haya un estado predeterminado al guardar.
        Si este estado se marca como predeterminado, desmarca todos los demás.
        """
        if self.es_predeterminado:
            # Paso 1: Desmarcar otros estados predeterminados
            # Esto asegura que solo este estado sea el predeterminado
            Estado.objects.filter(
                es_predeterminado=True
            ).exclude(pk=self.pk).update(es_predeterminado=False)
        
        # Paso 2: Ejecutar validaciones del modelo
        self.clean()
        
        # Paso 3: Guardar el modelo llamando al método save de la clase padre
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class EstadoFuente(models.Model):
    """
    Mapea un Estado a una FUENTE EXTERNA de datos (cualquier modelo),
    para poder consultar si la persona está en ese estado por rangos de fechas,
    SIN tocar código.

    Ejemplos:
    - Estado 'Permiso' -> content_type = Ausentismo, campo_inicio='desde', campo_fin='hasta', campo_personal='personal'
    - Estado 'Licencia' -> content_type = LicenciaMedica, campo_inicio='inicio', campo_fin='fin'
    """
    estado = models.OneToOneField(Estado, on_delete=models.CASCADE, related_name="fuente")
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        help_text="Modelo origen (ej: Ausentismo, LicenciaMedica, etc.)"
    )
    campo_fecha_inicio = models.CharField(max_length=50, default="fecha_inicio")
    campo_fecha_fin = models.CharField(max_length=50, default="fecha_fin")
    campo_personal = models.CharField(max_length=50, default="personal")
    # Filtro extra opcional como JSON simple (texto) para casos especiales (ej: tipo='Permiso')
    filtro_extra = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Fuente de Estado"
        verbose_name_plural = "Fuentes de Estados"

    def __str__(self):
        return f"Fuente({self.estado.nombre}) → {self.content_type.app_label}.{self.content_type.model}"

#2 TURNOS Y CICLOS
class Turno(models.Model):
    """
    Turno configurable, p. ej. '7x7', '7x7x7x7', '5x2', '15x15', o personalizados.
    NO define la secuencia en sí; la secuencia vive en TurnoBloque.
    """
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"

    def __str__(self):
        return self.nombre

    @property
    def longitud_ciclo(self) -> int:
        """
        Calcula la longitud total del ciclo del turno en días.
        Suma la duración de todos los bloques que componen el turno.
        
        Ejemplo: Para un turno '7x7x7x7' con bloques de 7, 7, 7, 7 días,
        retorna 28 días.
        
        Retorna:
            int: Suma total de días del ciclo
        """
        return sum(self.bloques.values_list("duracion_dias", flat=True))

class TurnoBloque(models.Model):
    """
    Cada bloque del turno con su duración y el Estado que representa.
    Ejemplo para '7x7x7x7':
      - orden=1, duracion_dias=7, estado='Día'
      - orden=2, duracion_dias=7, estado='Descanso'
      - orden=3, duracion_dias=7, estado='Noche'
      - orden=4, duracion_dias=7, estado='Descanso'
    """
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name="bloques")
    orden = models.PositiveIntegerField(help_text="Posición del bloque dentro del ciclo (1..n)")
    duracion_dias = models.PositiveIntegerField()
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, related_name="bloques_turno")

    class Meta:
        ordering = ["turno", "orden"]
        unique_together = [("turno", "orden")]
        verbose_name = "Bloque de Turno"
        verbose_name_plural = "Bloques de Turno"

    def __str__(self):
        return f"{self.turno.nombre} · bloque {self.orden} · {self.estado.nombre} ({self.duracion_dias}d)"


#3 FAENAS Y ASIGNACIONES


class Faena(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código/Identificador', help_text='Código único identificador de la faena')
    nombre = models.CharField(max_length=150)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["codigo", "nombre"]
        verbose_name = "Faena"
        verbose_name_plural = "Faenas"
        constraints = [
            CheckConstraint(
                check=Q(fecha_fin__gte=F("fecha_inicio")),
                name="faena_rango_valido",
            )
        ]
        # Permisos personalizados para acciones específicas dentro del modelo Faena
        permissions = [
            ('desactivar_faena', 'Puede desactivar faenas'),
            ('activar_faena', 'Puede activar faenas'),
            ('asignar_personal_faena', 'Puede asignar personal a faenas'),
            ('asignar_equipos_faena', 'Puede asignar equipos a faenas'),
            ('ver_historial_faena', 'Puede ver historial completo de faenas'),
            ('exportar_faenas', 'Puede exportar datos de faenas'),
        ]

    def clean(self):
        """
        Validar que la fecha de fin sea posterior a la fecha de inicio.
        Este método se ejecuta automáticamente antes de guardar el modelo.
        """
        super().clean()
        # Validar que si ambas fechas están definidas, la fecha de fin sea posterior a la de inicio
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({
                'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })

    def save(self, *args, **kwargs):
        """
        Validar el modelo antes de guardar.
        Ejecuta todas las validaciones (clean, full_clean) antes de persistir en la base de datos.
        """
        self.full_clean()  # Ejecutar todas las validaciones del modelo
        super().save(*args, **kwargs)  # Guardar en la base de datos

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def duracion_dias(self):
        """
        Calcula la duración en días de la faena.
        Incluye tanto el día de inicio como el día de fin en el cálculo.
        
        Retorna:
            int: Cantidad de días de duración de la faena, o None si faltan fechas
        """
        if self.fecha_inicio and self.fecha_fin:
            # Sumar 1 para incluir tanto el día de inicio como el de fin
            return (self.fecha_fin - self.fecha_inicio).days + 1
        return None



class AsignacionFaena(models.Model):
    """
    Asigna una persona a una faena + turno, con fecha de inicio y (opcional) fin.
    El 'bloque_inicio' permite definir con qué parte del ciclo comienza (día, noche, descanso, etc.).
    """
    personal = models.ForeignKey("rrhh_personal.Personal", on_delete=models.CASCADE, related_name="asignaciones_faena", db_index=True)
    faena = models.ForeignKey(Faena, on_delete=models.CASCADE, related_name="asignaciones", db_index=True)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name="asignaciones", db_index=True)

    fecha_inicio = models.DateField(db_index=True)
    fecha_fin = models.DateField(blank=True, null=True, db_index=True)

    bloque_inicio = models.ForeignKey(
        TurnoBloque,
        on_delete=models.CASCADE,
        related_name="asignaciones_inicio",
        help_text="Bloque del turno desde el cual arranca el ciclo para esta persona"
    )

    observaciones = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["personal", "fecha_inicio"]
        verbose_name = "Asignación a Faena"
        verbose_name_plural = "Asignaciones a Faenas"
        indexes = [
            models.Index(fields=["personal", "fecha_inicio", "fecha_fin"]),
            models.Index(fields=["faena", "turno"]),
        ]
        constraints = [
            CheckConstraint(
                check=Q(fecha_fin__gte=F("fecha_inicio")) | Q(fecha_fin__isnull=True),
                name="asig_faena_rango_valido",
            )
        ]
        # Permisos personalizados para acciones específicas dentro del modelo AsignacionFaena
        permissions = [
            ('asignacion_masiva_personal', 'Puede realizar asignaciones masivas de personal'),
            ('modificar_asignacion_personal', 'Puede modificar asignaciones de personal existentes'),
        ]

    def __str__(self):
        ffin = self.fecha_fin or "∼"
        return f"{self.personal} → {self.faena} [{self.turno}] {self.fecha_inicio} → {ffin}"

    def clean(self):
        """
        Validar que el bloque de inicio pertenezca al turno asignado.
        Este método se ejecuta automáticamente antes de guardar el modelo.
        """
        # Validación: el bloque_inicio debe pertenecer al turno asignado
        # Esto asegura la integridad de los datos: no se puede iniciar un turno
        # con un bloque que pertenece a otro turno diferente
        if self.bloque_inicio and self.bloque_inicio.turno_id != self.turno_id:
            raise ValidationError({"bloque_inicio": _("El bloque de inicio no pertenece al turno asignado.")})

    def obtener_estado_en_fecha(self, fecha):
        """
        Calcula el estado de la persona en una fecha específica basado en el turno asignado.
        Considera el ciclo del turno, el bloque de inicio y la fecha de la asignación.
        
        Parámetros:
            fecha: datetime.date - Fecha para la cual se quiere calcular el estado
        
        Retorna:
            Estado: El estado correspondiente a la fecha, o None si la fecha está fuera del rango
        """
        # Paso 1: Validar que la asignación esté activa y la fecha esté dentro del rango
        if not self.activo or fecha < self.fecha_inicio:
            return None  # Asignación inactiva o fecha antes del inicio
        
        if self.fecha_fin and fecha > self.fecha_fin:
            return None  # Fecha después del fin de la asignación
        
        # Paso 2: Calcular días transcurridos desde el inicio de la asignación
        dias_transcurridos = (fecha - self.fecha_inicio).days
        
        # Paso 3: Obtener la longitud del ciclo del turno
        longitud_ciclo = self.turno.longitud_ciclo
        if longitud_ciclo == 0:
            return None  # Turno sin bloques definidos
        
        # Paso 4: Calcular posición en el ciclo usando módulo
        # Esto permite que el ciclo se repita indefinidamente
        posicion_ciclo = dias_transcurridos % longitud_ciclo
        
        # Paso 5: Obtener todos los bloques del turno ordenados por orden
        bloques = self.turno.bloques.all().order_by('orden')
        
        # Paso 6: Calcular offset basado en el bloque de inicio
        # El bloque_inicio permite que diferentes personas empiecen en diferentes
        # partes del ciclo (ej: una empieza en Día, otra en Noche)
        offset_inicio = 0
        if self.bloque_inicio:
            # Sumar la duración de todos los bloques anteriores al bloque de inicio
            for bloque in bloques:
                if bloque.orden < self.bloque_inicio.orden:
                    offset_inicio += bloque.duracion_dias
                else:
                    break
        
        # Paso 7: Ajustar la posición del ciclo con el offset de inicio
        # Esto desplaza el ciclo para que comience desde el bloque_inicio
        posicion_ajustada = (posicion_ciclo + offset_inicio) % longitud_ciclo
        
        # Paso 8: Encontrar el bloque que corresponde a la posición ajustada
        # Recorrer los bloques acumulando días hasta encontrar el bloque correcto
        dias_acumulados = 0
        for bloque in bloques:
            if posicion_ajustada < dias_acumulados + bloque.duracion_dias:
                return bloque.estado  # Retornar el estado del bloque encontrado
            dias_acumulados += bloque.duracion_dias
        
        return None  # No se encontró bloque (no debería ocurrir)


class AsignacionEquipoFaena(models.Model):
    """
    Asigna un equipo a una faena con fecha de inicio y (opcional) fin.
    """
    equipo = models.ForeignKey("maquinarias.Equipo", on_delete=models.CASCADE, related_name="asignaciones_faena", db_index=True)
    faena = models.ForeignKey(Faena, on_delete=models.CASCADE, related_name="asignaciones_equipos", db_index=True)
    
    fecha_inicio = models.DateField(db_index=True)
    fecha_fin = models.DateField(blank=True, null=True, db_index=True)
    
    observaciones = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["equipo", "fecha_inicio"]
        verbose_name = "Asignación de Equipo a Faena"
        verbose_name_plural = "Asignaciones de Equipos a Faenas"
        indexes = [
            models.Index(fields=["equipo", "fecha_inicio", "fecha_fin"]),
            models.Index(fields=["faena", "fecha_inicio"]),
        ]
        constraints = [
            CheckConstraint(
                check=Q(fecha_fin__gte=F("fecha_inicio")) | Q(fecha_fin__isnull=True),
                name="asig_equipo_faena_rango_valido",
            )
        ]
        # Permisos personalizados para acciones específicas dentro del modelo AsignacionEquipoFaena
        permissions = [
            ('modificar_asignacion_equipo', 'Puede modificar asignaciones de equipos existentes'),
        ]
    
    def __str__(self):
        ffin = self.fecha_fin or "∼"
        return f"{self.equipo} → {self.faena} {self.fecha_inicio} → {ffin}"


class HistorialFaena(models.Model):
    """
    Registra todos los cambios y acciones realizadas en una faena.
    Permite auditoría completa de asignaciones, modificaciones y eliminaciones.
    """
    ACCION_CHOICES = [
        ('FAENA_CREADA', 'Faena Creada'),
        ('FAENA_MODIFICADA', 'Faena Modificada'),
        ('PERSONAL_ASIGNADO', 'Personal Asignado'),
        ('PERSONAL_ELIMINADO', 'Personal Eliminado'),
        ('ASIGNACION_MODIFICADA', 'Asignación Modificada'),
        ('TURNO_MODIFICADO', 'Turno Modificado'),
        ('FECHA_MODIFICADA', 'Fecha Modificada'),
        ('EQUIPO_ASIGNADO', 'Equipo Asignado'),
        ('EQUIPO_ELIMINADO', 'Equipo Eliminado'),
        ('EQUIPO_MODIFICADO', 'Equipo Modificado'),
    ]
    
    faena = models.ForeignKey(
        Faena, 
        on_delete=models.CASCADE, 
        related_name="historial",
        db_index=True
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que realizó la acción"
    )
    accion = models.CharField(
        max_length=50,
        choices=ACCION_CHOICES,
        help_text="Tipo de acción realizada"
    )
    personal = models.ForeignKey(
        "rrhh_personal.Personal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_faenas",
        help_text="Personal involucrado en la acción (si aplica)"
    )
    descripcion = models.TextField(
        help_text="Descripción detallada del cambio"
    )
    datos_previos = models.JSONField(
        null=True,
        blank=True,
        help_text="Estado anterior antes del cambio (JSON)"
    )
    datos_nuevos = models.JSONField(
        null=True,
        blank=True,
        help_text="Estado nuevo después del cambio (JSON)"
    )
    
    class Meta:
        ordering = ["-fecha_hora"]
        verbose_name = "Historial de Faena"
        verbose_name_plural = "Historial de Faenas"
        indexes = [
            models.Index(fields=["faena", "-fecha_hora"]),
            models.Index(fields=["usuario", "-fecha_hora"]),
        ]
    
    def __str__(self):
        return f"{self.faena.codigo} - {self.get_accion_display()} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def registrar(cls, faena, accion, descripcion, usuario=None, personal=None, datos_previos=None, datos_nuevos=None):
        """
        Método helper para registrar fácilmente un evento en el historial de faenas.
        Simplifica la creación de registros de historial con todos los datos necesarios.
        
        Parámetros:
            faena: Faena - La faena relacionada con el evento
            accion: str - Tipo de acción realizada (debe ser una de ACCION_CHOICES)
            descripcion: str - Descripción detallada del cambio o evento
            usuario: User (opcional) - Usuario que realizó la acción
            personal: Personal (opcional) - Personal involucrado en la acción
            datos_previos: dict (opcional) - Estado anterior antes del cambio (JSON)
            datos_nuevos: dict (opcional) - Estado nuevo después del cambio (JSON)
        
        Retorna:
            HistorialFaena: Instancia creada del historial
        """
        return cls.objects.create(
            faena=faena,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            personal=personal,
            datos_previos=datos_previos,
            datos_nuevos=datos_nuevos
        )


#4 ESTADOS MANUALES

class EstadoManual(models.Model):
    """
    Permite fijar un estado manual por rango (sobrescribe según prioridad/bloqueo).
    Útil para casos puntuales sin depender de otras tablas.
    """
    personal = models.ForeignKey("rrhh_personal.Personal", on_delete=models.CASCADE, related_name="estados_manuales", db_index=True)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name="aplicaciones_manuales", db_index=True)
    faena = models.ForeignKey(Faena, on_delete=models.CASCADE, related_name="estados_manuales", db_index=True, blank=True, null=False)
    fecha_inicio = models.DateField(db_index=True, blank=True, null=True)
    fecha_fin = models.DateField(db_index=True, blank=True, null=True)
    motivo = models.CharField(max_length=200, blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["personal", "fecha_inicio"]
        verbose_name = "Estado Manual"
        verbose_name_plural = "Estados Manuales"
        indexes = [
            models.Index(fields=["personal", "fecha_inicio", "fecha_fin"]),
        ]
        constraints = [
            CheckConstraint(
                check=Q(fecha_fin__gte=F("fecha_inicio")),
                name="estado_manual_rango_valido",
            )
        ]
        # Permisos personalizados para acciones específicas dentro del modelo EstadoManual
        permissions = [
            ('asignar_estado_manual', 'Puede asignar estados manuales a personal'),
            ('eliminar_estado_manual', 'Puede eliminar estados manuales'),
        ]

    def __str__(self):
        return f"{self.personal} · {self.estado.nombre} · {self.fecha_inicio} → {self.fecha_fin}"

# ============================================================================
# 5. MÉTODOS UTILITARIOS PARA CALCULAR ESTADO FINAL
# ============================================================================

def obtener_estado_final_personal_fecha(personal, fecha):
    """
    Método utilitario que calcula el estado final de una persona en una fecha específica,
    considerando todas las fuentes de estados y sus prioridades.
    
    Este método consolida estados de diferentes fuentes (manuales, fuentes externas, turnos)
    y aplica reglas de prioridad para determinar el estado final.
    
    Orden de prioridad (de mayor a menor):
    1. Estados manuales (más alta prioridad, pueden ser bloqueantes)
    2. Estados de fuentes externas (según prioridad del estado configurada)
    3. Estados derivados de turnos (más baja prioridad)
    4. Estado predeterminado (si no hay ningún otro estado)
    
    Parámetros:
        personal: Personal - La persona para la cual calcular el estado
        fecha: datetime.date - Fecha para la cual calcular el estado
    
    Retorna:
        list[Estado]: Lista de estados (normalmente uno, pero puede haber múltiples
                      si tienen la misma prioridad máxima y no son bloqueantes)
    """
    from django.db.models import Q
    
    # Paso 1: Buscar estados manuales activos para esta fecha
    # Los estados manuales tienen la mayor prioridad y pueden sobrescribir otros estados
    estados_manuales = EstadoManual.objects.filter(
        personal=personal,
        fecha_inicio__lte=fecha,  # La fecha debe ser >= fecha_inicio
        fecha_fin__gte=fecha,  # La fecha debe ser <= fecha_fin
        activo=True
    ).select_related('estado').order_by('-estado__prioridad')  # Ordenar por prioridad descendente
    
    if estados_manuales.exists():
        # Paso 1.1: Si hay estados bloqueantes, retornar solo el de mayor prioridad
        # Los estados bloqueantes siempre tienen prioridad absoluta
        bloqueantes = [em for em in estados_manuales if em.estado.es_bloqueante]
        if bloqueantes:
            return [bloqueantes[0].estado]  # Retornar el bloqueante de mayor prioridad
        
        # Paso 1.2: Si no hay bloqueantes, retornar el estado manual de mayor prioridad
        return [estados_manuales.first().estado]
    
    # Paso 2: Buscar estados de fuentes externas (Ausentismo, Licencias, etc.)
    # Estos estados se obtienen dinámicamente desde otros modelos configurados en EstadoFuente
    estados_fuente = []
    for estado_fuente in EstadoFuente.objects.select_related('estado', 'content_type').all():
        # Paso 2.1: Verificar que el estado esté activo
        if not estado_fuente.estado.activo:
            continue
        
        # Paso 2.2: Obtener la clase del modelo desde el ContentType
        modelo = estado_fuente.content_type.model_class()
        if not modelo:
            continue  # Si el modelo no existe, continuar con el siguiente
        
        # Paso 2.3: Construir consulta dinámica usando los campos configurados
        # Los campos se configuran en EstadoFuente (campo_personal, campo_fecha_inicio, etc.)
        filtros = Q(**{
            f"{estado_fuente.campo_personal}": personal,  # Filtrar por personal
            f"{estado_fuente.campo_fecha_inicio}__lte": fecha,  # Fecha >= inicio
            f"{estado_fuente.campo_fecha_fin}__gte": fecha,  # Fecha <= fin
        })
        
        # Paso 2.4: Aplicar filtros extra si existen (ej: tipo='Permiso')
        # Estos filtros permiten refinar la búsqueda (ej: solo ausentismos de tipo "Permiso")
        if estado_fuente.filtro_extra:
            for campo, valor in estado_fuente.filtro_extra.items():
                filtros &= Q(**{campo: valor})
        
        # Paso 2.5: Verificar si existe algún registro que cumpla los filtros
        if modelo.objects.filter(filtros).exists():
            estados_fuente.append(estado_fuente.estado)  # Agregar el estado encontrado
    
    # Paso 3: Buscar estado derivado de turno (asignación a faena)
    # El estado del turno se calcula basándose en el ciclo del turno y la fecha
    estado_turno = None
    asignaciones_activas = AsignacionFaena.objects.filter(
        personal=personal,
        fecha_inicio__lte=fecha,  # La asignación debe haber comenzado antes o en la fecha
        activo=True
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha)  # Sin fecha fin o fecha fin >= fecha
    ).select_related('turno').first()  # Obtener la primera asignación activa
    
    if asignaciones_activas:
        # Calcular el estado del turno para esta fecha específica
        estado_turno = asignaciones_activas.obtener_estado_en_fecha(fecha)
    
    # Paso 4: Resolver conflictos de prioridad entre todos los estados encontrados
    # Consolidar todos los estados en una lista con su tipo y prioridad
    todos_estados = []
    
    # Paso 4.1: Agregar estados de fuentes externas a la lista consolidada
    for estado in estados_fuente:
        todos_estados.append({
            'estado': estado,
            'tipo': 'fuente',  # Tipo de fuente del estado
            'prioridad': estado.prioridad  # Prioridad del estado
        })
    
    # Paso 4.2: Agregar estado de turno si existe
    if estado_turno:
        todos_estados.append({
            'estado': estado_turno,
            'tipo': 'turno',  # Tipo de fuente del estado
            'prioridad': estado_turno.prioridad  # Prioridad del estado
        })
    
    # Paso 4.3: Si no hay ningún estado, retornar el estado predeterminado
    if not todos_estados:
        try:
            estado_predeterminado = Estado.objects.filter(
                activo=True,
                es_predeterminado=True
            ).first()
            
            if estado_predeterminado:
                return [estado_predeterminado]  # Retornar estado predeterminado
            
            return []  # No hay estados disponibles
        except:
            return []  # Error al obtener estado predeterminado
    
    # Paso 4.4: Ordenar todos los estados por prioridad (mayor número = mayor prioridad)
    todos_estados.sort(key=lambda x: x['prioridad'], reverse=True)
    
    # Paso 4.5: Si hay estados bloqueantes, solo retornar el de mayor prioridad
    # Los estados bloqueantes tienen prioridad absoluta sobre los demás
    bloqueantes = [x for x in todos_estados if x['estado'].es_bloqueante]
    if bloqueantes:
        return [bloqueantes[0]['estado']]  # Retornar el bloqueante de mayor prioridad
    
    # Paso 4.6: Obtener la prioridad más alta de todos los estados
    prioridad_maxima = todos_estados[0]['prioridad']
    
    # Paso 4.7: Retornar todos los estados que tengan la prioridad más alta
    # Esto permite manejar casos donde múltiples estados tienen la misma prioridad máxima
    estados_misma_prioridad = [
        x['estado'] for x in todos_estados 
        if x['prioridad'] == prioridad_maxima
    ]
    
    return estados_misma_prioridad

def obtener_calendario_mensual(anio, mes, personal_filtro=None):
    """
    Obtiene el calendario completo para un mes específico con todos los estados calculados.
    Genera una estructura de datos que incluye el personal y sus estados para cada día del mes.
    
    Parámetros:
        anio: int - Año del calendario (ej: 2025)
        mes: int - Mes del calendario (1-12)
        personal_filtro: QuerySet (opcional) - QuerySet de Personal para filtrar.
                        Si es None, se obtienen todos los personal activos.
    
    Retorna:
        dict: Diccionario con la siguiente estructura:
            {
                'personal': [lista de objetos Personal],
                'estados': {
                    personal_id: {
                        dia: [lista de estados]  # día es el número del día (1-31)
                    }
                },
                'fechas': [lista de objetos date para cada día del mes]
            }
    """
    from datetime import date
    from calendar import monthrange
    
    # Paso 1: Obtener rango de fechas del mes
    # monthrange retorna (día de la semana del primer día, último día del mes)
    _, ultimo_dia = monthrange(anio, mes)
    fecha_inicio = date(anio, mes, 1)  # Primer día del mes
    fecha_fin = date(anio, mes, ultimo_dia)  # Último día del mes
    
    # Paso 2: Obtener personal activo según el filtro proporcionado
    if personal_filtro is None:
        # Si no hay filtro, obtener todos los personal activos ordenados por nombre
        personal = Personal.objects.filter(activo=True).order_by('nombre')
    else:
        # Si hay filtro, aplicarlo y filtrar solo activos
        personal = personal_filtro.filter(activo=True).order_by('nombre')
    
    # Paso 3: Inicializar estructura de resultados del calendario
    calendario = {
        'personal': list(personal),  # Lista de objetos Personal
        'estados': {},  # Diccionario para almacenar estados por personal y día
        'fechas': [fecha_inicio + timedelta(days=i) for i in range(ultimo_dia)]  # Lista de fechas del mes
    }
    
    # Paso 4: Calcular estado para cada persona en cada día del mes
    for persona in personal:
        calendario['estados'][persona.personal_id] = {}  # Inicializar diccionario para esta persona
        
        # Calcular estado para cada fecha del mes
        for fecha in calendario['fechas']:
            # Obtener estados finales para esta persona en esta fecha
            estados = obtener_estado_final_personal_fecha(persona, fecha)
            # Almacenar estados usando el número del día como clave
            calendario['estados'][persona.personal_id][fecha.day] = estados
    
    return calendario
