# Generated migration for initial data
from django.db import migrations
from datetime import datetime, timedelta
import random


def generar_rut_chileno():
    """Genera un RUT chileno válido"""
    rut = random.randint(10000000, 25000000)
    serie = [2, 3, 4, 5, 6, 7]
    suma = 0
    multiplicador = 0
    
    for digito in str(rut)[::-1]:
        suma += int(digito) * serie[multiplicador % 6]
        multiplicador += 1
    
    resto = suma % 11
    dv = 11 - resto
    
    if dv == 11:
        dv = '0'
    elif dv == 10:
        dv = 'K'
    else:
        dv = str(dv)
    
    return str(rut), dv


def crear_datos_iniciales(apps, schema_editor):
    # Obtener modelos
    Region = apps.get_model('gen_settings', 'Region')
    Comuna = apps.get_model('gen_settings', 'Comuna')
    Empresa = apps.get_model('gen_settings', 'Empresa')
    Sexo = apps.get_model('rrhh_personal', 'Sexo')
    EstadoCivil = apps.get_model('rrhh_personal', 'EstadoCivil')
    DeptoEmpresa = apps.get_model('rrhh_personal', 'DeptoEmpresa')
    Cargo = apps.get_model('rrhh_personal', 'Cargo')
    Personal = apps.get_model('rrhh_personal', 'Personal')
    InfoLaboral = apps.get_model('rrhh_personal', 'InfoLaboral')
    TipoAusentismo = apps.get_model('rrhh_personal', 'TipoAusentismo')
    TipoExamen = apps.get_model('rrhh_personal', 'TipoExamen')
    ResultadoExamen = apps.get_model('rrhh_personal', 'ResultadoExamen')
    TipoCertificacion = apps.get_model('rrhh_personal', 'TipoCertificacion')
    TipoLicencia = apps.get_model('rrhh_personal', 'TipoLicencia')
    TipoLicenciaMedica = apps.get_model('rrhh_personal', 'TipoLicenciaMedica')
    TipoLicenciaInterna = apps.get_model('rrhh_personal', 'TipoLicenciaInterna')
    
    # 1. SEXOS
    print("Creando Sexos...")
    sexos_data = ['MASCULINO', 'FEMENINO', 'OTRO']
    sexos = {}
    for sexo in sexos_data:
        s = Sexo.objects.create(sexo=sexo)
        sexos[sexo] = s
    
    # 2. ESTADOS CIVILES
    print("Creando Estados Civiles...")
    estados_civiles_data = ['SOLTERO/A', 'CASADO/A', 'VIUDO/A', 'DIVORCIADO/A', 'SEPARADO/A', 'CONVIVIENTE']
    estados_civiles = {}
    for estado in estados_civiles_data:
        ec = EstadoCivil.objects.create(estadocivil=estado)
        estados_civiles[estado] = ec
    
    # 3. REGIONES DE CHILE
    print("Creando Regiones de Chile...")
    regiones_data = [
        'Región de Arica y Parinacota',
        'Región de Tarapacá',
        'Región de Antofagasta',
        'Región de Atacama',
        'Región de Coquimbo',
        'Región de Valparaíso',
        'Región Metropolitana de Santiago',
        'Región del Libertador General Bernardo O\'Higgins',
        'Región del Maule',
        'Región de Ñuble',
        'Región del Biobío',
        'Región de La Araucanía',
        'Región de Los Ríos',
        'Región de Los Lagos',
        'Región de Aysén del General Carlos Ibáñez del Campo',
        'Región de Magallanes y de la Antártica Chilena',
    ]
    
    regiones = {}
    for region in regiones_data:
        r = Region.objects.create(nombre=region)
        regiones[region] = r
    
    # 4. COMUNAS DE CHILE (principales por región)
    print("Creando Comunas de Chile...")
    comunas_data = {
        'Región de Arica y Parinacota': ['Arica', 'Camarones', 'Putre', 'General Lagos'],
        'Región de Tarapacá': ['Iquique', 'Alto Hospicio', 'Pozo Almonte', 'Camiña', 'Colchane', 'Huara', 'Pica'],
        'Región de Antofagasta': ['Antofagasta', 'Mejillones', 'Sierra Gorda', 'Taltal', 'Calama', 'Ollagüe', 'San Pedro de Atacama', 'Tocopilla', 'María Elena'],
        'Región de Atacama': ['Copiapó', 'Caldera', 'Tierra Amarilla', 'Chañaral', 'Diego de Almagro', 'Vallenar', 'Alto del Carmen', 'Freirina', 'Huasco'],
        'Región de Coquimbo': ['La Serena', 'Coquimbo', 'Andacollo', 'La Higuera', 'Paihuano', 'Vicuña', 'Illapel', 'Canela', 'Los Vilos', 'Salamanca', 'Ovalle', 'Combarbalá', 'Monte Patria', 'Punitaqui', 'Río Hurtado'],
        'Región de Valparaíso': ['Valparaíso', 'Casablanca', 'Concón', 'Juan Fernández', 'Puchuncaví', 'Quintero', 'Viña del Mar', 'Isla de Pascua', 'Los Andes', 'Calle Larga', 'Rinconada', 'San Esteban', 'La Ligua', 'Cabildo', 'Papudo', 'Petorca', 'Zapallar', 'Quillota', 'Calera', 'Hijuelas', 'La Cruz', 'Nogales', 'San Antonio', 'Algarrobo', 'Cartagena', 'El Quisco', 'El Tabo', 'Santo Domingo', 'San Felipe', 'Catemu', 'Llaillay', 'Panquehue', 'Putaendo', 'Santa María', 'Quilpué', 'Limache', 'Olmué', 'Villa Alemana'],
        'Región Metropolitana de Santiago': ['Santiago', 'Cerrillos', 'Cerro Navia', 'Conchalí', 'El Bosque', 'Estación Central', 'Huechuraba', 'Independencia', 'La Cisterna', 'La Florida', 'La Granja', 'La Pintana', 'La Reina', 'Las Condes', 'Lo Barnechea', 'Lo Espejo', 'Lo Prado', 'Macul', 'Maipú', 'Ñuñoa', 'Pedro Aguirre Cerda', 'Peñalolén', 'Providencia', 'Pudahuel', 'Quilicura', 'Quinta Normal', 'Recoleta', 'Renca', 'San Joaquín', 'San Miguel', 'San Ramón', 'Vitacura', 'Puente Alto', 'Pirque', 'San José de Maipo', 'Colina', 'Lampa', 'Tiltil', 'San Bernardo', 'Buin', 'Calera de Tango', 'Paine', 'Melipilla', 'Alhué', 'Curacaví', 'María Pinto', 'San Pedro', 'Talagante', 'El Monte', 'Isla de Maipo', 'Padre Hurtado', 'Peñaflor'],
        'Región del Libertador General Bernardo O\'Higgins': ['Rancagua', 'Codegua', 'Coinco', 'Coltauco', 'Doñihue', 'Graneros', 'Las Cabras', 'Machalí', 'Malloa', 'Mostazal', 'Olivar', 'Peumo', 'Pichidegua', 'Quinta de Tilcoco', 'Rengo', 'Requínoa', 'San Vicente', 'Pichilemu', 'La Estrella', 'Litueche', 'Marchihue', 'Navidad', 'Paredones', 'San Fernando', 'Chépica', 'Chimbarongo', 'Lolol', 'Nancagua', 'Palmilla', 'Peralillo', 'Placilla', 'Pumanque', 'Santa Cruz'],
        'Región del Maule': ['Talca', 'ConsConsideración', 'Curepto', 'Empedrado', 'Maule', 'Pelarco', 'Pencahue', 'Río Claro', 'San Clemente', 'San Rafael', 'Cauquenes', 'Chanco', 'Pelluhue', 'Curicó', 'Hualañé', 'Licantén', 'Molina', 'Rauco', 'Romeral', 'Sagrada Familia', 'Teno', 'Vichuquén', 'Linares', 'Colbún', 'Longaví', 'Parral', 'Retiro', 'San Javier', 'Villa Alegre', 'Yerbas Buenas'],
        'Región de Ñuble': ['Chillán', 'Bulnes', 'Cobquecura', 'Coelemu', 'Coihueco', 'Chillán Viejo', 'El Carmen', 'Ninhue', 'Ñiquén', 'Pemuco', 'Pinto', 'Portezuelo', 'Quillón', 'Quirihue', 'Ránquil', 'San Carlos', 'San Fabián', 'San Ignacio', 'San Nicolás', 'Treguaco', 'Yungay'],
        'Región del Biobío': ['Concepción', 'Coronel', 'Chiguayante', 'Florida', 'Hualqui', 'Lota', 'Penco', 'San Pedro de la Paz', 'Santa Juana', 'Talcahuano', 'Tomé', 'Hualpén', 'Lebu', 'Arauco', 'Cañete', 'Contulmo', 'Curanilahue', 'Los Álamos', 'Tirúa', 'Los Ángeles', 'Antuco', 'Cabrero', 'Laja', 'Mulchén', 'Nacimiento', 'Negrete', 'Quilaco', 'Quilleco', 'San Rosendo', 'Santa Bárbara', 'Tucapel', 'Yumbel', 'Alto Biobío'],
        'Región de La Araucanía': ['Temuco', 'Carahue', 'Cunco', 'Curarrehue', 'Freire', 'Galvarino', 'Gorbea', 'Lautaro', 'Loncoche', 'Melipeuco', 'Nueva Imperial', 'Padre Las Casas', 'Perquenco', 'Pitrufquén', 'Pucón', 'Saavedra', 'Teodoro Schmidt', 'Toltén', 'Vilcún', 'Villarrica', 'Cholchol', 'Angol', 'Collipulli', 'Curacautín', 'Ercilla', 'Lonquimay', 'Los Sauces', 'Lumaco', 'Purén', 'Renaico', 'Traiguén', 'Victoria'],
        'Región de Los Ríos': ['Valdivia', 'Corral', 'Lanco', 'Los Lagos', 'Máfil', 'Mariquina', 'Paillaco', 'Panguipulli', 'La Unión', 'Futrono', 'Lago Ranco', 'Río Bueno'],
        'Región de Los Lagos': ['Puerto Montt', 'Calbuco', 'Cochamó', 'Fresia', 'Frutillar', 'Los Muermos', 'Llanquihue', 'Maullín', 'Puerto Varas', 'Castro', 'Ancud', 'Chonchi', 'Curaco de Vélez', 'Dalcahue', 'Puqueldón', 'Queilén', 'Quellón', 'Quemchi', 'Quinchao', 'Osorno', 'Puerto Octay', 'Purranque', 'Puyehue', 'Río Negro', 'San Juan de la Costa', 'San Pablo', 'Chaitén', 'Futaleufú', 'Hualaihué', 'Palena'],
        'Región de Aysén del General Carlos Ibáñez del Campo': ['Coyhaique', 'Lago Verde', 'Aysén', 'Cisnes', 'Guaitecas', 'Cochrane', 'O\'Higgins', 'Tortel', 'Chile Chico', 'Río Ibáñez'],
        'Región de Magallanes y de la Antártica Chilena': ['Punta Arenas', 'Laguna Blanca', 'Río Verde', 'San Gregorio', 'Cabo de Hornos', 'Antártica', 'Porvenir', 'Primavera', 'Timaukel', 'Natales', 'Torres del Paine'],
    }
    
    comunas = {}
    for region_nombre, comunas_lista in comunas_data.items():
        region = regiones[region_nombre]
        for comuna_nombre in comunas_lista:
            c = Comuna.objects.create(nombre=comuna_nombre, region=region)
            comunas[comuna_nombre] = c
    
    # 5. EMPRESAS
    print("Creando Empresas...")
    region_antofagasta = regiones['Región de Antofagasta']
    comuna_antofagasta = comunas['Antofagasta']
    
    empresa_gruas = Empresa.objects.create(
        rut='76543210',
        dv='K',
        razonSocial='GRÚAS BYC LIMITADA',
        nomFantasia='Grúas ByC',
        giro='SERVICIOS DE GRÚAS Y MAQUINARIA PESADA',
        direccion='AV. INDUSTRIAL 1234, ANTOFAGASTA',
        telefono='552345678',
        email='contacto@gruasbyc.cl',
        region=region_antofagasta,
        comuna=comuna_antofagasta
    )
    
    empresa_transportes = Empresa.objects.create(
        rut='76543211',
        dv='9',
        razonSocial='BYC TRANSPORTES LIMITADA',
        nomFantasia='ByC Transportes',
        giro='TRANSPORTE DE CARGA Y PASAJEROS',
        direccion='AV. GRECIA 5678, ANTOFAGASTA',
        telefono='552345679',
        email='contacto@byctransportes.cl',
        region=region_antofagasta,
        comuna=comuna_antofagasta
    )
    
    # 6. DEPARTAMENTOS
    print("Creando Departamentos...")
    depto_maquinarias = DeptoEmpresa.objects.create(depto='MAQUINARIAS')
    depto_operaciones = DeptoEmpresa.objects.create(depto='OPERACIONES')
    
    # 7. CARGOS
    print("Creando Cargos...")
    # Cargos para Maquinarias
    cargos_maquinarias = [
        'MECÁNICO',
        'RIGGER',
        'MAESTRO MECÁNICO',
        'TÉCNICO EN MANTENCIÓN',
        'SUPERVISOR DE MAQUINARIAS',
        'LUBRICADOR',
        'SOLDADOR',
        'ELECTRICISTA DE MAQUINARIA',
        'AYUDANTE DE MECÁNICO',
    ]
    
    cargos_maq = []
    for cargo_nombre in cargos_maquinarias:
        c = Cargo.objects.create(depto_id=depto_maquinarias, cargo=cargo_nombre)
        cargos_maq.append(c)
    
    # Cargos para Operaciones
    cargos_operaciones = [
        'OPERADOR GRÚA',
        'OPERADOR MANLIFT',
        'OPERADOR CAMIÓN',
        'OPERADOR RETROEXCAVADORA',
        'OPERADOR CARGADOR FRONTAL',
        'OPERADOR EXCAVADORA',
        'OPERADOR BULLDOZER',
        'SUPERVISOR DE OPERACIONES',
        'COORDINADOR DE FAENA',
        'PREVENCIONISTA DE RIESGOS',
        'CAPATAZ',
    ]
    
    cargos_ope = []
    for cargo_nombre in cargos_operaciones:
        c = Cargo.objects.create(depto_id=depto_operaciones, cargo=cargo_nombre)
        cargos_ope.append(c)
    
    # 8. TIPOS ADICIONALES (para documentación)
    print("Creando Tipos de Ausentismo...")
    tipos_ausentismo = ['LICENCIA MÉDICA', 'VACACIONES', 'PERMISO ADMINISTRATIVO', 'PERMISO SIN GOCE DE SUELDO', 'CAPACITACIÓN']
    for tipo in tipos_ausentismo:
        TipoAusentismo.objects.create(tipo=tipo)
    
    print("Creando Tipos de Examen...")
    tipos_examen = ['EXAMEN PREOCUPACIONAL', 'EXAMEN OCUPACIONAL', 'EXAMEN DE EGRESO', 'EXAMEN DE ALTURA', 'EXAMEN PSICOSENSOTÉCNICO', 'EXAMEN DE ALCOHOL Y DROGAS']
    for tipo in tipos_examen:
        TipoExamen.objects.create(tipoExamen=tipo)
    
    print("Creando Resultados de Examen...")
    resultados = ['APTO', 'APTO CON RESTRICCIONES', 'NO APTO', 'PENDIENTE']
    for resultado in resultados:
        ResultadoExamen.objects.create(resultado=resultado)
    
    print("Creando Tipos de Certificación...")
    tipos_certificacion = [
        'CERTIFICACIÓN DE GRÚA HORQUILLA',
        'CERTIFICACIÓN DE GRÚA TORRE',
        'CERTIFICACIÓN DE TRABAJO EN ALTURA',
        'CERTIFICACIÓN DE ESPACIOS CONFINADOS',
        'CERTIFICACIÓN DE PRIMEROS AUXILIOS',
        'CERTIFICACIÓN DE MANEJO DEFENSIVO',
        'CERTIFICACIÓN DE IZAJE DE CARGAS',
        'CERTIFICACIÓN OPERADOR DE EQUIPOS MÓVILES',
    ]
    for tipo in tipos_certificacion:
        TipoCertificacion.objects.create(tipoCertificacion=tipo)
    
    print("Creando Tipos de Licencia de Conducir...")
    tipos_licencia = ['CLASE A', 'CLASE B', 'CLASE C', 'CLASE D', 'CLASE E', 'CLASE F']
    for tipo in tipos_licencia:
        TipoLicencia.objects.create(tipoLicencia=tipo)
    
    print("Creando Tipos de Licencia Médica...")
    tipos_lic_medica = ['ENFERMEDAD COMÚN', 'ACCIDENTE LABORAL', 'ENFERMEDAD PROFESIONAL', 'LICENCIA MATERNAL', 'LICENCIA PATERNAL']
    for tipo in tipos_lic_medica:
        TipoLicenciaMedica.objects.create(tipoLicenciaMedica=tipo)
    
    print("Creando Tipos de Licencia Interna...")
    tipos_lic_interna = [
        ('LIC-A', 'Licencia Interna Clase A - Equipos Livianos'),
        ('LIC-B', 'Licencia Interna Clase B - Equipos Medianos'),
        ('LIC-C', 'Licencia Interna Clase C - Equipos Pesados'),
        ('LIC-D', 'Licencia Interna Clase D - Grúas Torre'),
        ('LIC-E', 'Licencia Interna Clase E - Grúas Móviles'),
    ]
    for tipo, desc in tipos_lic_interna:
        TipoLicenciaInterna.objects.create(tipoLicenciaInterna=tipo, descripcion=desc)
    
    # 9. CREAR 300 TRABAJADORES
    print("Creando 300 trabajadores...")
    
    nombres_hombres = [
        'JUAN', 'PEDRO', 'CARLOS', 'LUIS', 'JORGE', 'MANUEL', 'RICARDO', 'FERNANDO', 'MIGUEL', 'ANDRÉS',
        'ROBERTO', 'FRANCISCO', 'JOSÉ', 'DIEGO', 'RAÚL', 'SERGIO', 'EDUARDO', 'PABLO', 'HÉCTOR', 'DANIEL',
        'ALEJANDRO', 'ANTONIO', 'JAVIER', 'CRISTIAN', 'MARCELO', 'RODRIGO', 'GABRIEL', 'FELIPE', 'CLAUDIO', 'OSCAR'
    ]
    
    nombres_mujeres = [
        'MARÍA', 'PATRICIA', 'CARMEN', 'ANA', 'ROSA', 'ELENA', 'GLORIA', 'ISABEL', 'CLAUDIA', 'PAULA',
        'ANDREA', 'LORENA', 'CAROLINA', 'MÓNICA', 'DANIELA', 'ALEJANDRA', 'FRANCISCA', 'MARCELA', 'VERÓNICA', 'PAMELA'
    ]
    
    apellidos = [
        'GONZÁLEZ', 'MUÑOZ', 'ROJAS', 'DÍAZ', 'PÉREZ', 'SOTO', 'CONTRERAS', 'SILVA', 'MARTÍNEZ', 'SEPÚLVEDA',
        'MORALES', 'RODRÍGUEZ', 'LÓPEZ', 'FUENTES', 'HERNÁNDEZ', 'TORRES', 'ARAYA', 'FLORES', 'ESPINOZA', 'VALENZUELA',
        'CASTILLO', 'NÚÑEZ', 'ALONSO', 'RAMÍREZ', 'REYES', 'GUTIÉRREZ', 'CASTRO', 'VARGAS', 'NAVARRO', 'VEGA',
        'CORTÉS', 'CARRASCO', 'IBÁÑEZ', 'BRAVO', 'MÉNDEZ', 'PARRA', 'MEDINA', 'RÍOS', 'JARA', 'MORA'
    ]
    
    todas_comunas = list(comunas.values())
    todos_cargos = cargos_maq + cargos_ope
    empresas = [empresa_gruas, empresa_transportes]
    
    ruts_usados = set()
    
    for i in range(300):
        # Generar RUT único
        while True:
            rut, dv = generar_rut_chileno()
            if rut not in ruts_usados:
                ruts_usados.add(rut)
                break
        
        # Determinar sexo (70% hombres, 30% mujeres para este tipo de industria)
        if random.random() < 0.7:
            sexo = sexos['MASCULINO']
            nombre = random.choice(nombres_hombres)
        else:
            sexo = sexos['FEMENINO']
            nombre = random.choice(nombres_mujeres)
        
        apepat = random.choice(apellidos)
        apemat = random.choice(apellidos)
        
        # Estado civil aleatorio
        estado_civil = random.choice(list(estados_civiles.values()))
        
        # Comuna aleatoria
        comuna = random.choice(todas_comunas)
        region = comuna.region
        
        # Fecha de nacimiento (entre 20 y 60 años)
        edad = random.randint(20, 60)
        fecha_nac = datetime.now() - timedelta(days=edad*365)
        
        # Crear correo único
        correo = f"{nombre.lower()}.{apepat.lower()}{i}@byc.cl"
        
        # Crear dirección
        direccion = f"CALLE {random.randint(1, 30)} #{random.randint(100, 9999)}, {comuna.nombre.upper()}"
        
        # Crear personal
        personal = Personal.objects.create(
            rut=rut,
            dvrut=dv,
            nombre=nombre,
            apepat=apepat,
            apemat=apemat,
            sexo_id=sexo,
            estcivil_id=estado_civil,
            fechanac=fecha_nac,
            correo=correo,
            direccion=direccion,
            region_id=region,
            comuna_id=comuna,
            activo=True
        )
        
        # Asignar cargo y crear info laboral
        cargo = random.choice(todos_cargos)
        depto = cargo.depto_id
        empresa = random.choice(empresas)
        
        # Fecha de contratación (último año)
        fecha_contrata = datetime.now() - timedelta(days=random.randint(30, 730))
        
        InfoLaboral.objects.create(
            personal_id=personal,
            empresa_id=empresa,
            depto_id=depto,
            cargo_id=cargo,
            fechacontrata=fecha_contrata.date()
        )
        
        if (i + 1) % 50 == 0:
            print(f"  Creados {i + 1} trabajadores...")
    
    print("✓ Datos iniciales creados exitosamente!")
    print(f"  - {len(regiones_data)} regiones")
    print(f"  - {sum(len(c) for c in comunas_data.values())} comunas")
    print(f"  - 2 empresas")
    print(f"  - 2 departamentos")
    print(f"  - {len(cargos_maquinarias) + len(cargos_operaciones)} cargos")
    print(f"  - 300 trabajadores")


