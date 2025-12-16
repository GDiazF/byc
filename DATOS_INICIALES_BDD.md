# 📋 DATOS INICIALES REQUERIDOS PARA EL SISTEMA BYC

Este documento lista todas las tablas maestras y datos estáticos que deben existir en la base de datos para que el sistema funcione correctamente.

---

## 🔴 **DATOS CRÍTICOS (OBLIGATORIOS)**

### 1. **GEN_SETTINGS - Configuraciones Generales**

#### **Region** (Tabla: `gen_settings_region`)
**Datos mínimos requeridos:** Todas las 16 regiones de Chile
```sql
- Región de Arica y Parinacota
- Región de Tarapacá
- Región de Antofagasta
- Región de Atacama
- Región de Coquimbo
- Región de Valparaíso
- Región Metropolitana de Santiago
- Región del Libertador General Bernardo O'Higgins
- Región del Maule
- Región de Ñuble
- Región del Biobío
- Región de La Araucanía
- Región de Los Ríos
- Región de Los Lagos
- Región de Aysén del General Carlos Ibáñez del Campo
- Región de Magallanes y de la Antártica Chilena
```

#### **Comuna** (Tabla: `gen_settings_comuna`)
**Datos mínimos requeridos:** Al menos las comunas principales de cada región
- Debe tener relación con `Region` (campo `region_id`)
- Ejemplos: Antofagasta, Santiago, Valparaíso, Concepción, etc.

#### **Empresa** (Tabla: `gen_settings_empresa`)
**Datos mínimos requeridos:** Al menos 1 empresa
```sql
Campos requeridos:
- rut (ej: '76543210')
- dv (ej: 'K')
- razonSocial (ej: 'GRÚAS BYC LIMITADA')
- nomFantasia (ej: 'Grúas ByC')
- giro
- direccion
- telefono
- email
- region_id (FK a Region)
- comuna_id (FK a Comuna)
```

---

### 2. **RRHH_PERSONAL - Recursos Humanos**

#### **Sexo** (Tabla: `sexo`)
**Datos mínimos requeridos:**
```sql
- MASCULINO
- FEMENINO
- OTRO
```

#### **EstadoCivil** (Tabla: `estadocivil`)
**Datos mínimos requeridos:**
```sql
- SOLTERO/A
- CASADO/A
- VIUDO/A
- DIVORCIADO/A
- SEPARADO/A
- CONVIVIENTE
```

#### **DeptoEmpresa** (Tabla: `DeptoEmpresa`)
**Datos mínimos requeridos:** Al menos 1 departamento
```sql
Ejemplos:
- MAQUINARIAS
- OPERACIONES
- ADMINISTRACIÓN
- RRHH
```

#### **Cargo** (Tabla: `Cargo`)
**Datos mínimos requeridos:** Al menos 1 cargo por departamento
```sql
Ejemplos para MAQUINARIAS:
- MECÁNICO
- RIGGER
- MAESTRO MECÁNICO
- TÉCNICO EN MANTENCIÓN
- SUPERVISOR DE MAQUINARIAS
- LUBRICADOR
- SOLDADOR
- ELECTRICISTA DE MAQUINARIA
- AYUDANTE DE MECÁNICO

Ejemplos para OPERACIONES:
- OPERADOR GRÚA
- OPERADOR MANLIFT
- OPERADOR CAMIÓN
- OPERADOR RETROEXCAVADORA
- OPERADOR CARGADOR FRONTAL
- OPERADOR EXCAVADORA
- OPERADOR BULLDOZER
- SUPERVISOR DE OPERACIONES
- COORDINADOR DE FAENA
- PREVENCIONISTA DE RIESGOS
- CAPATAZ
```

#### **TipoAusentismo** (Tabla: `TipoAusentismo`)
**Datos mínimos requeridos:**
```sql
- LICENCIA MÉDICA
- VACACIONES
- PERMISO ADMINISTRATIVO
- PERMISO SIN GOCE DE SUELDO
- CAPACITACIÓN
```

