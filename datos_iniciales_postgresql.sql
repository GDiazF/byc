-- ============================================================================
-- SCRIPT DE DATOS INICIALES PARA POSTGRESQL - SISTEMA BYC
-- ============================================================================
-- Este script contiene todos los datos iniciales necesarios para que el
-- sistema funcione correctamente. Ejecutar después de crear las tablas.
-- 
-- IMPORTANTE: Ejecutar este script en el orden indicado para respetar
-- las relaciones ForeignKey entre tablas.
-- ============================================================================

-- Desactivar temporalmente las restricciones de claves foráneas (si es necesario)
-- SET session_replication_role = 'replica';

-- ============================================================================
-- 1. REGIONES DE CHILE
-- ============================================================================
-- Tabla: gen_settings_region

INSERT INTO gen_settings_region (nombre) VALUES
('Región de Arica y Parinacota'),
('Región de Tarapacá'),
('Región de Antofagasta'),
('Región de Atacama'),
('Región de Coquimbo'),
('Región de Valparaíso'),
('Región Metropolitana de Santiago'),
('Región del Libertador General Bernardo O''Higgins'),
('Región del Maule'),
('Región de Ñuble'),
('Región del Biobío'),
('Región de La Araucanía'),
('Región de Los Ríos'),
('Región de Los Lagos'),
('Región de Aysén del General Carlos Ibáñez del Campo'),
('Región de Magallanes y de la Antártica Chilena')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 2. COMUNAS DE CHILE (Principales)
-- ============================================================================
-- Tabla: gen_settings_comuna
-- NOTA: Ajustar los region_id según los IDs generados en el paso anterior

INSERT INTO gen_settings_comuna (nombre, region_id) VALUES
-- Región de Arica y Parinacota (region_id = 1)
('Arica', 1),
('Camarones', 1),
('Putre', 1),
('General Lagos', 1),

-- Región de Tarapacá (region_id = 2)
('Iquique', 2),
('Alto Hospicio', 2),
('Pozo Almonte', 2),
('Camiña', 2),
('Colchane', 2),
('Huara', 2),
('Pica', 2),

-- Región de Antofagasta (region_id = 3)
('Antofagasta', 3),
('Mejillones', 3),
('Sierra Gorda', 3),
('Taltal', 3),
('Calama', 3),
('Ollagüe', 3),
('San Pedro de Atacama', 3),
('Tocopilla', 3),
('María Elena', 3),

-- Región de Atacama (region_id = 4)
('Copiapó', 4),
('Caldera', 4),
('Tierra Amarilla', 4),
('Chañaral', 4),
('Diego de Almagro', 4),
('Vallenar', 4),
('Alto del Carmen', 4),
('Freirina', 4),
('Huasco', 4),

-- Región de Coquimbo (region_id = 5)
('La Serena', 5),
('Coquimbo', 5),
('Andacollo', 5),
('La Higuera', 5),
('Paiguano', 5),
('Vicuña', 5),
('Illapel', 5),
('Canela', 5),
('Los Vilos', 5),
('Salamanca', 5),
('Ovalle', 5),
('Combarbalá', 5),
('Monte Patria', 5),
('Punitaqui', 5),
('Río Hurtado', 5),

-- Región de Valparaíso (region_id = 6)
('Valparaíso', 6),
('Casablanca', 6),
('Concón', 6),
('Juan Fernández', 6),
('Puchuncaví', 6),
('Quintero', 6),
('Viña del Mar', 6),
('Isla de Pascua', 6),
('Los Andes', 6),
('Calle Larga', 6),
('Rinconada', 6),
('San Esteban', 6),
('La Ligua', 6),
('Cabildo', 6),
('Papudo', 6),
('Petorca', 6),
('Zapallar', 6),
('Quillota', 6),
('Calera', 6),
('Hijuelas', 6),
('La Cruz', 6),
('Nogales', 6),
('Olmué', 6),
('San Antonio', 6),
('Algarrobo', 6),
('Cartagena', 6),
('El Quisco', 6),
('El Tabo', 6),
('Santo Domingo', 6),
('San Felipe', 6),
('Catemu', 6),
('Llaillay', 6),
('Panquehue', 6),
('Putaendo', 6),
('Santa María', 6),

