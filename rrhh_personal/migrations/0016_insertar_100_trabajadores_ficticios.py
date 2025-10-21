# Generated manually to populate test data with 100 workers

from django.db import migrations
import random
from datetime import datetime, timedelta


def calcular_dv(rut):
    """Calcular dígito verificador de RUT chileno"""
    reversed_digits = map(int, reversed(str(rut)))
    factors = [2, 3, 4, 5, 6, 7]
    s = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
    dv = 11 - (s % 11)
    if dv == 11:
        return '0'
    elif dv == 10:
        return 'K'
    else:
        return str(dv)


def crear_personal_ficticio(apps, schema_editor):
    """Crear 100 trabajadores ficticios para el área de maquinarias y operaciones"""
    
    Personal = apps.get_model('rrhh_personal', 'Personal')
    InfoLaboral = apps.get_model('rrhh_personal', 'InfoLaboral')
    Sexo = apps.get_model('rrhh_personal', 'Sexo')
    EstadoCivil = apps.get_model('rrhh_personal', 'EstadoCivil')
    Region = apps.get_model('gen_settings', 'Region')
    Comuna = apps.get_model('gen_settings', 'Comuna')
    Empresa = apps.get_model('gen_settings', 'Empresa')
    DeptoEmpresa = apps.get_model('rrhh_personal', 'DeptoEmpresa')
    Cargo = apps.get_model('rrhh_personal', 'Cargo')
    
    # Nombres chilenos comunes
    nombres_masculinos = [
        'JUAN', 'PEDRO', 'CARLOS', 'LUIS', 'JOSE', 'FRANCISCO', 'MIGUEL', 'JORGE', 'RICARDO', 'ROBERTO',
        'DIEGO', 'JAVIER', 'SERGIO', 'MANUEL', 'MARIO', 'FERNANDO', 'ANDRES', 'PABLO', 'EDUARDO', 'DAVID',
        'CRISTIAN', 'GONZALO', 'FELIPE', 'RODRIGO', 'ANTONIO', 'RAUL', 'ALEX', 'PATRICIO', 'MARCELO', 'OSCAR',
        'MAURICIO', 'HUGO', 'HECTOR', 'GABRIEL', 'DANIEL', 'MARCO', 'NELSON', 'IVAN', 'RAMON', 'VICTOR',
        'CLAUDIO', 'LEONARDO', 'RENATO', 'ARTURO', 'GUILLERMO', 'IGNACIO', 'SEBASTIAN', 'MATIAS', 'BENJAMIN'
    ]
    
    nombres_femeninos = [
        'MARIA', 'CARMEN', 'ANA', 'ROSA', 'PATRICIA', 'GLORIA', 'CLAUDIA', 'VERONICA', 'SANDRA', 'MONICA',
        'ALEJANDRA', 'CAROLINA', 'ANDREA', 'PAULA', 'DANIELA', 'LORENA', 'CECILIA', 'ELIZABETH', 'JESSICA',
        'GABRIELA', 'KARINA', 'PAOLA', 'SOLEDAD', 'XIMENA', 'VALENTINA', 'CAMILA', 'JAVIERA', 'FRANCISCA'
    ]
    
    apellidos = [
        'GONZALEZ', 'RODRIGUEZ', 'MUÑOZ', 'ROJAS', 'DIAZ', 'PEREZ', 'SOTO', 'CONTRERAS', 'SILVA', 'MARTINEZ',
        'SEPULVEDA', 'MORALES', 'GARCIA', 'LOPEZ', 'FERNANDEZ', 'TORRES', 'ARAYA', 'FLORES', 'ESPINOZA', 'VALENZUELA',
        'REYES', 'PINO', 'CASTRO', 'ALARCON', 'CARRASCO', 'GUTIERREZ', 'HERRERA', 'MEDINA', 'NUNEZ', 'RAMIREZ',
        'VASQUEZ', 'RUIZ', 'HERNANDEZ', 'MOLINA', 'VERGARA', 'ORTIZ', 'SANCHEZ', 'JIMENEZ', 'NAVARRO', 'LEON',
        'VARGAS', 'ROMERO', 'CASTILLO', 'VEGA', 'AGUIRRE', 'BRAVO', 'GUERRERO', 'PARRA', 'SALAZAR', 'VERA',
        'CAMPOS', 'CORTES', 'RIOS', 'BUSTOS', 'FUENTES', 'CACERES', 'SANDOVAL', 'MENDEZ', 'SANTANA', 'LAGOS'
    ]
    
    # Obtener datos necesarios
    sexo_masculino = Sexo.objects.get(sexo_id=5)  # MASCULINO
    sexo_femenino = Sexo.objects.get(sexo_id=4)   # FEMENINO
    
    estados_civiles = list(EstadoCivil.objects.all())
    regiones = list(Region.objects.all()[:5])  # Primeras 5 regiones
    empresas = list(Empresa.objects.all())
    
    # Departamentos y cargos
    depto_operaciones = DeptoEmpresa.objects.get(depto_id=2)
    depto_maquinarias = DeptoEmpresa.objects.get(depto_id=1)
    
    cargos = list(Cargo.objects.all())
    
    # Generar 100 trabajadores
    trabajadores_creados = 0
    ruts_usados = set()
    
    # Obtener RUTs ya existentes
    ruts_existentes = set(Personal.objects.values_list('rut', flat=True))
    
    for i in range(100):
        # Generar RUT único
        rut_base = None
        while True:
            rut_base = random.randint(15000000, 25000000)
            if str(rut_base) not in ruts_usados and str(rut_base) not in ruts_existentes:
                ruts_usados.add(str(rut_base))
                break
        
        dv = calcular_dv(rut_base)
        
        # Decidir sexo (80% masculino, 20% femenino para área industrial)
        es_masculino = random.random() < 0.8
        sexo = sexo_masculino if es_masculino else sexo_femenino
        
        # Elegir nombre según sexo
        if es_masculino:
            nombre = random.choice(nombres_masculinos)
        else:
            nombre = random.choice(nombres_femeninos)
        
        apellido_paterno = random.choice(apellidos)
        apellido_materno = random.choice(apellidos)
        
        # Generar fecha de nacimiento (entre 22 y 60 años)
        edad = random.randint(22, 60)
        fecha_nacimiento = datetime.now().date() - timedelta(days=edad * 365 + random.randint(0, 365))
        
        # Estado civil
        estado_civil = random.choice(estados_civiles)
        
        # Región y comuna
        region = random.choice(regiones)
        comunas_region = list(Comuna.objects.filter(region=region))
        comuna = random.choice(comunas_region) if comunas_region else None
        
        # Email
        email = f"{nombre.lower()}.{apellido_paterno.lower()}{rut_base}@email.com"
        
        # Dirección
        calles = ['AVENIDA LIBERTADOR', 'CALLE LOS AROMOS', 'PASAJE LAS ROSAS', 'AVENIDA CENTRAL', 'CALLE PRINCIPAL']
        direccion = f"{random.choice(calles)} {random.randint(100, 9999)}"
        
        # Crear personal
        try:
            personal = Personal.objects.create(
                rut=str(rut_base),
                dvrut=dv,
                nombre=nombre,
                apepat=apellido_paterno,
                apemat=apellido_materno,
                sexo_id=sexo,
                fechanac=fecha_nacimiento,
                estcivil_id=estado_civil,
                correo=email,
                region_id=region,
                comuna_id=comuna,
                direccion=direccion,
                activo=True
            )
            
            # Crear información laboral
            empresa = random.choice(empresas)
            cargo = random.choice(cargos)
            
            # Fecha de contrato (entre 6 meses y 5 años atrás)
            dias_antiguedad = random.randint(180, 1825)
            fecha_contrato = datetime.now().date() - timedelta(days=dias_antiguedad)
            
            InfoLaboral.objects.create(
                personal_id=personal,
                empresa_id=empresa,
                depto_id=cargo.depto_id,
                cargo_id=cargo,
                fechacontrata=fecha_contrato
            )
            
            trabajadores_creados += 1
            
        except Exception as e:
            print(f"Error creando trabajador {i+1}: {e}")
            continue
    
    print(f"\nSe crearon {trabajadores_creados} trabajadores ficticios exitosamente")


def eliminar_personal_ficticio(apps, schema_editor):
    """Eliminar los trabajadores ficticios creados (rollback)"""
    Personal = apps.get_model('rrhh_personal', 'Personal')
    
    # Eliminar personal con emails que contengan '@email.com'
    # (identificador de datos ficticios)
    personal_ficticio = Personal.objects.filter(correo__contains='@email.com')
    count = personal_ficticio.count()
    personal_ficticio.delete()
    
    print(f"Se eliminaron {count} trabajadores ficticios")


class Migration(migrations.Migration):

    dependencies = [
        ('rrhh_personal', '0015_cambiar_tipos_a_tipo_licencia_interna'),
        ('gen_settings', '0006_alter_empresa_options'),
    ]

    operations = [
        migrations.RunPython(
            crear_personal_ficticio,
            eliminar_personal_ficticio
        ),
    ]