#### **TipoExamen** (Tabla: `TipoExamen`)
**Datos mínimos requeridos:**
```sql
- EXAMEN PREOCUPACIONAL
- EXAMEN OCUPACIONAL
- EXAMEN DE EGRESO
- EXAMEN DE ALTURA
- EXAMEN PSICOSENSOTÉCNICO
- EXAMEN DE ALCOHOL Y DROGAS
```

#### **ResultadoExamen** (Tabla: `ResultadoExamen`)
**Datos mínimos requeridos:**
```sql
- APTO
- APTO CON RESTRICCIONES
- NO APTO
- PENDIENTE
```

#### **TipoCertificacion** (Tabla: `TipoCertificacion`)
**Datos mínimos requeridos:**
```sql
- CERTIFICACIÓN DE GRÚA HORQUILLA
- CERTIFICACIÓN DE GRÚA TORRE
- CERTIFICACIÓN DE TRABAJO EN ALTURA
- CERTIFICACIÓN DE ESPACIOS CONFINADOS
- CERTIFICACIÓN DE PRIMEROS AUXILIOS
- CERTIFICACIÓN DE MANEJO DEFENSIVO
- CERTIFICACIÓN DE IZAJE DE CARGAS
- CERTIFICACIÓN OPERADOR DE EQUIPOS MÓVILES
```

#### **TipoLicencia** (Tabla: `TipoLicencia`)
**Datos mínimos requeridos:**
```sql
- CLASE A
- CLASE B
- CLASE C
- CLASE D
- CLASE E
- CLASE F
```

#### **TipoLicenciaMedica** (Tabla: `TipoLicenciaMedica`)
**Datos mínimos requeridos:**
```sql
- ENFERMEDAD COMÚN
- ACCIDENTE LABORAL
- ENFERMEDAD PROFESIONAL
- LICENCIA MATERNAL
- LICENCIA PATERNAL
```

#### **TipoLicenciaInterna** (Tabla: `TipoLicenciaInterna`)
**Datos mínimos requeridos:**
```sql
- LIC-A (Licencia Interna Clase A - Equipos Livianos)
- LIC-B (Licencia Interna Clase B - Equipos Medianos)
- LIC-C (Licencia Interna Clase C - Equipos Pesados)
- LIC-D (Licencia Interna Clase D - Grúas Torre)
- LIC-E (Licencia Interna Clase E - Grúas Móviles)
```

#### **ClaseLicencia** (Tabla: `ClaseLicencia`)
**Datos mínimos requeridos:** Depende de los tipos de licencias que uses
```sql
Ejemplos:
- A1, A2, A3, A4, A5
- B, B1, B2
- C, C1, C2, C3, C4, C5
- D, D1, D2, D3
- E, E1, E2, E3
```

---

### 3. **MAQUINARIAS - Gestión de Equipos**

#### **TipoEquipo** (Tabla: `maquinarias_tipoequipo`)
**Datos mínimos requeridos:** Al menos 1 tipo
```sql
Ejemplos:
- GRÚA TORRE (sigla: GT)
- EXCAVADORA (sigla: EX)
- CAMIÓN (sigla: CM)
- CARGADOR FRONTAL (sigla: CF)
- RETROEXCAVADORA (sigla: RT)
- MANLIFT (sigla: ML)
- BULLDOZER (sigla: BD)
```

#### **MarcaEquipo** (Tabla: `maquinarias_marcaequipo`)
**Datos mínimos requeridos:** Al menos 1 marca
```sql
Ejemplos:
- CATERPILLAR
- KOMATSU
- LIEBHERR
- VOLVO
- JCB
- CASE
- HYUNDAI
```

#### **ModeloEquipo** (Tabla: `maquinarias_modeloequipo`)
**Datos mínimos requeridos:** Al menos 1 modelo
- Debe tener relación con `TipoEquipo` y `MarcaEquipo`
- Ejemplos: CAT 320D, Komatsu PC200, Liebherr LTM 1200

#### **EstadoEquipo** (Tabla: `maquinarias_estadoequipo`)
**Datos mínimos requeridos:**
```sql
- Disponible (color: success, orden: 1)
- Shutdown (color: danger, orden: 2)
- En Reparación (color: warning, orden: 3)
- En Reparación Disponible (color: info, orden: 4)
```