def eliminar_datos(apps, schema_editor):
    # Si necesitas hacer rollback de la migración
    Personal = apps.get_model('rrhh_personal', 'Personal')
    InfoLaboral = apps.get_model('rrhh_personal', 'InfoLaboral')
    Cargo = apps.get_model('rrhh_personal', 'Cargo')
    DeptoEmpresa = apps.get_model('rrhh_personal', 'DeptoEmpresa')
    Empresa = apps.get_model('gen_settings', 'Empresa')
    Comuna = apps.get_model('gen_settings', 'Comuna')
    Region = apps.get_model('gen_settings', 'Region')
    Sexo = apps.get_model('rrhh_personal', 'Sexo')
    EstadoCivil = apps.get_model('rrhh_personal', 'EstadoCivil')
    
    InfoLaboral.objects.all().delete()
    Personal.objects.all().delete()
    Cargo.objects.all().delete()
    DeptoEmpresa.objects.all().delete()
    Empresa.objects.all().delete()
    Comuna.objects.all().delete()
    Region.objects.all().delete()
    Sexo.objects.all().delete()
    EstadoCivil.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rrhh_personal', '0016_insertar_100_trabajadores_ficticios'),
        ('gen_settings', '0006_alter_empresa_options'),
    ]

    operations = [
        migrations.RunPython(crear_datos_iniciales, eliminar_datos),
    ]

