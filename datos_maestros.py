# Datos maestros: vehículos fijos, conductores, rutas habituales y kilómetros oficiales.
# Fuente: Programación_fija.xlsx (hoja COLOMBINA FIJOS) y KILOMETRAJE_RUTAS.xlsx
from datetime import date

# placa -> {conductor, ruta_habitual, numero_interno, municipio}
VEHICULOS = {
    'GUZ038': {'conductor': 'GUSTAVO ADOLFO SANTA', 'ruta': 'T2', 'numero_interno': '444', 'municipio': 'Tuluá'},
    'VAK305': {'conductor': 'OSCAR LADINO ECHEVERRY', 'ruta': 'T3', 'numero_interno': '449', 'municipio': 'Tuluá'},
    'SIT809': {'conductor': 'CARLOS MURILLO OSPINA', 'ruta': 'T4', 'numero_interno': '432', 'municipio': 'Tuluá'},
    'ESZ696': {'conductor': 'DIDIER ORLANDO COY', 'ruta': 'T5', 'numero_interno': '439', 'municipio': 'Tuluá'},
    'ETL439': {'conductor': 'VICTOR ALFONSO ECHEVERRY', 'ruta': 'T6', 'numero_interno': '447', 'municipio': 'Tuluá'},
    'ESZ474': {'conductor': 'JHON PEDRO GONZALEZ', 'ruta': 'T7', 'numero_interno': '434', 'municipio': 'Tuluá'},
    'ESZ697': {'conductor': 'REYNALDO VASQUEZ', 'ruta': 'T8', 'numero_interno': '440', 'municipio': 'Tuluá'},
    'TJY479': {'conductor': 'KEVIN GONZALEZ TRIVIÑO', 'ruta': 'T9', 'numero_interno': '441', 'municipio': 'Tuluá'},
    'WHX092': {'conductor': 'JORGE DANIEL HERNANDEZ', 'ruta': 'A1', 'numero_interno': '427', 'municipio': 'Andalucía'},
    'ESZ548': {'conductor': 'FRANCISCO JAVIER MOLINA', 'ruta': 'A2', 'numero_interno': '438', 'municipio': 'Andalucía'},
    'WHX093': {'conductor': 'RAUL ANDRES VILLADA', 'ruta': 'A3', 'numero_interno': '428', 'municipio': 'Andalucía'},
    'WHX088': {'conductor': 'LEONARDO GALVIS TORRES', 'ruta': 'B1', 'numero_interno': '423', 'municipio': 'Bugalagrande'},
    'SZU346': {'conductor': 'ALVARO CARDONA', 'ruta': 'Z2', 'numero_interno': '8036', 'municipio': 'Zarzal'},
    'GIL764': {'conductor': 'ANDRES FELIPE VERGARA', 'ruta': 'Z4', 'numero_interno': '452', 'municipio': 'Zarzal'},
    'WHX089': {'conductor': 'JULIO CESAR TORRES', 'ruta': 'Z5', 'numero_interno': '424', 'municipio': 'Zarzal'},
    'ZDA565': {'conductor': 'ERICK FERNANDO BEDOYA', 'ruta': 'Z6', 'numero_interno': '3005', 'municipio': 'Zarzal'},
    'TTZ369': {'conductor': 'MIGUEL ANGUEL PIEDRAHITA', 'ruta': 'Z7', 'numero_interno': '98', 'municipio': 'Zarzal'},
    'STS028': {'conductor': 'DAINER MARIN', 'ruta': 'Z8', 'numero_interno': '428', 'municipio': 'Zarzal'},
    'ESZ549': {'conductor': 'LUIS FELIPE ARIAS', 'ruta': 'Z9', 'numero_interno': '437', 'municipio': 'Zarzal'},
    'WHX094': {'conductor': 'OSCAR CAMILO CORRECHA', 'ruta': 'CASA DE LA CULTURA', 'numero_interno': '430', 'municipio': 'Zarzal'},
    'TJY520': {'conductor': 'CARLOS ALFONSO VILLEGAS', 'ruta': 'CASA DE LA CULTURA', 'numero_interno': '451', 'municipio': 'Zarzal'},
    'WHX095': {'conductor': 'HAROLD GIRALDO LOAIZA', 'ruta': 'R1', 'numero_interno': '426', 'municipio': 'Roldanillo'},
    'SIT798': {'conductor': 'JHON JAMES CASTAÑO', 'ruta': 'R2', 'numero_interno': '431', 'municipio': 'Roldanillo'},
    'WMV587': {'conductor': 'ORBEIN SOTO BEDOYA', 'ruta': 'R3', 'numero_interno': '418', 'municipio': 'Roldanillo'},
    'JTS878': {'conductor': '', 'ruta': 'REFUERZO ZARZAL', 'numero_interno': '446', 'municipio': 'Zarzal'},
    'ZAP855': {'conductor': '', 'ruta': 'REFUERZO ZARZAL', 'numero_interno': '718', 'municipio': 'Zarzal'},
    'TFT782': {'conductor': '', 'ruta': 'REFUERZO ZARZAL', 'numero_interno': '', 'municipio': 'Zarzal'},
    'SIT838': {'conductor': '', 'ruta': 'REFUERZO ZARZAL', 'numero_interno': '442', 'municipio': 'Zarzal'},
    'ESZ695': {'conductor': '', 'ruta': 'APOYO ANDALUCIA', 'numero_interno': '436', 'municipio': 'Andalucía'},
    'WHX091': {'conductor': '', 'ruta': 'APOYO BUGALAGRANDE', 'numero_interno': '425', 'municipio': 'Bugalagrande'},
    'VAK302': {'conductor': '', 'ruta': 'APOYO TULUA', 'numero_interno': '450', 'municipio': 'Tuluá'},
    'ESZ473': {'conductor': '', 'ruta': 'APOYO TULUA', 'numero_interno': '433', 'municipio': 'Tuluá'},
    'JVM359': {'conductor': '', 'ruta': 'APOYO TULUA', 'numero_interno': '448', 'municipio': 'Tuluá'},
    'TJV520': {'conductor': 'CARLOS ALFONSO VILLEGAS', 'ruta': 'CASA DE LA CULTURA', 'numero_interno': '451', 'municipio': 'Zarzal'},
    'ETM038': {'conductor': 'CARLOS ALFONSO VILLEGAS', 'ruta': 'CASA DE LA CULTURA', 'numero_interno': '451', 'municipio': 'Zarzal'},
}

