# ⚡ Optimización del Sistema de Notificaciones

## 🔍 Problema detectado

Al analizar el Network tab del navegador, se identificó que:

- Múltiples llamadas AJAX a `/notificaciones/api/contar/` tomaban **150-200ms cada una**
- Estas llamadas se ejecutaban **2-3 veces** en cada carga de página
- **NO estaban cacheadas**, causando queries a PostgreSQL en cada request
- Acumulaban varios segundos de demora en cada navegación

---

## ✅ Solución implementada

### 1️⃣ **Caché del contador de notificaciones** (`notificaciones/views.py`)

```python
# Antes: Query directa a la BD en cada request
count = contar_notificaciones_no_leidas(request.user)

# Ahora: Cache de 30 segundos por usuario
cache_key = f'notif_count_user_{request.user.id}'
count = cache.get(cache_key)

if count is None:
    count = contar_notificaciones_no_leidas(request.user)
    cache.set(cache_key, count, 30)  # 30 segundos
```

**Beneficio:** 
- Primera llamada: ~150ms (query a BD)
- Siguientes llamadas: < 5ms (desde caché)
- **Reducción del 97% en tiempo de respuesta**

---

### 2️⃣ **Invalidación automática del caché** (`notificaciones/signals.py`)

El caché se invalida automáticamente cuando:
- Se crea una nueva notificación
- Se marca como leída
- Se archiva/desarc hiva
- Cualquier modificación a notificaciones

```python
@receiver(post_save, sender=Notificacion)
def enviar_evento_sse_notificacion(sender, instance, created, **kwargs):
    # Invalidar caché del contador
    from django.core.cache import cache
    cache_key = f'notif_count_user_{instance.usuario.id}'
    cache.delete(cache_key)
    # ... resto del código ...
```

**Beneficio:** El usuario siempre ve el contador actualizado sin demora adicional.

---

## 📊 Resultados esperados

### Antes:
```
/notificaciones/api/contar/ → 150-200ms (cada llamada)
× 2-3 llamadas = 300-600ms acumulados
```

### Después:
```
Primera llamada: ~150ms (query a BD + guardar en caché)
Siguientes 30 segundos:
  - Llamada 2: ~5ms (desde caché)
  - Llamada 3: ~5ms (desde caché)
Total: ~160ms vs 300-600ms
```

**Mejora: 60-75% más rápido**

---

## 🚀 Deployment

### PASO 1: Commit y push
```bash
git add notificaciones/views.py notificaciones/signals.py
git commit -m "perf: cachear contador de notificaciones para reducir queries"
git push origin main
```

### PASO 2: Actualizar en EC2
```bash
cd /home/ec2-user/proyecto/byc
git pull origin main
sudo systemctl restart gunicorn.service
```

### PASO 3: Verificar
Abre las herramientas de desarrollo → Network y navega por la app:
- Las llamadas a `/notificaciones/api/contar/` deberían ser **< 10ms** después de la primera

---

## 🔍 Monitoreo

Para verificar que el caché funciona:

```bash
# En la EC2, ver logs de Django
tail -f /home/ec2-user/proyecto/byc/logs/django.log

# O verificar el cache en la BD
python manage.py shell
>>> from django.core.cache import cache
>>> cache.get('notif_count_user_1')  # Reemplazar 1 con tu user ID
```

---

## 💡 Consideraciones

### ¿Por qué 30 segundos de caché?

Balance entre **rendimiento** y **actualización**:
- ✅ Suficientemente corto para que las notificaciones nuevas aparezcan rápido
- ✅ Suficientemente largo para evitar queries repetidas
- ✅ Se invalida automáticamente si hay cambios

### ¿Afecta la experiencia del usuario?

**NO**, porque:
- El sistema SSE (Server-Sent Events) actualiza en tiempo real cuando llegan notificaciones nuevas
- El caché se invalida automáticamente al marcar como leída
- Los 30 segundos son imperceptibles para el usuario

---

## 🎯 Próximas optimizaciones (opcionales)

Si la app aún tiene problemas de rendimiento:

1. **Cachear lista completa de notificaciones** (no solo el contador)
2. **Lazy loading** de notificaciones (cargar bajo demanda)
3. **Reducir frecuencia de polling** en JavaScript
4. **Usar Redis** en lugar de cache en base de datos

---

## ✅ Checklist de deployment

- [ ] Hacer commit de los cambios
- [ ] Push a GitHub
- [ ] Pull en la EC2
- [ ] Reiniciar Gunicorn
- [ ] Probar navegación (debería ser mucho más rápida)
- [ ] Verificar Network tab (< 10ms en llamadas a `/api/contar/`)
- [ ] Limpiar vistas de test si ya no las necesitas

