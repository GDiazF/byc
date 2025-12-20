# Especificación de Requisitos de Software (ERS)
## Requerimientos Funcionales - Análisis de Código

Este documento contiene los requerimientos funcionales identificados mediante ingeniería inversa del código implementado.

---

## Módulo: Recursos Humanos (RRHH)

| Sigla | Título | Descripción Técnica (Basada en el código) |
| :--- | :--- | :--- |
| RF-RRHH-01 | Gestión de Personal | El sistema permite crear, leer, actualizar y borrar (CRUD) fichas de personal. Datos gestionados: RUT (único), DV RUT, Nombre, Apellido Paterno (obligatorio), Apellido Materno (opcional), Fecha Nacimiento, Sexo, Estado Civil, Correo (único), Dirección, Región, Comuna, Estado Activo/Inactivo. Validaciones: RUT único, correo único, apellido materno opcional. El sistema normaliza todos los campos de texto a mayúsculas automáticamente. |
| RF-RRHH-02 | Gestión de Documentos Personales | El sistema permite subir y gestionar documentos personales asociados a cada trabajador. Documentos soportados: Curriculum, Certificado Antecedentes, Hoja de Vida Conductor, Foto Carnet, Certificado AFP, Certificado Salud, Certificado Estudios, Certificado Residencia, Fotocopia Carnet, Fotocopia Finiquito, Comprobante Banco. Los archivos se organizan automáticamente por RUT del personal y tipo de documento. El sistema mantiene historial de documentos eliminados. |
| RF-RRHH-03 | Gestión de Información Laboral | El sistema permite registrar y actualizar información laboral del personal. Datos: Empresa, Departamento, Cargo, Fecha Contratación. El sistema permite múltiples registros históricos de información laboral por persona. |
| RF-RRHH-04 | Gestión de Ausentismos | El sistema permite registrar ausentismos del personal. Datos: Personal, Tipo Ausentismo, Fecha Inicio, Fecha Fin, Observaciones. Validaciones: Fecha fin debe ser posterior a fecha inicio. El sistema genera notificaciones automáticas cuando se crea un ausentismo. |
| RF-RRHH-05 | Gestión de Licencias de Conducir | El sistema permite registrar licencias de conducir del personal. Datos: Personal, Tipo Licencia, Número Licencia, Fecha Emisión, Fecha Vencimiento, Archivo PDF. Validaciones: Fecha vencimiento debe ser posterior a fecha emisión. El sistema permite subir documentos PDF asociados. |
| RF-RRHH-06 | Gestión de Licencias Médicas | El sistema permite registrar licencias médicas del personal. Datos: Personal, Tipo Licencia Médica, Fecha Emisión, Días Licencia, Fecha Fin (calculada automáticamente), Archivo PDF. El sistema calcula automáticamente la fecha fin basada en días de licencia. |
| RF-RRHH-07 | Gestión de Licencias Internas | El sistema permite registrar licencias internas del personal. Datos: Personal, Tipo Licencia Interna, Fecha Emisión, Fecha Vencimiento, Archivo PDF. Validaciones: Fecha vencimiento debe ser posterior a fecha emisión. |
| RF-RRHH-08 | Gestión de Certificaciones | El sistema permite registrar certificaciones del personal. Datos: Personal, Tipo Certificación, Fecha Emisión, Fecha Vencimiento, Archivo PDF. Validaciones: Fecha vencimiento debe ser posterior a fecha emisión. |
| RF-RRHH-09 | Gestión de Exámenes Médicos | El sistema permite registrar exámenes médicos del personal. Datos: Personal, Tipo Examen, Fecha Realización, Resultado Examen, Archivo PDF. El sistema mantiene historial de exámenes realizados. |
| RF-RRHH-10 | Historial de Cambios de Personal | El sistema mantiene un historial completo de cambios realizados en los datos del personal. Registra: Campo modificado, Valor anterior, Valor nuevo, Usuario que realizó el cambio, Fecha y hora del cambio. |
| RF-RRHH-11 | Historial de Documentos | El sistema mantiene historial de documentos eliminados o reemplazados. Datos: Documento original, Ruta del archivo, Fecha eliminación, Usuario que eliminó, Motivo. Los archivos eliminados se mueven a carpeta de eliminados en lugar de borrarse físicamente. |
| RF-RRHH-12 | Gestión de Proveedores | El sistema permite gestionar proveedores de servicios médicos y otros. Datos: Nombre Proveedor, Tipo Clasificación, Contacto. El sistema permite asociar proveedores a exámenes y certificaciones. |
| RF-RRHH-13 | Catálogos Maestros RRHH | El sistema mantiene catálogos maestros para: Sexo, Estado Civil, Tipo Ausentismo, Tipo Licencia, Tipo Licencia Médica, Tipo Licencia Interna, Tipo Certificación, Tipo Examen, Resultado Examen, Tipo Clasificación Proveedor, Departamento Empresa, Cargo. Estos catálogos permiten configuración dinámica sin modificar código. |