-- Región Metropolitana de Santiago (region_id = 7)
('Santiago', 7),
('Cerrillos', 7),
('Cerro Navia', 7),
('Conchalí', 7),
('El Bosque', 7),
('Estación Central', 7),
('Huechuraba', 7),
('Independencia', 7),
('La Cisterna', 7),
('La Florida', 7),
('La Granja', 7),
('La Pintana', 7),
('La Reina', 7),
('Las Condes', 7),
('Lo Barnechea', 7),
('Lo Espejo', 7),
('Lo Prado', 7),
('Macul', 7),
('Maipú', 7),
('Ñuñoa', 7),
('Pedro Aguirre Cerda', 7),
('Peñalolén', 7),
('Providencia', 7),
('Pudahuel', 7),
('Quilicura', 7),
('Quinta Normal', 7),
('Recoleta', 7),
('Renca', 7),
('San Joaquín', 7),
('San Miguel', 7),
('San Ramón', 7),
('Vitacura', 7),
('Puente Alto', 7),
('Pirque', 7),
('San José de Maipo', 7),
('Colina', 7),
('Lampa', 7),
('Tiltil', 7),
('San Bernardo', 7),
('Buin', 7),
('Calera de Tango', 7),
('Paine', 7),
('Melipilla', 7),
('Alhué', 7),
('Curacaví', 7),
('María Pinto', 7),
('San Pedro', 7),
('Talagante', 7),
('El Monte', 7),
('Isla de Maipo', 7),
('Padre Hurtado', 7),
('Peñaflor', 7),

-- Región del Libertador General Bernardo O''Higgins (region_id = 8)
('Rancagua', 8),
('Codegua', 8),
('Coinco', 8),
('Coltauco', 8),
('Doñihue', 8),
('Graneros', 8),
('Las Cabras', 8),
('Machalí', 8),
('Malloa', 8),
('Mostazal', 8),
('Olivar', 8),
('Peumo', 8),
('Pichidegua', 8),
('Quinta de Tilcoco', 8),
('Rengo', 8),
('Requínoa', 8),
('San Vicente', 8),
('Pichilemu', 8),
('La Estrella', 8),
('Litueche', 8),
('Marchihue', 8),
('Navidad', 8),
('Paredones', 8),
('San Fernando', 8),
('Chépica', 8),
('Chimbarongo', 8),
('Lolol', 8),
('Nancagua', 8),
('Palmilla', 8),
('Peralillo', 8),
('Placilla', 8),
('Pumanque', 8),
('Santa Cruz', 8),

-- Región del Maule (region_id = 9)
('Talca', 9),
('Constitución', 9),
('Curepto', 9),
('Empedrado', 9),
('Maule', 9),
('Pelarco', 9),
('Pencahue', 9),
('Río Claro', 9),
('San Clemente', 9),
('San Rafael', 9),
('Cauquenes', 9),
('Chanco', 9),
('Pelluhue', 9),
('Curicó', 9),
('Hualañé', 9),
('Licantén', 9),
('Molina', 9),
('Rauco', 9),
('Romeral', 9),
('Sagrada Familia', 9),
('Teno', 9),
('Vichuquén', 9),
('Linares', 9),
('Colbún', 9),
('Longaví', 9),
('Parral', 9),
('Retiro', 9),
('San Javier', 9),
('Villa Alegre', 9),
('Yerbas Buenas', 9),

-- Región de Ñuble (region_id = 10)
('Chillán', 10),
('Bulnes', 10),
('Chillán Viejo', 10),
('El Carmen', 10),
('Pemuco', 10),
('Pinto', 10),
('Quillón', 10),
('San Ignacio', 10),
('Yungay', 10),
('Cobquecura', 10),
('Coelemu', 10),
('Ninhue', 10),
('Portezuelo', 10),
('Quirihue', 10),
('Ránquil', 10),
('Treguaco', 10),
('San Carlos', 10),
('Coihueco', 10),
('Ñiquén', 10),
('San Fabián', 10),
('San Nicolás', 10),

-- Región del Biobío (region_id = 11)
('Concepción', 11),
('Coronel', 11),
('Chiguayante', 11),
('Florida', 11),
('Hualqui', 11),
('Lota', 11),
('Penco', 11),
('San Pedro de la Paz', 11),
('Santa Juana', 11),
('Talcahuano', 11),
('Tomé', 11),
('Hualpén', 11),
('Lebu', 11),
('Arauco', 11),
('Cañete', 11),
('Contulmo', 11),
('Curanilahue', 11),
('Los Álamos', 11),
('Tirúa', 11),
('Los Ángeles', 11),
('Antuco', 11),
('Cabrero', 11),
('Laja', 11),
('Mulchén', 11),
('Nacimiento', 11),
('Negrete', 11),
('Quilaco', 11),
('Quilleco', 11),
('San Rosendo', 11),
('Santa Bárbara', 11),
('Tucapel', 11),
('Yumbel', 11),
('Alto Biobío', 11),

