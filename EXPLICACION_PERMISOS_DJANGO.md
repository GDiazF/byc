# 📚 EXPLICACIÓN: Permisos Automáticos de Django

## 🎯 ¿Qué son los permisos automáticos?

Django crea **automáticamente 4 permisos básicos** para **CADA modelo** que defines en tu proyecto.

### **Formato de los permisos:**
```
{app_label}.{action}_{modelo}
```

Donde:
- `app_label`: Nombre de la app (ej: `rrhh_personal`)
- `action`: Acción (add, change, delete, view)
- `modelo`: Nombre del modelo en minúsculas (ej: `sexo`, `personal`)

---

## 📋 Ejemplos de Permisos Automáticos

### **Para el modelo `Sexo` (en app `rrhh_personal`):**

Django crea automáticamente estos 4 permisos:

1. **`rrhh_personal.add_sexo`**
   - **Significado**: Puede crear/agregar nuevos registros en la tabla `Sexo`
   - **Ejemplo**: Agregar "Otro" como nuevo sexo

2. **`rrhh_personal.change_sexo`**
   - **Significado**: Puede modificar registros existentes en la tabla `Sexo`
   - **Ejemplo**: Cambiar el nombre de "Masculino" a "M"

3. **`rrhh_personal.delete_sexo`**
   - **Significado**: Puede eliminar registros de la tabla `Sexo`
   - **Ejemplo**: Eliminar un sexo que ya no se usa

4. **`rrhh_personal.view_sexo`**
   - **Significado**: Puede ver/leer registros de la tabla `Sexo`
   - **Ejemplo**: Ver la lista de sexos disponibles en un dropdown

---

## 🔍 ¿Para qué sirven estos permisos?

### **Casos de Uso:**

#### **1. Tablas Maestras (Catálogos)**
Para modelos como `Sexo`, `EstadoCivil`, `Cargo`, `TipoAusentismo`, etc.:

- **Control de acceso**: Solo administradores pueden modificar estas tablas
- **Prevenir cambios accidentales**: Evitar que usuarios modifiquen datos críticos
- **Auditoría**: Saber quién puede modificar datos maestros

**Ejemplo práctico:**
```python
# Solo administradores pueden agregar/modificar/eliminar sexos
# Pero todos pueden verlos (para usar en formularios)

# En una vista para gestionar sexos:
@login_required
@permission_required_custom('rrhh_personal.add_sexo')
def crear_sexo(request):
    # Solo usuarios con permiso pueden crear sexos
    ...
```

#### **2. Modelos Principales**
Para modelos como `Personal`, `Equipo`, `OrdenTrabajo`, etc.:

- **Control granular**: Diferentes roles tienen diferentes permisos
- **Seguridad**: Prevenir acceso no autorizado a datos sensibles

**Ejemplo práctico:**
```python
# Jefe de RRHH puede ver, agregar y modificar personal
# Trabajador de RRHH solo puede ver y agregar, pero NO modificar

# En la vista de lista de personal:
@login_required
@permission_required_custom('rrhh_personal.view_personal')
def lista_personal(request):
    # Todos los usuarios con permiso pueden ver
    ...
```

---

## 📊 Permisos por Modelo en tu Proyecto

### **App `rrhh_personal`:**

Django crea automáticamente permisos para TODOS estos modelos:

| Modelo | Permisos Automáticos | ¿Son Importantes? |
|--------|---------------------|-------------------|
| `Sexo` | add, change, delete, view | ⚠️ Solo si quieres controlar quién modifica catálogos |
| `EstadoCivil` | add, change, delete, view | ⚠️ Solo si quieres controlar quién modifica catálogos |
| `Personal` | add, change, delete, view | ✅ **MUY IMPORTANTES** - Control de acceso principal |
| `Cargo` | add, change, delete, view | ⚠️ Solo si quieres controlar quién modifica catálogos |
| `DeptoEmpresa` | add, change, delete, view | ⚠️ Solo si quieres controlar quién modifica catálogos |
| `InfoLaboral` | add, change, delete, view | ✅ Importantes - Información laboral |
| `Ausentismo` | add, change, delete, view | ✅ Importantes - Control de ausencias |
| `LicenciaPorPersonal` | add, change, delete, view | ✅ Importantes - Licencias de conducir |
| `Certificacion` | add, change, delete, view | ✅ Importantes - Certificaciones |
| `Examen` | add, change, delete, view | ✅ Importantes - Exámenes médicos |
| ... y todos los demás modelos | add, change, delete, view | Depende del modelo |

---

## 🎯 Recomendación: ¿Qué Permisos Usar?

### **✅ Permisos IMPORTANTES (usar en roles):**

1. **Modelos Principales:**
   - `rrhh_personal.view_personal` ✅
   - `rrhh_personal.add_personal` ✅
   - `rrhh_personal.change_personal` ✅
   - `rrhh_personal.delete_personal` ✅
   - `rrhh_personal.desactivar_personal` ✅ (personalizado)
   - `rrhh_personal.activar_personal` ✅ (personalizado)

