import re
import os
from datetime import datetime
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageOps, ImageFilter

PLACA_RE = re.compile(r'\b([A-Z]{3}\s?-?\s?\d{3})\b')
RUTA_RE = re.compile(r'\b([ABRTZ]\d{1,2}|ADM\s?[ZRT]|REFUERZO\s?ZARZAL|CASA\s?DE\s?LA\s?CULTURA|MANTENIMIENTO)\b', re.IGNORECASE)
KM_RE = re.compile(r'\b(\d{1,3}[.,]\d{1,2})\b')
FECHA_RE = re.compile(r'\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b')

RUTAS_OPERATIVAS = {
    'A1', 'A2', 'A3', 'B1', 'R1', 'R2', 'R3',
    'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9',
    'Z2', 'Z3', 'Z4', 'Z5', 'Z6', 'Z7', 'Z8', 'Z9',
    'REFUERZO ZARZAL', 'CASA DE LA CULTURA'
}
RUTAS_ADMINISTRATIVAS = {'ADM Z', 'ADM R', 'ADM T', 'MANTENIMIENTO'}

PLACA_CANONICA = {
    'TJV520': 'WHX094', 'TJY520': 'WHX094', 'ETM038': 'WHX094',
}

CONFUSIONES_OCR = [
    ('GIL764', 'GIL464'), ('SZU436', 'SZU346'),
]

KM_REFERENCIA = {
    'B1': 19.0, 'A1': 22.6, 'A2': 22.6, 'A3': 22.6,
    'T2': 32.0, 'T3': 33.5, 'T4': 35.0, 'T5': 36.0,
    'T6': 37.0, 'T7': 38.0, 'T8': 39.0, 'T9': 40.0,
    'Z2': 9.8, 'Z3': 10.0, 'Z4': 10.2, 'Z5': 10.4,
    'Z6': 10.5, 'Z7': 10.6, 'Z8': 10.7, 'Z9': 10.8,
}

MUNICIPIOS = ['Tuluá', 'La Paila', 'Andalucía', 'Zarzal', 'Bugalagrande', 'Roldanillo']


def normalizar_placa(raw):
    p = re.sub(r'[\s\-]', '', raw.upper())
    if len(p) != 6:
        return p, False
    return p, True


def detectar_confusion(placa):
    for a, b in CONFUSIONES_OCR:
        if placa == a or placa == b:
            return [a, b]
    return None


def aplicar_canonica(placa):
    return PLACA_CANONICA.get(placa, placa)


def factor_facturacion(ruta):
    ruta_norm = ruta.strip().upper()
    if ruta_norm in RUTAS_ADMINISTRATIVAS or 'ADM' in ruta_norm or 'MANTENIMIENTO' in ruta_norm:
        return 1
    return 2


def preprocesar_imagen(img):
    img = img.convert('L')
    img = ImageOps.autocontrast(img, cutoff=1)
    w, h = img.size
    if w < 2000:
        scale = 2000 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=80, threshold=3))
    return img


def pdf_a_imagenes(pdf_path, dpi=200):
    return convert_from_path(pdf_path, dpi=dpi, thread_count=1)


def contar_paginas(pdf_path):
    from pdf2image.pdf2image import pdfinfo_from_path
    info = pdfinfo_from_path(pdf_path)
    return info.get('Pages', 1)


def ocr_pagina(img):
    img_proc = preprocesar_imagen(img)
    config = '--oem 3 --psm 6'
    texto = pytesseract.image_to_string(img_proc, lang='eng', config=config)
    del img_proc
    return texto


def extraer_viajes_de_texto(texto, pagina_num):
    lineas = [l.strip() for l in texto.split('\n') if l.strip()]
    viajes = []
    placa_actual = None
    ruta_actual = None
    fecha_actual = None

    for linea in lineas:
        m_placa = PLACA_RE.search(linea)
        m_ruta = RUTA_RE.search(linea)
        m_km = KM_RE.search(linea)
        m_fecha = FECHA_RE.search(linea)

        if m_placa:
            placa_norm, valida = normalizar_placa(m_placa.group(1))
            placa_actual = placa_norm

        if m_ruta:
            ruta_actual = m_ruta.group(1).upper().strip()

        if m_fecha:
            d, mo, y = m_fecha.groups()
            y = '20' + y if len(y) == 2 else y
            try:
                fecha_actual = f"{int(d):02d}/{int(mo):02d}/{y}"
            except ValueError:
                pass

        if m_km and placa_actual:
            km_val = float(m_km.group(1).replace(',', '.'))

            confusion = detectar_confusion(placa_actual)
            placa_final = aplicar_canonica(placa_actual)

            viajes.append({
                'placa_detectada': placa_actual,
                'placa_canonica': placa_final,
                'ruta': ruta_actual or '',
                'km': km_val,
                'fecha': fecha_actual,
                'pagina': pagina_num,
                'factor': factor_facturacion(ruta_actual or ''),
                'confusion_posible': confusion,
                'linea_origen': linea,
                'confianza': 'baja' if (confusion or not ruta_actual) else 'media',
            })

    return viajes


MAX_PAGINAS = 15


def procesar_pdf(pdf_path):
    total_paginas = contar_paginas(pdf_path)
    paginas_a_procesar = min(total_paginas, MAX_PAGINAS)
    todos_viajes = []

    for i in range(1, paginas_a_procesar + 1):
        imagenes = convert_from_path(pdf_path, dpi=200, first_page=i, last_page=i, thread_count=1)
        if not imagenes:
            continue
        img = imagenes[0]
        texto = ocr_pagina(img)
        viajes = extraer_viajes_de_texto(texto, i)
        todos_viajes.extend(viajes)
        del img
        del imagenes

    return todos_viajes