#### **EstadoOT** (Tabla: `maquinarias_estadoot`)
**Datos mínimos requeridos:**
```sql
- Pendiente (color: secondary, orden: 1)
- En Proceso (color: primary, orden: 2)
- Terminada (color: success, orden: 3)
- Cancelada (color: danger, orden: 4)
```

#### **TipoMantenimiento** (Tabla: `maquinarias_tipomantenimiento`)
**Datos mínimos requeridos:**
```sql
- Preventivo (descripción: Mantenimiento preventivo programado)
- Correctivo (descripción: Mantenimiento correctivo por falla)
```

#### **Seccion** (Tabla: `maquinarias_seccion`)
**Datos mínimos requeridos:** Al menos 1 sección
```sql
Ejemplos:
- Motor
- Radiador
- Sistema Hidráulico
- Transmisión
- Sistema Eléctrico
- Sistema de Frenos
- Sistema de Dirección
- Chasis
```

#### **TipoReparacion** (Tabla: `maquinarias_tiporeparacion`)
**Datos mínimos requeridos:** Al menos 1 tipo por sección
- Debe tener relación con `Seccion`
- Ejemplos: Cambio de aceite (Motor), Reemplazo de filtro (Radiador)

#### **EstadoCalendarioEquipo** (Tabla: `maquinarias_estadocalendarioequipo`)
**Datos mínimos requeridos:** Al menos 1 estado predeterminado
```sql
Ejemplos:
- Disponible (es_predeterminado: True, color: #000000, background_color: #FFFFFF)
- En Mantenimiento (color: #FFA500, background_color: #FFF8DC)
- En Reparación (color: #FF0000, background_color: #FFE4E1)
- Fuera de Servicio (color: #800000, background_color: #F5F5F5)
```

#### **TipoDocumentoMaquinaria** (Tabla: `maquinarias_tipodocumento`)
**Datos mínimos requeridos:** Al menos 1 tipo
```sql
Ejemplos:
- Revisión Técnica (requiere_fecha_vencimiento: True)
- Seguro (requiere_fecha_vencimiento: True)
- Permiso de Circulación (requiere_fecha_vencimiento: True)
- Certificado de Inspección (requiere_fecha_vencimiento: True)
- Manual de Operación (requiere_fecha_vencimiento: False)
```

---

### 4. **OPE_CALENDARIO - Calendario de Operaciones**

#### **Estado** (Tabla: `ope_calendario_estado`)
**Datos mínimos requeridos:** Al menos 1 estado predeterminado
```sql
Ejemplos:
- Día (es_predeterminado: True, color: #000000, background_color: #FFFFFF)
- Noche (color: #000000, background_color: #000080)
- Descanso (color: #000000, background_color: #D3D3D3)
- Licencia (color: #FFFFFF, background_color: #FFA500)
- Vacaciones (color: #FFFFFF, background_color: #008000)
```

#### **Faena** (Tabla: `ope_calendario_faena`)
**Datos mínimos requeridos:** Opcional (puede estar vacío)
- Si se usa el módulo de calendario, al menos 1 faena activa

---

### 5. **GEN_PERMISSIONS - Sistema de Permisos**

#### **Rol** (Tabla: `gen_permissions_rol`)
**Datos mínimos requeridos:** Al menos 1 rol para usuarios
```sql
Ejemplos:
- Administrador
- Supervisor
- Usuario
- Operador
```

#### **User (Django Auth)**
**Datos mínimos requeridos:** Al menos 1 usuario superusuario
```sql
- username
- email
- password (hasheado)
- is_superuser: True
- is_staff: True
- is_active: True
```

#### **UserProfile** (Tabla: `gen_permissions_userprofile`)
**Datos mínimos requeridos:** 1 perfil por usuario
- Debe tener relación con `User` (OneToOne)
- Opcionalmente puede tener `rol_id` (FK a Rol)

---

## 🟡 **DATOS OPCIONALES (Recomendados)**

### **UnidadMedida** (Tabla: `gen_settings_unidadmedida`)
```sql
Ejemplos:
- Litros (L)
- Kilogramos (kg)
- Metros (m)
- Unidades (un)
- Horas (hrs)
```