-- Región de La Araucanía (region_id = 12)
('Temuco', 12),
('Carahue', 12),
('Cunco', 12),
('Curarrehue', 12),
('Freire', 12),
('Galvarino', 12),
('Gorbea', 12),
('Lautaro', 12),
('Loncoche', 12),
('Melipeuco', 12),
('Nueva Imperial', 12),
('Padre Las Casas', 12),
('Perquenco', 12),
('Pitrufquén', 12),
('Pucón', 12),
('Saavedra', 12),
('Teodoro Schmidt', 12),
('Toltén', 12),
('Vilcún', 12),
('Villarrica', 12),
('Cholchol', 12),
('Angol', 12),
('Collipulli', 12),
('Curacautín', 12),
('Ercilla', 12),
('Lonquimay', 12),
('Los Sauces', 12),
('Lumaco', 12),
('Purén', 12),
('Renaico', 12),
('Traiguén', 12),
('Victoria', 12),

-- Región de Los Ríos (region_id = 13)
('Valdivia', 13),
('Corral', 13),
('Lanco', 13),
('Los Lagos', 13),
('Máfil', 13),
('Mariquina', 13),
('Paillaco', 13),
('Panguipulli', 13),
('La Unión', 13),
('Futrono', 13),
('Lago Ranco', 13),
('Río Bueno', 13),

-- Región de Los Lagos (region_id = 14)
('Puerto Montt', 14),
('Calbuco', 14),
('Cochamó', 14),
('Fresia', 14),
('Frutillar', 14),
('Los Muermos', 14),
('Llanquihue', 14),
('Maullín', 14),
('Puerto Varas', 14),
('Castro', 14),
('Ancud', 14),
('Chonchi', 14),
('Curaco de Vélez', 14),
('Dalcahue', 14),
('Puqueldón', 14),
('Queilén', 14),
('Quellón', 14),
('Quemchi', 14),
('Quinchao', 14),
('Osorno', 14),
('Puerto Octay', 14),
('Purranque', 14),
('Puyehue', 14),
('Río Negro', 14),
('San Juan de la Costa', 14),
('San Pablo', 14),
('Chaitén', 14),
('Futaleufú', 14),
('Hualaihué', 14),
('Palena', 14),

-- Región de Aysén del General Carlos Ibáñez del Campo (region_id = 15)
('Coyhaique', 15),
('Lago Verde', 15),
('Aysén', 15),
('Cisnes', 15),
('Guaitecas', 15),
('Cochrane', 15),
('O''Higgins', 15),
('Tortel', 15),
('Chile Chico', 15),
('Río Ibáñez', 15),

-- Región de Magallanes y de la Antártica Chilena (region_id = 16)
('Punta Arenas', 16),
('Laguna Blanca', 16),
('Río Verde', 16),
('San Gregorio', 16),
('Cabo de Hornos', 16),
('Antártica', 16),
('Porvenir', 16),
('Primavera', 16),
('Timaukel', 16),
('Natales', 16),
('Torres del Paine', 16)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 3. EMPRESA
-- ============================================================================
-- Tabla: gen_settings_empresa
-- NOTA: Ajustar region_id y comuna_id según los IDs generados

INSERT INTO gen_settings_empresa (rut, dv, "razonSocial", "nomFantasia", giro, direccion, telefono, email, region_id, comuna_id) VALUES
('76543210', 'K', 'GRÚAS BYC LIMITADA', 'Grúas ByC', 'Arriendo de maquinarias y equipos', 'Av. Principal 123', '+56912345678', 'contacto@gruasbyc.cl', 7, (SELECT id FROM gen_settings_comuna WHERE nombre = 'Santiago' LIMIT 1))
ON CONFLICT (rut) DO NOTHING;

-- ============================================================================
-- 4. SEXO
-- ============================================================================
-- Tabla: sexo

INSERT INTO sexo (sexo) VALUES
('MASCULINO'),
('FEMENINO'),
('OTRO')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 5. ESTADO CIVIL
-- ============================================================================
-- Tabla: estadocivil

INSERT INTO estadocivil (estadocivil) VALUES
('SOLTERO/A'),
('CASADO/A'),
('VIUDO/A'),
('DIVORCIADO/A'),
('SEPARADO/A'),
('CONVIVIENTE')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 6. DEPARTAMENTOS DE EMPRESA
-- ============================================================================
-- Tabla: "DeptoEmpresa"