---

## Módulo: Maquinarias

| Sigla | Título | Descripción Técnica (Basada en el código) |
| :--- | :--- | :--- |
| RF-MAQ-01 | Gestión de Tipos de Equipos | El sistema permite crear y gestionar tipos de equipos. Datos: Nombre Tipo Equipo, Sigla (única). Ejemplos: Grúa Torre (GT), Grúa Telescópica (GT), Camión Mixer (CM). Validaciones: Sigla única. |
| RF-MAQ-02 | Gestión de Marcas de Equipos | El sistema permite crear y gestionar marcas de equipos. Datos: Nombre Marca. Ejemplos: Caterpillar, Komatsu, Liebherr. |
| RF-MAQ-03 | Gestión de Modelos de Equipos | El sistema permite crear y gestionar modelos de equipos. Datos: Nombre Modelo, Tipo Equipo, Marca Equipo. Validaciones: La combinación de Tipo, Marca y Nombre de Modelo debe ser única. |
| RF-MAQ-04 | Gestión de Equipos | El sistema permite crear, leer, actualizar y borrar (CRUD) fichas de equipos. Datos: Empresa, Modelo Equipo, Código Interno (numérico, único por tipo de equipo), Patente (única), Horómetro, Odómetro, Horómetro Superestructural, Estado Activo/Inactivo. Validaciones: Patente única, código interno numérico, combinación Tipo Equipo + Código Interno única (incluso si el equipo está desactivado). El nombre del equipo se genera automáticamente como: {SiglaTipo}{CodigoInterno} - {Patente}. |
| RF-MAQ-05 | Gestión de Documentos de Equipos | El sistema permite subir y gestionar documentos asociados a cada equipo. Datos: Equipo, Tipo Documento, Archivo PDF, Fecha Vencimiento (opcional según tipo). Los documentos se organizan automáticamente por ID de equipo y tipo de documento. El sistema mantiene historial de documentos eliminados o reemplazados. |
| RF-MAQ-06 | Gestión de Tipos de Documentos | El sistema permite configurar tipos de documentos para equipos. Datos: Nombre Tipo Documento, Requiere Fecha Vencimiento (booleano). Ejemplos: Permiso de Circulación, Seguro, Revisión Técnica. |
| RF-MAQ-07 | Gestión de Órdenes de Trabajo | El sistema permite crear y gestionar órdenes de trabajo (OT) para equipos. Datos: Folio (único, auto-generado), Equipo, Tipo Mantenimiento, Tipo Reparación, Sección, Estado OT, Estado Equipo, Fecha Inicio, Fecha Fin, Observaciones, Items de Sección. Validaciones: Fecha fin debe ser posterior a fecha inicio. El sistema permite agregar múltiples items por sección. |
| RF-MAQ-08 | Gestión de Items de Órdenes de Trabajo | El sistema permite agregar items detallados a las órdenes de trabajo. Datos: Orden Trabajo, Sección, Descripción Item, Cantidad, Unidad Medida, Precio Unitario, Total (calculado). El sistema calcula automáticamente el total por item y el total general de la OT. |
| RF-MAQ-09 | Gestión de Estados de Equipos | El sistema permite configurar estados dinámicos para equipos. Datos: Nombre Estado, Color Texto, Color Fondo, Prioridad, Es Bloqueante, Es Predeterminado. El sistema permite mapear estados a fuentes externas (otros modelos) mediante GenericForeignKey. |
| RF-MAQ-10 | Gestión de Estados Manuales de Equipos | El sistema permite asignar estados manuales a equipos por rangos de fechas. Datos: Equipo, Estado, Fecha Inicio, Fecha Fin, Observaciones. Validaciones: Fecha fin debe ser posterior a fecha inicio, no puede haber solapamiento de estados bloqueantes. |
| RF-MAQ-11 | Gestión de Pautas de Mantenimiento Preventivo | El sistema permite crear pautas de mantenimiento preventivo. Datos: Nombre Pauta, Tipo Equipo, Items de Pauta (descripción, frecuencia). El sistema permite asociar pautas a tipos de equipos específicos. |
| RF-MAQ-12 | Gestión de Tipos de Mantenimiento | El sistema permite configurar tipos de mantenimiento. Datos: Nombre Tipo Mantenimiento. Ejemplos: Preventivo, Correctivo, Predictivo. |
| RF-MAQ-13 | Gestión de Tipos de Reparación | El sistema permite configurar tipos de reparación. Datos: Nombre Tipo Reparación. |
| RF-MAQ-14 | Gestión de Secciones de OT | El sistema permite configurar secciones para organizar items en órdenes de trabajo. Datos: Nombre Sección. |
| RF-MAQ-15 | Historial de Órdenes de Trabajo | El sistema mantiene historial completo de cambios en órdenes de trabajo. Registra: Campo modificado, Valor anterior, Valor nuevo, Usuario, Fecha y hora. |
| RF-MAQ-16 | Historial de Observaciones de OT | El sistema mantiene historial de observaciones agregadas a órdenes de trabajo. Datos: Orden Trabajo, Observación, Usuario, Fecha y hora. |
| RF-MAQ-17 | Historial de Equipos | El sistema mantiene historial completo de cambios en equipos. Registra: Campo modificado, Valor anterior, Valor nuevo, Usuario, Fecha y hora. |
| RF-MAQ-18 | Historial de Documentos de Equipos | El sistema mantiene historial de documentos eliminados o reemplazados. Datos: Documento original, Equipo, Tipo Documento, Ruta archivo, Fecha eliminación, Usuario. Los archivos eliminados se mueven a carpeta de eliminados. |