### **Proveedor** (Tabla: `Proveedor`)
- Opcional, pero necesario si se registran exámenes/certificaciones con proveedores

### **TipoClasificacion** (Tabla: `TipoClasificacion`)
```sql
Ejemplos:
- Clínica
- Laboratorio
- Centro de Exámenes
- Centro de Certificación
```

---

## 📝 **COMANDOS PARA POBLAR DATOS**

### Opción 1: Usar la migración de datos iniciales
```bash
python manage.py migrate rrhh_personal 0017
```
Esta migración crea automáticamente:
- Sexos, Estados Civiles
- Todas las Regiones y Comunas de Chile
- 2 Empresas de ejemplo
- Departamentos y Cargos
- Todos los tipos de documentación
- 300 trabajadores ficticios (opcional)

### Opción 2: Usar comando de management
```bash
# Para datos de maquinarias
python manage.py poblar_datos_iniciales_ot
```

### Opción 3: Crear manualmente desde Django Admin
1. Acceder a `/admin/`
2. Crear los datos en cada tabla maestra
3. Asegurarse de seguir el orden de dependencias

---

## ⚠️ **ORDEN DE CREACIÓN (IMPORTANTE)**

Debido a las relaciones ForeignKey, los datos deben crearse en este orden:

1. **Region** → **Comuna** (Comuna depende de Region)
2. **Region, Comuna** → **Empresa** (Empresa depende de Region y Comuna)
3. **Sexo, EstadoCivil** (independientes)
4. **DeptoEmpresa** → **Cargo** (Cargo depende de DeptoEmpresa)
5. **Empresa, DeptoEmpresa, Cargo** → **Personal** → **InfoLaboral**
6. **TipoEquipo, MarcaEquipo** → **ModeloEquipo**
7. **Seccion** → **TipoReparacion**
8. **ModeloEquipo, Seccion, TipoReparacion** → **PautaMantenimientoPreventivo**

---

## ✅ **CHECKLIST DE VERIFICACIÓN**

Antes de usar el sistema, verificar que existan:

- [ ] Al menos 1 **Region** y 1 **Comuna**
- [ ] Al menos 1 **Empresa**
- [ ] Al menos 1 **Sexo** (MASCULINO, FEMENINO, OTRO)
- [ ] Al menos 1 **EstadoCivil**
- [ ] Al menos 1 **DeptoEmpresa**
- [ ] Al menos 1 **Cargo** por departamento
- [ ] Al menos 1 **TipoEquipo**, 1 **MarcaEquipo**, 1 **ModeloEquipo**
- [ ] Al menos 1 **EstadoEquipo** y 1 **EstadoOT**
- [ ] Al menos 1 **EstadoCalendarioEquipo** con `es_predeterminado=True`
- [ ] Al menos 1 **Estado** (ope_calendario) con `es_predeterminado=True`
- [ ] Al menos 1 usuario **superusuario** en Django Auth
- [ ] Todos los tipos de documentación (TipoExamen, TipoCertificacion, TipoLicencia, etc.)

---

## 🔧 **NOTAS IMPORTANTES**

1. **Estados Predeterminados**: Debe haber exactamente 1 estado predeterminado activo en:
   - `EstadoCalendarioEquipo` (para calendario de maquinarias)
   - `Estado` (para calendario de operaciones)

2. **Relaciones Obligatorias**: 
   - `Personal` requiere `Sexo`, `EstadoCivil`, `Region`, `Comuna`
   - `InfoLaboral` requiere `Personal`, `Empresa`, `DeptoEmpresa`, `Cargo`
   - `Equipo` requiere `ModeloEquipo`, `Empresa`

3. **Datos de Prueba**: La migración `0017_datos_iniciales_completos.py` crea 300 trabajadores ficticios. Si no los necesitas, puedes eliminarlos después.

4. **Permisos**: El sistema usa Django permissions. Asegúrate de tener al menos un usuario con permisos de administrador.

---

## 📚 **REFERENCIAS**

- Migración de datos iniciales: `rrhh_personal/migrations/0017_datos_iniciales_completos.py`
- Comando de datos maquinarias: `maquinarias/management/commands/poblar_datos_iniciales_ot.py`