2. **Modelos Relacionados:**
   - `rrhh_personal.view_infolaboral` ✅
   - `rrhh_personal.add_infolaboral` ✅
   - `rrhh_personal.change_infolaboral` ✅
   - `rrhh_personal.view_ausentismo` ✅
   - `rrhh_personal.add_ausentismo` ✅
   - etc.

### **⚠️ Permisos OPCIONALES (solo si necesitas control):**

1. **Tablas Maestras (Catálogos):**
   - `rrhh_personal.add_sexo` ⚠️ (solo si quieres controlar quién modifica catálogos)
   - `rrhh_personal.change_sexo` ⚠️
   - `rrhh_personal.delete_sexo` ⚠️
   - `rrhh_personal.view_sexo` ⚠️ (generalmente no necesario, todos pueden ver)

   **¿Cuándo usarlos?**
   - Si quieres que solo administradores puedan modificar catálogos
   - Si quieres prevenir cambios accidentales en datos maestros
   - Si NO los necesitas, simplemente ignóralos

---

## 💡 Estrategia Recomendada

### **Opción 1: Solo Permisos de Modelos Principales (Recomendada)**

**Usar solo permisos de modelos importantes:**
- Personal, Equipo, OrdenTrabajo, Faena, etc.
- Ignorar permisos de tablas maestras (Sexo, EstadoCivil, etc.)

**Ventajas:**
- ✅ Más simple de gestionar
- ✅ Menos permisos que asignar
- ✅ Enfocado en lo importante

**Ejemplo de Rol "Jefe de RRHH":**
```
Permisos asignados:
- rrhh_personal.view_personal ✅
- rrhh_personal.add_personal ✅
- rrhh_personal.change_personal ✅
- rrhh_personal.desactivar_personal ✅
- rrhh_personal.activar_personal ✅
- rrhh_personal.view_infolaboral ✅
- rrhh_personal.add_infolaboral ✅
- rrhh_personal.change_infolaboral ✅
- ... (otros modelos importantes)

NO incluir:
- rrhh_personal.add_sexo ❌
- rrhh_personal.change_sexo ❌
- rrhh_personal.delete_sexo ❌
```

### **Opción 2: Control Total (Más Complejo)**

**Usar TODOS los permisos, incluyendo tablas maestras:**

**Ventajas:**
- ✅ Control total sobre quién modifica qué
- ✅ Más seguro

**Desventajas:**
- ❌ Muchos más permisos que gestionar
- ❌ Más complejo de mantener
- ❌ Puede ser excesivo para la mayoría de casos

**Ejemplo de Rol "Administrador":**
```
Permisos asignados:
- TODOS los permisos de TODOS los modelos ✅
- Incluyendo tablas maestras ✅
```

---

## 🔧 ¿Cómo Ocultar Permisos que No Necesitas?

Si quieres ocultar permisos de tablas maestras del admin, puedes crear un comando personalizado o simplemente **no asignarlos a ningún rol**.

**Los permisos existen, pero si no los asignas a ningún rol, no afectan nada.**

---

## 📝 Resumen

### **Pregunta: "can add sexo" se refiere a la tabla Sexo?**

**Respuesta: SÍ, exactamente.**

- `rrhh_personal.add_sexo` = Puede agregar registros en la tabla `Sexo`
- `rrhh_personal.change_sexo` = Puede modificar registros en la tabla `Sexo`
- `rrhh_personal.delete_sexo` = Puede eliminar registros de la tabla `Sexo`
- `rrhh_personal.view_sexo` = Puede ver registros de la tabla `Sexo`

### **¿Debo usar estos permisos?**

**Depende de tus necesidades:**

- ✅ **SÍ**, si quieres controlar quién puede modificar catálogos/tablas maestras
- ❌ **NO**, si solo te interesa controlar acceso a modelos principales (Personal, Equipo, etc.)

### **Recomendación:**

**Empieza solo con permisos de modelos principales** (Personal, Equipo, etc.).
Si más adelante necesitas controlar quién modifica catálogos, puedes agregar esos permisos.

---

## 🎯 Ejemplo Práctico: Crear Rol "Jefe de RRHH"

### **Permisos a Asignar:**

```
✅ Modelos Principales:
- rrhh_personal.view_personal
- rrhh_personal.add_personal
- rrhh_personal.change_personal
- rrhh_personal.desactivar_personal (personalizado)
- rrhh_personal.activar_personal (personalizado)
- rrhh_personal.view_infolaboral
- rrhh_personal.add_infolaboral
- rrhh_personal.change_infolaboral
- rrhh_personal.view_ausentismo
- rrhh_personal.add_ausentismo
- rrhh_personal.change_ausentismo
- ... (otros modelos importantes)

❌ NO incluir (tablas maestras):
- rrhh_personal.add_sexo
- rrhh_personal.change_sexo
- rrhh_personal.delete_sexo
- rrhh_personal.add_estadocivil
- rrhh_personal.change_estadocivil
- etc.
```

**Resultado:**
- El jefe puede gestionar personal completo
- Pero NO puede modificar catálogos (Sexo, EstadoCivil, etc.)
- Solo administradores pueden modificar catálogos