INSERT INTO "DeptoEmpresa" (depto) VALUES
('MAQUINARIAS'),
('OPERACIONES'),
('ADMINISTRACIÓN'),
('RRHH')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 7. CARGOS
-- ============================================================================
-- Tabla: "Cargo"
-- NOTA: Ajustar depto_id según los IDs generados
-- IMPORTANTE: Los cargos se insertan en MAYÚSCULAS para mantener consistencia.
-- El backend usa cargo__iexact (case-insensitive) pero es mejor mantener
-- consistencia. El cargo 'MECÁNICO' es crítico para el filtro de personal en OT.

INSERT INTO "Cargo" (depto_id, cargo) VALUES
-- Cargos para MAQUINARIAS (depto_id = 1)
-- NOTA: 'MECÁNICO' debe estar exactamente así (mayúsculas y acento) para que
-- el filtro de personal en las OT funcione correctamente
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'MECÁNICO'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'RIGGER'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'MAESTRO MECÁNICO'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'TÉCNICO EN MANTENCIÓN'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'SUPERVISOR DE MAQUINARIAS'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'LUBRICADOR'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'SOLDADOR'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'ELECTRICISTA DE MAQUINARIA'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'MAQUINARIAS' LIMIT 1), 'AYUDANTE DE MECÁNICO'),

-- Cargos para OPERACIONES (depto_id = 2)
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'OPERADOR GRÚA'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'OPERADOR MANLIFT'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'OPERADOR CAMIÓN'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'OPERADOR RETROEXCAVADORA'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'OPERADOR CARGADOR FRONTAL'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'OPERADOR EXCAVADORA'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'OPERADOR BULLDOZER'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'SUPERVISOR DE OPERACIONES'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'COORDINADOR DE FAENA'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'PREVENCIONISTA DE RIESGOS'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'OPERACIONES' LIMIT 1), 'CAPATAZ'),

-- Cargos para ADMINISTRACIÓN (depto_id = 3)
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'ADMINISTRACIÓN' LIMIT 1), 'ADMINISTRADOR'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'ADMINISTRACIÓN' LIMIT 1), 'CONTADOR'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'ADMINISTRACIÓN' LIMIT 1), 'SECRETARIA'),

-- Cargos para RRHH (depto_id = 4)
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'RRHH' LIMIT 1), 'JEFE DE RRHH'),
((SELECT depto_id FROM "DeptoEmpresa" WHERE depto = 'RRHH' LIMIT 1), 'ANALISTA DE RRHH')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 8. TIPOS DE AUSENTISMO
-- ============================================================================
-- Tabla: "TipoAusentismo"

INSERT INTO "TipoAusentismo" (tipo) VALUES
('LICENCIA MÉDICA'),
('VACACIONES'),
('PERMISO ADMINISTRATIVO'),
('PERMISO SIN GOCE DE SUELDO'),
('CAPACITACIÓN')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 9. TIPOS DE EXÁMENES
-- ============================================================================
-- Tabla: "TipoExamen"

INSERT INTO "TipoExamen" ("tipoExamen") VALUES
('EXAMEN PREOCUPACIONAL'),
('EXAMEN OCUPACIONAL'),
('EXAMEN DE EGRESO'),
('EXAMEN DE ALTURA'),
('EXAMEN PSICOSENSOTÉCNICO'),
('EXAMEN DE ALCOHOL Y DROGAS')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 10. RESULTADOS DE EXÁMENES
-- ============================================================================
-- Tabla: "ResultadoExamen"

INSERT INTO "ResultadoExamen" (resultado) VALUES
('APTO'),
('APTO CON RESTRICCIONES'),
('NO APTO'),
('PENDIENTE')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 11. TIPOS DE CERTIFICACIONES
-- ============================================================================
-- Tabla: "TipoCertificacion"

INSERT INTO "TipoCertificacion" ("tipoCertificacion") VALUES
('CERTIFICACIÓN DE GRÚA HORQUILLA'),
('CERTIFICACIÓN DE GRÚA TORRE'),
('CERTIFICACIÓN DE TRABAJO EN ALTURA'),
('CERTIFICACIÓN DE ESPACIOS CONFINADOS'),
('CERTIFICACIÓN DE PRIMEROS AUXILIOS'),
('CERTIFICACIÓN DE MANEJO DEFENSIVO'),
('CERTIFICACIÓN DE IZAJE DE CARGAS'),
('CERTIFICACIÓN OPERADOR DE EQUIPOS MÓVILES')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 12. TIPOS DE LICENCIAS DE CONDUCIR
-- ============================================================================
-- Tabla: "TipoLicencia"