---

## Módulo: Operaciones y Calendario

| Sigla | Título | Descripción Técnica (Basada en el código) |
| :--- | :--- | :--- |
| RF-OPE-01 | Gestión de Estados Dinámicos | El sistema permite configurar estados dinámicos para el personal en operaciones. Datos: Nombre Estado, Nombre Corto, Color Texto, Color Fondo, Prioridad, Es Bloqueante, Es Predeterminado, Activo. Validaciones: Solo puede haber un estado predeterminado activo. El sistema permite mapear estados a fuentes externas mediante GenericForeignKey. |
| RF-OPE-02 | Gestión de Fuentes de Estados | El sistema permite mapear estados a modelos externos (Ausentismo, Licencia Médica, etc.). Datos: Estado, Content Type (modelo origen), Campo Fecha Inicio, Campo Fecha Fin, Campo Personal, Filtro Extra (JSON). Esto permite que el sistema consulte automáticamente si una persona está en un estado específico según datos de otros módulos. |
| RF-OPE-03 | Gestión de Turnos | El sistema permite crear y configurar turnos de trabajo. Datos: Nombre Turno, Descripción, Activo. Ejemplos: 7x7, 7x7x7x7, 5x2, 15x15. Los turnos se definen mediante bloques (TurnoBloque). |
| RF-OPE-04 | Gestión de Bloques de Turnos | El sistema permite definir la secuencia de bloques de un turno. Datos: Turno, Orden, Estado, Duración (días). El sistema permite crear turnos personalizados con cualquier secuencia de estados y duraciones. |
| RF-OPE-05 | Gestión de Faenas | El sistema permite crear y gestionar faenas (proyectos/obras). Datos: Nombre Faena, Empresa, Descripción, Fecha Inicio, Fecha Fin, Activa. Validaciones: Fecha fin debe ser posterior a fecha inicio. |
| RF-OPE-06 | Asignación de Personal a Faenas | El sistema permite asignar personal a faenas con turnos específicos. Datos: Personal, Faena, Turno, Bloque Inicio, Fecha Inicio, Fecha Fin, Observaciones. Validaciones: Fecha fin debe ser posterior a fecha inicio, no puede haber solapamiento de asignaciones bloqueantes. El sistema genera estados automáticamente según el turno asignado. |
| RF-OPE-07 | Asignación de Equipos a Faenas | El sistema permite asignar equipos a faenas. Datos: Equipo, Faena, Fecha Inicio, Fecha Fin, Observaciones. Validaciones: Fecha fin debe ser posterior a fecha inicio. |
| RF-OPE-08 | Gestión de Estados Manuales | El sistema permite asignar estados manuales al personal por rangos de fechas. Datos: Personal, Estado, Fecha Inicio, Fecha Fin, Observaciones. Validaciones: Fecha fin debe ser posterior a fecha inicio, no puede haber solapamiento de estados bloqueantes. Los estados manuales tienen prioridad sobre estados generados automáticamente. |
| RF-OPE-09 | Historial de Faenas | El sistema mantiene historial completo de cambios en faenas. Registra: Campo modificado, Valor anterior, Valor nuevo, Usuario, Fecha y hora. |
| RF-OPE-10 | Visualización de Calendario | El sistema permite visualizar calendarios mensuales con asignaciones de personal y equipos. Muestra estados por día, permite filtros por faena, personal, equipo, fecha. El sistema consolida estados automáticos (de turnos) y manuales, respetando prioridades y estados bloqueantes. |

