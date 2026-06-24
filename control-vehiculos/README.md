# Control de Vehículos — SET Colombina

App web real para registrar y consultar viajes de la flota, con lectura automática (OCR) de planillas escaneadas en PDF. Todo se guarda en un archivo Excel (`data/viajes.xlsx`) que se actualiza automáticamente — no hay base de datos oculta, puedes abrir ese archivo en cualquier momento.

## Qué hace esta versión (v1)

- **Cargar planilla PDF** → la app convierte cada página a imagen y usa Tesseract OCR para detectar placas, rutas y kilómetros.
- **Revisar antes de guardar** → como el OCR en letra manuscrita no es perfecto, cada viaje detectado se muestra en un formulario editable antes de guardarse. Las filas con baja confianza (posible confusión de placa, ruta no detectada) se marcan en rojo.
- **Registrar viaje manual** → para cuando no hay PDF o el OCR falla.
- **Lista y detalle por placa** → consulta todos los viajes guardados, filtra por placa o municipio, ve el historial de un vehículo específico.
- **Descargar Excel** → en cualquier momento puedes descargar `viajes.xlsx` con todo lo registrado.

Reglas de negocio ya incorporadas: rutas operativas (A1-A3, B1, R1-R3, T2-T9, Z2-Z9, Refuerzo Zarzal, Casa de la Cultura) aplican factor ×2; rutas administrativas (ADM Z/R/T, Mantenimiento) aplican ×1; placas TJV520/TJY520/ETM038 se consolidan bajo WHX094; alerta automática si se detecta la confusión OCR conocida GIL764↔GIL464 o SZU436↔SZU346.

## Instalación

Necesitas Python 3.10+ y **Tesseract OCR** instalado en el sistema (no solo la librería de Python).

### 1. Instalar Tesseract (motor de OCR)

**Windows:**
Descarga el instalador desde https://github.com/UB-Mannheim/tesseract/wiki y ejecútalo. Anota la ruta de instalación (normalmente `C:\Program Files\Tesseract-OCR\tesseract.exe`).

**Mac:**
```
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```
sudo apt install tesseract-ocr poppler-utils
```

> `poppler-utils` es necesario en Linux/Mac para convertir PDF a imagen. En Windows, `pdf2image` necesita los binarios de poppler — descárgalos de https://github.com/oschwartz10612/poppler-windows/releases y agrega la carpeta `bin` al PATH.

### 2. Instalar dependencias de Python

Desde la carpeta del proyecto:
```
pip install -r requirements.txt
```

### 3. (Solo Windows) indicar la ruta de Tesseract

Si Tesseract no quedó en el PATH, abre `ocr_engine.py` y agrega esta línea al inicio, con tu ruta real:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Cómo correrla

```
python app.py
```

Verás un mensaje como `Running on http://127.0.0.1:5000`. Abre esa dirección en tu navegador (Chrome, Edge, lo que uses normalmente).

Para detenerla, vuelve a la terminal y presiona `Ctrl+C`.

## Dónde quedan los datos

Todo se guarda en `data/viajes.xlsx`, dentro de la misma carpeta del proyecto. Puedes abrir ese archivo directamente con Excel en cualquier momento — no necesitas la app corriendo para verlo, solo para agregar/editar viajes.

Los PDF que subas se guardan temporalmente en `uploads/` solo durante el procesamiento.

## Limitaciones honestas de esta v1

- El OCR con Tesseract es gratuito pero **no es perfecto en letra manuscrita**. Por eso existe el paso de revisión antes de guardar — siempre verifica los datos detectados.
- Solo está instalado el idioma inglés de Tesseract por defecto. Si los nombres de conductores o municipios salen mal leídos, puedes instalar el paquete de idioma español de Tesseract (`tesseract-ocr-spa` en Linux) para mejorar esa parte — los datos numéricos (placas, kilómetros) no se ven afectados por el idioma.
- No incluye todavía el módulo de cotejo automático ni los KPI de costo por persona — eso queda para una v2.

## Estructura del proyecto

```
control-vehiculos/
├── app.py              # Rutas y lógica web (Flask)
├── ocr_engine.py        # Lectura de PDF + OCR + reglas de negocio
├── excel_store.py        # Lectura/escritura del Excel
├── templates/            # Pantallas HTML
├── data/viajes.xlsx       # Tus datos (se crea automáticamente)
└── uploads/               # PDFs temporales durante el procesamiento
```