INSERT INTO "TipoLicencia" ("tipoLicencia") VALUES
('CLASE A'),
('CLASE B'),
('CLASE C'),
('CLASE D'),
('CLASE E'),
('CLASE F')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 13. TIPOS DE LICENCIAS MÉDICAS
-- ============================================================================
-- Tabla: "TipoLicenciaMedica"

INSERT INTO "TipoLicenciaMedica" ("tipoLicenciaMedica") VALUES
('ENFERMEDAD COMÚN'),
('ACCIDENTE LABORAL'),
('ENFERMEDAD PROFESIONAL'),
('LICENCIA MATERNAL'),
('LICENCIA PATERNAL')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 14. TIPOS DE LICENCIAS INTERNAS
-- ============================================================================
-- Tabla: tipo_licencia_interna

INSERT INTO tipo_licencia_interna ("tipoLicenciaInterna", descripcion) VALUES
('LIC-A', 'Licencia Interna Clase A - Equipos Livianos'),
('LIC-B', 'Licencia Interna Clase B - Equipos Medianos'),
('LIC-C', 'Licencia Interna Clase C - Equipos Pesados'),
('LIC-D', 'Licencia Interna Clase D - Grúas Torre'),
('LIC-E', 'Licencia Interna Clase E - Grúas Móviles')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 15. CLASES DE LICENCIAS (Opcional - depende de uso)
-- ============================================================================
-- NOTA: Esta tabla no aparece en los modelos, pero se menciona en el documento
-- Si existe, descomentar y ajustar según necesidad

-- INSERT INTO "ClaseLicencia" (clase, "tipoLicencia_id") VALUES
-- ('A1', (SELECT "tipoLicencia_id" FROM "TipoLicencia" WHERE "tipoLicencia" = 'CLASE A' LIMIT 1)),
-- ('A2', (SELECT "tipoLicencia_id" FROM "TipoLicencia" WHERE "tipoLicencia" = 'CLASE A' LIMIT 1)),
-- ('B', (SELECT "tipoLicencia_id" FROM "TipoLicencia" WHERE "tipoLicencia" = 'CLASE B' LIMIT 1)),
-- ('C', (SELECT "tipoLicencia_id" FROM "TipoLicencia" WHERE "tipoLicencia" = 'CLASE C' LIMIT 1))
-- ON CONFLICT DO NOTHING;

-- ============================================================================
-- 16. TIPOS DE EQUIPOS
-- ============================================================================
-- Tabla: maquinarias_tipoequipo

INSERT INTO maquinarias_tipoequipo ("tipoEquipo", "siglaEquipo") VALUES
('GRÚA TORRE', 'GT'),
('EXCAVADORA', 'EX'),
('CAMIÓN', 'CM'),
('CARGADOR FRONTAL', 'CF'),
('RETROEXCAVADORA', 'RT'),
('MANLIFT', 'ML'),
('BULLDOZER', 'BD')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 17. MARCAS DE EQUIPOS
-- ============================================================================
-- Tabla: maquinarias_marcaequipo

INSERT INTO maquinarias_marcaequipo ("marcaEquipo") VALUES
('CATERPILLAR'),
('KOMATSU'),
('LIEBHERR'),
('VOLVO'),
('JCB'),
('CASE'),
('HYUNDAI')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 18. MODELOS DE EQUIPOS
-- ============================================================================
-- Tabla: maquinarias_modeloequipo
-- NOTA: Ajustar tipoEquipo_id y marcaEquipo_id según los IDs generados

INSERT INTO maquinarias_modeloequipo ("modeloEquipo", "tipoEquipo_id", "marcaEquipo_id") VALUES
-- Modelos de Excavadoras
('CAT 320D', (SELECT "tipoEquipo_id" FROM maquinarias_tipoequipo WHERE "tipoEquipo" = 'EXCAVADORA' LIMIT 1), (SELECT "marcaEquipo_id" FROM maquinarias_marcaequipo WHERE "marcaEquipo" = 'CATERPILLAR' LIMIT 1)),
('Komatsu PC200', (SELECT "tipoEquipo_id" FROM maquinarias_tipoequipo WHERE "tipoEquipo" = 'EXCAVADORA' LIMIT 1), (SELECT "marcaEquipo_id" FROM maquinarias_marcaequipo WHERE "marcaEquipo" = 'KOMATSU' LIMIT 1)),
('Liebherr R 944', (SELECT "tipoEquipo_id" FROM maquinarias_tipoequipo WHERE "tipoEquipo" = 'EXCAVADORA' LIMIT 1), (SELECT "marcaEquipo_id" FROM maquinarias_marcaequipo WHERE "marcaEquipo" = 'LIEBHERR' LIMIT 1)),

