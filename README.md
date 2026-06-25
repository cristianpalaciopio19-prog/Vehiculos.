# Control de Vehículos — SET Colombina

App web real para registrar y consultar viajes de la flota. Todo se guarda en un archivo Excel (`data/viajes.xlsx`) que se actualiza automáticamente — no hay base de datos oculta, puedes abrir ese archivo en cualquier momento.

## Qué hace esta versión

- **Registrar viaje** → formulario con autocompletado: al escribir la placa, se rellenan solos el conductor habitual, la ruta, el municipio y los kilómetros oficiales (usando los datos reales de tu flota de 36 vehículos).
- **Campos del registro:** placa, número interno, ruta, municipio, fecha, turno, semana operativa, conductor, kilómetros, si lleva/trae personal, y quién diligencia el registro.
- **Lista y detalle por placa** → consulta todos los viajes guardados, filtra por placa o municipio, ve el historial de un vehículo específico.
- **Descargar Excel** → en cualquier momento puedes descargar `viajes.xlsx` con todo lo registrado.

Los datos de autocompletado (vehículo, conductor, ruta habitual, número interno, kilómetros por ruta) vienen de tu programación fija real de 36 vehículos y la tabla oficial de kilometraje — están en `datos_maestros.py` y puedes editarlos ahí directamente si cambia algún dato (nuevo conductor, vehículo, etc.).

## Publicarla en internet (sin instalar nada en tu PC)

Esta app incluye un `Dockerfile` listo para desplegarse gratis en [Render](https://render.com).

1. Crea una cuenta gratis en https://render.com.
2. Sube esta carpeta a un repositorio de GitHub.
3. En Render: **New + → Web Service** → conecta tu repositorio.
4. En **Root Directory** escribe el nombre de la carpeta (ej. `control-vehiculos`).
5. En **Language** selecciona **Docker**.
6. En el plan, elige **Free**.
7. Dale a **Create Web Service** y espera unos minutos.
8. Te dará una URL pública — esa es tu app.

**Importante sobre el plan gratis de Render:** el servidor se "duerme" tras inactividad y al despertar puede perder los datos guardados, porque el almacenamiento no es permanente en el plan free. Por eso la app tiene un botón de **"Descargar respaldo ahora"** en la pantalla de inicio — úsalo seguido para no perder tu trabajo.

## Instalación local (alternativa)

Necesitas Python 3.10+.

```
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000` en tu navegador. Para detenerla, `Ctrl+C` en la terminal.

## Dónde quedan los datos

Todo se guarda en `data/viajes.xlsx`, dentro de la misma carpeta del proyecto. Puedes abrir ese archivo directamente con Excel en cualquier momento.

## Actualizar los datos de vehículos/conductores

Si cambia un conductor, se agrega un vehículo nuevo, o cambia el kilometraje de una ruta, edita directamente el archivo `datos_maestros.py` — ahí está el diccionario `VEHICULOS` (placa → conductor, ruta, número interno, municipio) y `KM_POR_RUTA` (ruta → kilómetros oficiales). Después de editar, sube el archivo actualizado a GitHub y Render lo desplegará automáticamente.

## Estructura del proyecto

```
control-vehiculos/
├── app.py                # Rutas y lógica web (Flask)
├── datos_maestros.py       # Vehículos, conductores, rutas y km de referencia
├── excel_store.py           # Lectura/escritura del Excel
├── templates/                # Pantallas HTML
└── data/viajes.xlsx           # Tus datos (se crea automáticamente)
```