---

## Módulo: Notificaciones

| Sigla | Título | Descripción Técnica (Basada en el código) |
| :--- | :--- | :--- |
| RF-NOT-01 | Gestión de Tipos de Notificaciones | El sistema permite configurar tipos de notificaciones. Datos: Código (único), Nombre, Descripción, Categoría (RRHH, MAQUINARIAS, PLANIFICACION, GENERAL), Prioridad (ALTA, MEDIA, BAJA), Template Título, Template Mensaje, Activo. Ejemplos de códigos: RRHH_PERSONAL_ACTIVADO, MAQUINARIAS_EQUIPO_ACTIVADO. |
| RF-NOT-02 | Configuración de Notificaciones por Rol | El sistema permite configurar qué tipos de notificaciones recibe cada rol. Datos: Rol, Tipo Notificación, Activo. Cuando se crea una notificación de un tipo específico, se buscan los roles habilitados y se crean notificaciones para todos los usuarios con esos roles. |
| RF-NOT-03 | Gestión de Notificaciones | El sistema permite crear, leer, marcar como leída y archivar notificaciones para usuarios. Datos: Usuario, Tipo Notificación, Título, Mensaje, Datos Adicionales (JSON), Leída, Fecha Leída, Prioridad, Archivada, Fecha Archivada, Fecha Creación. El sistema mantiene índices optimizados para consultas frecuentes por usuario y estado de lectura. |
| RF-NOT-04 | Notificaciones Automáticas | El sistema genera notificaciones automáticamente mediante signals de Django cuando ocurren eventos específicos (creación de ausentismo, activación de personal, etc.). Las notificaciones se crean según la configuración de roles y tipos de notificaciones. |
| RF-NOT-05 | API de Notificaciones | El sistema proporciona APIs para: obtener notificaciones no leídas, contar notificaciones no leídas, marcar como leída, archivar, desarchivar. El sistema utiliza caché para optimizar el conteo de notificaciones no leídas. |

---

## Módulo: Vencimientos de Documentos

| Sigla | Título | Descripción Técnica (Basada en el código) |
| :--- | :--- | :--- |
| RF-VEN-01 | Consulta de Vencimientos de Documentos | El sistema permite consultar documentos próximos a vencer (personal y equipos). Datos mostrados: Personal/Equipo, Tipo Documento, Fecha Vencimiento, Días Restantes, Estado (Vigente, Por Vencer, Vencido). El sistema permite filtrar por tipo de documento, días restantes, estado, solo activos. Validaciones: Calcula días restantes automáticamente basado en fecha actual. |
| RF-VEN-02 | Procesamiento Automático de Vencimientos | El sistema ejecuta procesamiento automático de vencimientos (mediante tarea programada o manual). Identifica documentos que vencen en los próximos 45 días y genera notificaciones automáticas según configuración de roles. El sistema permite ejecución manual para pruebas. |

---

## Módulo: Configuraciones Generales (Transversales)