-- Modelos de Grúas Torre
('Liebherr LTM 1200', (SELECT "tipoEquipo_id" FROM maquinarias_tipoequipo WHERE "tipoEquipo" = 'GRÚA TORRE' LIMIT 1), (SELECT "marcaEquipo_id" FROM maquinarias_marcaequipo WHERE "marcaEquipo" = 'LIEBHERR' LIMIT 1)),

-- Modelos de Camiones
('Volvo FMX', (SELECT "tipoEquipo_id" FROM maquinarias_tipoequipo WHERE "tipoEquipo" = 'CAMIÓN' LIMIT 1), (SELECT "marcaEquipo_id" FROM maquinarias_marcaequipo WHERE "marcaEquipo" = 'VOLVO' LIMIT 1)),

-- Modelos de Cargadores Frontales
('CAT 950M', (SELECT "tipoEquipo_id" FROM maquinarias_tipoequipo WHERE "tipoEquipo" = 'CARGADOR FRONTAL' LIMIT 1), (SELECT "marcaEquipo_id" FROM maquinarias_marcaequipo WHERE "marcaEquipo" = 'CATERPILLAR' LIMIT 1))
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 19. ESTADOS DE EQUIPOS
-- ============================================================================
-- Tabla: maquinarias_estadoequipo

INSERT INTO maquinarias_estadoequipo (nombre, descripcion, color, activo, orden) VALUES
('Disponible', 'Equipo disponible para operación', 'success', TRUE, 1),
('Shutdown', 'Equipo fuera de servicio', 'danger', TRUE, 2),
('En Reparación', 'Equipo en proceso de reparación', 'warning', TRUE, 3),
('En Reparación Disponible', 'Equipo en reparación pero disponible', 'info', TRUE, 4)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 20. ESTADOS DE ORDEN DE TRABAJO
-- ============================================================================
-- Tabla: maquinarias_estadoot

INSERT INTO maquinarias_estadoot (nombre, descripcion, color, activo, orden) VALUES
-- IMPORTANTE: Los nombres deben coincidir exactamente con lo que busca el código.
-- El código busca 'Pendiente' (case-sensitive) y 'FINALIZADA'/'CANCELADA' (case-insensitive con iexact)
('Pendiente', 'Orden de trabajo pendiente de iniciar', 'secondary', TRUE, 1),
('En Proceso', 'Orden de trabajo en ejecución', 'primary', TRUE, 2),
('FINALIZADA', 'Orden de trabajo completada', 'success', TRUE, 3),
('CANCELADA', 'Orden de trabajo cancelada', 'danger', TRUE, 4)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 21. TIPOS DE MANTENIMIENTO
-- ============================================================================
-- Tabla: maquinarias_tipomantenimiento

INSERT INTO maquinarias_tipomantenimiento (nombre, descripcion, activo) VALUES
('Preventivo', 'Mantenimiento preventivo programado', TRUE),
('Correctivo', 'Mantenimiento correctivo por falla', TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 22. SECCIONES DE EQUIPOS
-- ============================================================================
-- Tabla: maquinarias_seccion

INSERT INTO maquinarias_seccion (nombre, descripcion) VALUES
('Motor', 'Sistema de motor y componentes relacionados'),
('Radiador', 'Sistema de refrigeración'),
('Sistema Hidráulico', 'Componentes hidráulicos del equipo'),
('Transmisión', 'Sistema de transmisión'),
('Sistema Eléctrico', 'Componentes eléctricos y electrónicos'),
('Sistema de Frenos', 'Sistema de frenado'),
('Sistema de Dirección', 'Sistema de dirección'),
('Chasis', 'Estructura principal del equipo')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 23. TIPOS DE REPARACIÓN
-- ============================================================================
-- Tabla: maquinarias_tiporeparacion
-- NOTA: Ajustar seccion_id según los IDs generados

INSERT INTO maquinarias_tiporeparacion (seccion_id, nombre, descripcion) VALUES
-- Reparaciones de Motor
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Motor' LIMIT 1), 'Cambio de aceite', 'Cambio de aceite del motor'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Motor' LIMIT 1), 'Reemplazo de filtros', 'Reemplazo de filtros de aceite y aire'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Motor' LIMIT 1), 'Ajuste de válvulas', 'Ajuste y calibración de válvulas'),

