# Revisión del Sistema de Orden de Trabajo

## ✅ Modelos Creados

### 1. OrdenTrabajo (`maquinarias_ordentrabajo`)
**Campos principales:**
- `folio` - Folio único generado automáticamente (formato: OT-YYYYMMDD-HHMMSS)
- `equipo_id` - Relación con Equipo
- `empresa_id` - Relación con Empresa
- `horometro`, `odometro`, `horometro_superestructura` - Valores copiados del equipo (no editables)
- `fecha_creacion` - Automática
- `fecha_inicio`, `fecha_fin` - Fechas de la OT
- `tipo_mantenimiento` - Preventivo o Correctivo
- `corresponde_pauta` - Boolean (solo si es preventivo)
- `pauta_id` - Relación con PautaMantenimientoPreventivo (opcional)
- `estado_ot` - Pendiente, En Proceso, Terminada, Cancelada
- `estado_equipo` - Shutdown, En Reparación, En Reparación Disponible, Disponible
- `personal_asignado` - ManyToMany con Personal
- `observaciones` - Texto libre

### 2. ItemSeccionOT (`maquinarias_itemseccionot`)
**Campos principales:**
- `ot_id` - Relación con OrdenTrabajo
- `seccion_id` - Relación con Sección
- `tipos_reparacion` - ManyToMany con TipoReparacion
- `estado_seccion` - Pendiente, En Proceso, Terminada, Cancelada

### 3. HistorialObservacionesOT (`maquinarias_historialobservacionesot`)
**Campos principales:**
- `ot_id` - Relación con OrdenTrabajo
- `observacion` - Texto de la observación
- `usuario` - Usuario que agregó la observación
- `fecha` - Fecha automática

## ✅ Vistas Creadas

### Vistas de Template:
1. **`lista_ordenes_trabajo`** - `/maquinarias/ordenes-trabajo/`
   - Lista todas las ordenes de trabajo con filtros

2. **`crear_orden_trabajo`** - `/maquinarias/ordenes-trabajo/crear/`
   - Formulario para crear nueva OT

3. **`editar_orden_trabajo`** - `/maquinarias/ordenes-trabajo/<ot_id>/editar/`
   - Formulario para editar OT existente

### APIs:
1. **`api_listar_ordenes_trabajo`** - GET `/maquinarias/api/ordenes-trabajo/`
   - Lista OTs con filtros y paginación
   - Parámetros: `empresa_id`, `tipo_equipo_id`, `estado_ot`, `estado_equipo`, `tipo_mantenimiento`, `search`, `page`, `per_page`

2. **`api_guardar_orden_trabajo`** - POST `/maquinarias/api/ordenes-trabajo/guardar/`
   - Crea o actualiza una OT
   - Body JSON con todos los datos del formulario

3. **`api_equipos_filtrados`** - GET `/maquinarias/api/equipos-filtrados/`
   - Obtiene equipos filtrados por empresa, tipo, marca, modelo
   - Parámetros: `empresa_id`, `tipo_equipo_id`, `marca_equipo_id`, `modelo_equipo_id`

4. **`api_personal_maquinarias`** - GET `/maquinarias/api/personal-maquinarias/`
   - Obtiene personal activo con su cargo

5. **`api_agregar_observacion_ot`** - POST `/maquinarias/api/ordenes-trabajo/<ot_id>/observacion/`
   - Agrega una observación al historial de la OT

## ✅ Admin Django

Los modelos están registrados en el admin con:
- Listas filtrables y buscables
- Inlines para ItemSeccionOT y HistorialObservacionesOT
- Campos readonly apropiados
- Fieldsets organizados

## 🔍 Cómo Revisar

### 1. Admin de Django
```
http://localhost:8000/admin/
```
- Buscar sección "MAQUINARIAS"
- Ver "Ordenes de Trabajo", "Items Secciones OT", "Historial de Observaciones OT"

### 2. Probar URLs (requiere autenticación)
```
http://localhost:8000/maquinarias/ordenes-trabajo/
http://localhost:8000/maquinarias/ordenes-trabajo/crear/
```

### 3. Probar APIs (desde navegador o Postman)
```
GET http://localhost:8000/maquinarias/api/equipos-filtrados/
GET http://localhost:8000/maquinarias/api/personal-maquinarias/
GET http://localhost:8000/maquinarias/api/ordenes-trabajo/
```

### 4. Verificar Base de Datos
Las tablas creadas son:
- `maquinarias_ordentrabajo`
- `maquinarias_itemseccionot`
- `maquinarias_itemseccionot_tipos_reparacion` (tabla intermedia)
- `maquinarias_ordentrabajo_personal_asignado` (tabla intermedia)
- `maquinarias_historialobservacionesot`

## ⚠️ Pendiente

- Templates HTML (formulario y lista)
- JavaScript para lógica dinámica del formulario
- Estilos CSS si es necesario

## 📝 Notas

- El folio se genera automáticamente al crear la OT
- Los campos horómetro, odómetro y horómetro superestructura se copian automáticamente del equipo seleccionado
- Si es mantenimiento preventivo y corresponde a pauta, se muestra select de pautas
- Si es preventivo sin pauta o correctivo, se muestran secciones y tipos de reparación
- El personal se selecciona con checkbox múltiple mostrando nombre y cargo

