# 🔇 Desactivar Notificaciones Temporalmente (Para Pruebas de Rendimiento)

## 🎯 Objetivo

Desactivar completamente el sistema de notificaciones para:
- Eliminar llamadas AJAX a `/notificaciones/api/contar/`
- Desactivar conexiones SSE (Server-Sent Events)
- Identificar si las notificaciones son la causa de la lentitud

---

## ✅ Cambios realizados en `main_home/templates/home/index.html`

### 1️⃣ **Comentado el ícono de notificaciones** (líneas 42-62)

```html
<!-- ⚠️ NOTIFICACIONES DESACTIVADAS TEMPORALMENTE -->
<!-- 
<li class="nav-item dropdown">
    <a class="nav-link position-relative notifications-link" ...>
        <i class="bi bi-bell text-white notifications-icon"></i>
        ...
    </a>
</li>
-->
```

**Resultado:** El ícono de campanita NO aparece en la barra superior.

---

### 2️⃣ **Comentados los scripts de notificaciones** (líneas 345 y 351)

```html
<!-- ⚠️ NOTIFICACIONES DESACTIVADAS TEMPORALMENTE PARA PRUEBAS DE RENDIMIENTO -->
<!-- <script src="{% static 'js/notificaciones.js' %}"></script> -->

<!-- ⚠️ NOTIFICACIONES DESACTIVADAS TEMPORALMENTE PARA PRUEBAS DE RENDIMIENTO -->
<!-- <script src="{% static 'notificaciones/js/notificaciones.js' %}"></script> -->
```

**Resultado:** 
- ✅ NO se ejecutan llamadas AJAX a `/notificaciones/api/contar/`
- ✅ NO se establece conexión SSE
- ✅ NO hay polling de notificaciones
- ✅ Se eliminan ~300-600ms de carga por página

---

## 🚀 Deployment

```bash
# En tu máquina local:
git add main_home/templates/home/index.html
git commit -m "temp: desactivar notificaciones para pruebas de rendimiento"
git push origin main

# En la EC2:
cd /home/ec2-user/proyecto/byc
git pull origin main
sudo systemctl restart gunicorn.service
```

---

## 🧪 Probar rendimiento

### ANTES (con notificaciones):
```
Personal → Crear → Volver → Inicio
Tiempo total: 10-15 segundos
Network tab:
  - /notificaciones/api/contar/ × 2-3: 300-600ms
  - /notificaciones/api/sse/: Conexión persistente
```

### DESPUÉS (sin notificaciones):
```
Personal → Crear → Volver → Inicio
Tiempo esperado: 2-5 segundos (60-70% más rápido)
Network tab:
  - Sin llamadas a /notificaciones/
```

---

## 📊 Interpretar resultados

### **Si la app ahora es RÁPIDA:**
✅ **Las notificaciones eran el problema**

**Soluciones permanentes:**
1. Aumentar intervalo de polling (de 30s a 60s o más)
2. Desactivar SSE y usar solo polling
3. Cachear más agresivamente
4. Lazy loading de notificaciones (solo al abrir dropdown)

### **Si la app SIGUE LENTA:**
❌ **El problema está en otro lado**

**Revisar:**
1. Queries de la vista de Personal (N+1 queries)
2. Permisos del usuario (`handle_permissions.js`)
3. Archivos estáticos lentos
4. Otros JavaScript ejecutándose

---

## 🔄 Reactivar notificaciones después

Cuando termines las pruebas y quieras reactivar las notificaciones:

1. **Descomentar el ícono** (líneas 42-62)
2. **Descomentar los scripts** (líneas 345 y 351)
3. Commit, push, pull, reiniciar

```bash
# Deshacer los comentarios en main_home/templates/home/index.html
git add main_home/templates/home/index.html
git commit -m "feat: reactivar sistema de notificaciones"
git push origin main

# En EC2:
cd /home/ec2-user/proyecto/byc
git pull origin main
sudo systemctl restart gunicorn.service
```

---

## 📝 Próximos pasos

1. **Hacer deployment** de estos cambios
2. **Probar navegación** con Network tab abierto
3. **Reportar resultados:**
   - ¿La navegación es más rápida?
   - ¿Cuántos segundos tarda ahora?
   - ¿Qué aparece en Network tab ahora?

---

## 💡 Nota importante

Este cambio es **temporal** y solo para diagnóstico. No dejes la aplicación en producción sin notificaciones a largo plazo.

Si las notificaciones son el problema, implementaremos optimizaciones para que funcionen sin causar lentitud.