-- Reparaciones de Radiador
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Radiador' LIMIT 1), 'Limpieza de radiador', 'Limpieza y mantenimiento del radiador'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Radiador' LIMIT 1), 'Reemplazo de mangueras', 'Reemplazo de mangueras del sistema de refrigeración'),

-- Reparaciones de Sistema Hidráulico
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Sistema Hidráulico' LIMIT 1), 'Cambio de aceite hidráulico', 'Cambio de aceite del sistema hidráulico'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Sistema Hidráulico' LIMIT 1), 'Reemplazo de mangueras hidráulicas', 'Reemplazo de mangueras del sistema hidráulico'),

-- Reparaciones de Transmisión
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Transmisión' LIMIT 1), 'Cambio de aceite de transmisión', 'Cambio de aceite del sistema de transmisión'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Transmisión' LIMIT 1), 'Ajuste de transmisión', 'Ajuste y calibración de la transmisión'),

-- Reparaciones de Sistema Eléctrico
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Sistema Eléctrico' LIMIT 1), 'Revisión de sistema eléctrico', 'Revisión general del sistema eléctrico'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Sistema Eléctrico' LIMIT 1), 'Reemplazo de batería', 'Reemplazo de batería del equipo'),

-- Reparaciones de Sistema de Frenos
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Sistema de Frenos' LIMIT 1), 'Revisión de frenos', 'Revisión y ajuste del sistema de frenos'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Sistema de Frenos' LIMIT 1), 'Reemplazo de pastillas', 'Reemplazo de pastillas de freno'),

-- Reparaciones de Sistema de Dirección
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Sistema de Dirección' LIMIT 1), 'Alineación', 'Alineación del sistema de dirección'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Sistema de Dirección' LIMIT 1), 'Revisión de dirección', 'Revisión general del sistema de dirección'),

-- Reparaciones de Chasis
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Chasis' LIMIT 1), 'Revisión de chasis', 'Revisión general del chasis'),
((SELECT seccion_id FROM maquinarias_seccion WHERE nombre = 'Chasis' LIMIT 1), 'Soldadura de chasis', 'Reparación por soldadura del chasis')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 24. ESTADOS DE CALENDARIO DE EQUIPOS
-- ============================================================================
-- Tabla: maquinarias_estadocalendarioequipo