| Sigla | Título | Descripción Técnica (Basada en el código) |
| :--- | :--- | :--- |
| RF-GRAL-01 | Gestión de Regiones | El sistema permite gestionar regiones de Chile. Datos: Nombre Región. Se utiliza para asociar direcciones y ubicaciones geográficas. |
| RF-GRAL-02 | Gestión de Comunas | El sistema permite gestionar comunas asociadas a regiones. Datos: Nombre Comuna, Región. Se utiliza junto con Region para formar direcciones completas. |
| RF-GRAL-03 | Gestión de Empresas | El sistema permite crear y gestionar empresas del sistema. Datos: RUT (único), DV, Razón Social, Nombre Fantasía, Giro, Dirección, Teléfono, Email, Región, Comuna. Validaciones: RUT único. Las empresas se utilizan en múltiples módulos para asociar recursos (personal, equipos, etc.). |
| RF-GRAL-04 | Gestión de Unidades de Medida | El sistema permite gestionar unidades de medida. Datos: Código (único, 3 caracteres), Descripción. Se utiliza para inventarios, materiales, repuestos y otros elementos que requieren especificar cantidad con unidad (ej: kg, litros, metros, unidades). |
| RF-GRAL-05 | Gestión de Roles | El sistema permite crear y gestionar roles que agrupan permisos. Datos: Nombre Rol (único), Descripción, Permisos (ManyToMany con Permission de Django), Activo. Al asignar un rol a un usuario, este hereda automáticamente todos los permisos del rol mediante signals. |
| RF-GRAL-06 | Gestión de Perfiles de Usuario | El sistema extiende el modelo User de Django con UserProfile. Datos: Usuario (OneToOne), Rol, Fecha Asignación Rol, Fecha Modificación Rol. Cuando se asigna un rol, se asignan automáticamente todos los permisos del rol. El sistema crea automáticamente un UserProfile cuando se crea un User. |
| RF-GRAL-07 | Gestión de Permisos de Vista | El sistema permite crear permisos para vistas que no tienen modelo asociado. Datos: Código Permiso (único), Nombre, Descripción, App Label, Vista Nombre, Permission de Django (OneToOne), Activo. Ejemplo: dashboards.view_dashboard_rrhh. |
| RF-GRAL-08 | Gestión de Permisos de Acción | El sistema permite crear permisos personalizados para acciones específicas dentro de un modelo. Datos: Código Permiso (único), Nombre, Descripción, Modelo (ContentType), Acción, Permission de Django (OneToOne), Activo. Ejemplos: rrhh_personal.desactivar_personal, rrhh_personal.activar_personal. |
| RF-GRAL-09 | Catálogo de Permisos por Modelo | El sistema mantiene un catálogo de permisos disponibles por modelo (para referencia y documentación). Datos: Modelo (ContentType), App Label, Nombre Modelo, Permisos Disponibles (JSON). |
| RF-GRAL-10 | Autenticación y Autorización | El sistema utiliza el sistema de autenticación de Django. Requiere login para acceder a las funcionalidades. El sistema verifica permisos en cada vista mediante decoradores y mixins. Los permisos se asignan automáticamente según el rol del usuario. |
| RF-GRAL-11 | Widget de Fecha Chilena | El sistema proporciona un widget personalizado para campos de fecha que muestra formato DD/MM/YYYY al usuario pero almacena formato ISO (YYYY-MM-DD) en la base de datos. El widget permite entrada manual con formato automático y validación de fechas. |

---

## Módulo: Reportes y Auditoría

| Sigla | Título | Descripción Técnica (Basada en el código) |
| :--- | :--- | :--- |
| RF-AUD-01 | Historial de Cambios | El sistema mantiene historial completo de cambios en modelos críticos (Personal, Equipo, Orden Trabajo, Faena). Para cada cambio registra: Campo modificado, Valor anterior, Valor nuevo, Usuario que realizó el cambio, Fecha y hora del cambio. |
| RF-AUD-02 | Historial de Documentos | El sistema mantiene historial de documentos eliminados o reemplazados. Para cada documento eliminado registra: Documento original, Entidad asociada (Personal/Equipo), Tipo Documento, Ruta del archivo, Fecha eliminación, Usuario que eliminó. Los archivos eliminados se mueven a carpeta de eliminados en lugar de borrarse físicamente. |

---

## Notas Técnicas Generales

- **Almacenamiento de Archivos**: El sistema utiliza almacenamiento S3 (AWS) en producción y sistema de archivos local en desarrollo. Los archivos se organizan automáticamente en carpetas según tipo de entidad y documento.

- **Validaciones de Fechas**: El sistema valida que fechas fin sean posteriores a fechas inicio en todos los modelos que manejan rangos de fechas.

- **Normalización de Texto**: El sistema normaliza automáticamente todos los campos de texto a mayúsculas antes de guardar (excepto campos específicos como correos).

- **Estados Bloqueantes**: El sistema implementa lógica de estados bloqueantes que previenen solapamiento de estados conflictivos.

- **Signals de Django**: El sistema utiliza signals de Django para automatizar procesos como asignación de permisos, creación de notificaciones y mantenimiento de historiales.

- **Generic Foreign Keys**: El sistema utiliza GenericForeignKey para permitir relaciones flexibles entre modelos (ej: estados mapeados a diferentes modelos).

- **Caché**: El sistema utiliza caché de Django para optimizar consultas frecuentes como conteo de notificaciones no leídas.