# ruta -> kilómetros oficiales (fuente: KILOMETRAJE_RUTAS.xlsx)
KM_POR_RUTA = {
    'B1': 19.0,
    'A1': 22.6, 'A2': 20.0, 'A3': 20.1,
    'T2': 34.7, 'T3': 34.3, 'T4': 32.0, 'T5': 32.6, 'T6': 33.3, 'T7': 40.0, 'T8': 32.7, 'T9': 33.1,
    'R1': 20.3, 'R2': 20.6, 'R3': 21.0,
    'Z2': 10.7, 'Z4': 10.7, 'Z5': 9.8, 'Z6': 10.4, 'Z7': 10.5, 'Z8': 10.8, 'Z9': 9.79,
}


def datos_por_placa(placa):
    """Devuelve los datos habituales conocidos para una placa, o vacíos si no existe."""
    placa = (placa or '').strip().upper()
    info = VEHICULOS.get(placa, {})
    ruta = info.get('ruta', '')
    return {
        'conductor': info.get('conductor', ''),
        'ruta': ruta,
        'numero_interno': info.get('numero_interno', ''),
        'municipio': info.get('municipio', ''),
        'km': KM_POR_RUTA.get(ruta.upper(), ''),
    }


def km_de_ruta(ruta):
    return KM_POR_RUTA.get((ruta or '').strip().upper(), '')


# Rutas administrativas (un solo sentido, solo "Ingreso"). Todo lo demás es operativo (Ingreso/Salida).
RUTAS_ADMINISTRATIVAS = {'CASA DE LA CULTURA', 'ADM Z', 'ADM R', 'ADM T'}

# Municipio de rutas administrativas sin vehículo fijo asignado (rotan según necesidad)
MUNICIPIO_ADM = {'ADM Z': 'Zarzal', 'ADM R': 'Roldanillo', 'ADM T': 'Tuluá'}


def es_ruta_administrativa(ruta):
    return (ruta or '').strip().upper() in RUTAS_ADMINISTRATIVAS


def datos_por_ruta(ruta):
    """Devuelve el vehículo típico (placa, conductor, número interno, municipio) y km de una ruta."""
    ruta_norm = (ruta or '').strip().upper()
    vehiculo_encontrado = None
    placa_encontrada = ''
    for placa, info in VEHICULOS.items():
        if info.get('ruta', '').strip().upper() == ruta_norm:
            vehiculo_encontrado = info
            placa_encontrada = placa
            break
    if not vehiculo_encontrado:
        vehiculo_encontrado = {}
    return {
        'placa': placa_encontrada,
        'conductor': vehiculo_encontrado.get('conductor', ''),
        'numero_interno': vehiculo_encontrado.get('numero_interno', ''),
        'municipio': vehiculo_encontrado.get('municipio', '') or MUNICIPIO_ADM.get(ruta_norm, ''),
        'km': KM_POR_RUTA.get(ruta_norm, ''),
        'es_administrativa': es_ruta_administrativa(ruta_norm),
    }


# Ancla del Calendario Oficial Colombina 2026: domingo 28 dic 2025 = inicio de la Semana 1
ANCLA_SEMANA_1 = date(2025, 12, 28)


def semana_operativa(fecha=None):
    """Calcula el número de semana operativa (Calendario Colombina 2026) para una fecha dada."""
    if fecha is None:
        fecha = date.today()
    dias = (fecha - ANCLA_SEMANA_1).days
    return (dias // 7) + 1