INSERT INTO maquinarias_estadocalendarioequipo (nombre, nombre_corto, color, background_color, prioridad, es_bloqueante, es_predeterminado, activo) VALUES
('Disponible', 'DISP', '#000000', '#FFFFFF', 10, FALSE, TRUE, TRUE),
('En Mantenimiento', 'MANT', '#FFA500', '#FFF8DC', 20, FALSE, FALSE, TRUE),
('En Reparación', 'REP', '#FF0000', '#FFE4E1', 30, FALSE, FALSE, TRUE),
('Fuera de Servicio', 'FUERA', '#800000', '#F5F5F5', 40, TRUE, FALSE, TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 25. TIPOS DE DOCUMENTOS DE MAQUINARIAS
-- ============================================================================
-- Tabla: maquinarias_tipodocumento

INSERT INTO maquinarias_tipodocumento (nombre, descripcion, requiere_fecha_vencimiento, activo) VALUES
('Revisión Técnica', 'Documento de revisión técnica del vehículo', TRUE, TRUE),
('Seguro', 'Póliza de seguro del equipo', TRUE, TRUE),
('Permiso de Circulación', 'Permiso de circulación vigente', TRUE, TRUE),
('Certificado de Inspección', 'Certificado de inspección técnica', TRUE, TRUE),
('Manual de Operación', 'Manual de operación del equipo', FALSE, TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 26. ESTADOS DE CALENDARIO DE OPERACIONES
-- ============================================================================
-- Tabla: ope_calendario_estado

INSERT INTO ope_calendario_estado (nombre, nombre_corto, color, background_color, prioridad, es_bloqueante, es_predeterminado, activo) VALUES
('Día', 'D', '#000000', '#FFFFFF', 10, FALSE, TRUE, TRUE),
('Noche', 'N', '#000000', '#000080', 20, FALSE, FALSE, TRUE),
('Descanso', 'DESC', '#000000', '#D3D3D3', 5, FALSE, FALSE, TRUE),
('Licencia', 'LIC', '#FFFFFF', '#FFA500', 30, FALSE, FALSE, TRUE),
('Vacaciones', 'VAC', '#FFFFFF', '#008000', 25, FALSE, FALSE, TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 27. ROLES DEL SISTEMA
-- ============================================================================
-- Tabla: gen_permissions_rol

INSERT INTO gen_permissions_rol (nombre, descripcion, activo) VALUES
('Administrador', 'Rol con todos los permisos del sistema', TRUE),
('Supervisor', 'Rol con permisos de supervisión y gestión', TRUE),
('Usuario', 'Rol básico con permisos de visualización', TRUE),
('Operador', 'Rol para operadores de equipos', TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 28. UNIDADES DE MEDIDA
-- ============================================================================
-- Tabla: gen_settings_unidadmedida

INSERT INTO gen_settings_unidadmedida (nombre, simbolo) VALUES
('Litros', 'L'),
('Kilogramos', 'kg'),
('Metros', 'm'),
('Unidades', 'un'),
('Horas', 'hrs')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 29. TIPOS DE CLASIFICACIÓN DE PROVEEDORES
-- ============================================================================
-- Tabla: "TipoClasificacion"

INSERT INTO "TipoClasificacion" (tipo) VALUES
('Clínica'),
('Laboratorio'),
('Centro de Exámenes'),
('Centro de Certificación')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 30. USUARIO SUPERUSUARIO (Django Auth)
-- ============================================================================
-- NOTA: Este usuario se debe crear desde Django o usando el comando createsuperuser
-- El password debe ser hasheado con el algoritmo de Django (PBKDF2)
-- Ejemplo de creación manual (ajustar password hash según necesidad):
-- 
-- INSERT INTO auth_user (username, password, is_superuser, is_staff, is_active, date_joined, first_name, last_name, email) VALUES
-- ('admin', 'pbkdf2_sha256$600000$...', TRUE, TRUE, TRUE, NOW(), 'Administrador', 'Sistema', 'admin@gruasbyc.cl')
-- ON CONFLICT (username) DO NOTHING;
--
-- IMPORTANTE: Es mejor crear el superusuario usando:
-- python manage.py createsuperuser

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
-- Verificar que todos los datos se insertaron correctamente ejecutando:
-- SELECT 'Regiones' as tabla, COUNT(*) as cantidad FROM gen_settings_region
-- UNION ALL
-- SELECT 'Comunas', COUNT(*) FROM gen_settings_comuna
-- UNION ALL
-- SELECT 'Empresas', COUNT(*) FROM gen_settings_empresa
-- UNION ALL
-- SELECT 'Sexos', COUNT(*) FROM sexo
-- UNION ALL
-- SELECT 'Estados Civiles', COUNT(*) FROM estadocivil
-- UNION ALL
-- SELECT 'Departamentos', COUNT(*) FROM "DeptoEmpresa"
-- UNION ALL
-- SELECT 'Cargos', COUNT(*) FROM "Cargo"
-- UNION ALL
-- SELECT 'Tipos de Equipos', COUNT(*) FROM maquinarias_tipoequipo
-- UNION ALL
-- SELECT 'Marcas de Equipos', COUNT(*) FROM maquinarias_marcaequipo
-- UNION ALL
-- SELECT 'Modelos de Equipos', COUNT(*) FROM maquinarias_modeloequipo
-- UNION ALL
-- SELECT 'Estados de Equipos', COUNT(*) FROM maquinarias_estadoequipo
-- UNION ALL
-- SELECT 'Estados de OT', COUNT(*) FROM maquinarias_estadoot
-- UNION ALL
-- SELECT 'Tipos de Mantenimiento', COUNT(*) FROM maquinarias_tipomantenimiento
-- UNION ALL
-- SELECT 'Secciones', COUNT(*) FROM maquinarias_seccion
-- UNION ALL
-- SELECT 'Tipos de Reparación', COUNT(*) FROM maquinarias_tiporeparacion
-- UNION ALL
-- SELECT 'Estados Calendario Equipos', COUNT(*) FROM maquinarias_estadocalendarioequipo
-- UNION ALL
-- SELECT 'Tipos Documentos Maquinarias', COUNT(*) FROM maquinarias_tipodocumento
-- UNION ALL
-- SELECT 'Estados Calendario Operaciones', COUNT(*) FROM ope_calendario_estado
-- UNION ALL
-- SELECT 'Roles', COUNT(*) FROM gen_permissions_rol
-- UNION ALL
-- SELECT 'Unidades de Medida', COUNT(*) FROM gen_settings_unidadmedida;

