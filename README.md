# Encuesta de satisfacción del servicio de transporte – Colombina

App Flask con encuesta pública anónima y panel administrativo privado. Las respuestas se guardan de forma permanente en Supabase (PostgreSQL), en el proyecto independiente `encuesta-transporte`.

## Base de datos (ya creada)
Las tablas ya existen en Supabase, con las 7 preguntas y 23 rutas (A1–A3, B1, R1–R3, T2–T9, Z2–Z9) cargadas:

| Tabla | Contenido |
|---|---|
| `enc_rutas` | Rutas disponibles (editables desde el panel) |
| `enc_preguntas` | Preguntas de calificación 1–5 (editables desde el panel) |
| `enc_respuestas` | Una fila por encuesta: fecha, ruta, comentario |
| `enc_detalle` | Calificación de cada pregunta por encuesta |

Las tablas tienen RLS activado; solo el usuario de base de datos `encuesta_app` (exclusivo de esta app) puede leerlas o escribirlas.

## Despliegue en Render (desde el navegador)
1. Cree un repositorio nuevo en GitHub, por ejemplo `encuesta-transporte-colombina`, y suba **todo el contenido** de esta carpeta respetando las subcarpetas `templates/` y `static/`.
2. En Render: **New → Web Service**, conecte ese repositorio.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --workers 2 --timeout 60`
   - Plan: Free
3. En **Environment**, agregue estas variables:
   - `DATABASE_URL`: cadena de conexión del proyecto Supabase `encuesta-transporte` (usuario `encuesta_app`, Session pooler).
   - `ADMIN_PASSWORD`: la contraseña del panel.
   - `SECRET_KEY`: cualquier texto largo y aleatorio.
   - `PYTHON_VERSION`: `3.11.9`
4. Cuando termine el despliegue, abra `https://<su-servicio>.onrender.com/salud`. Si muestra `{"ok": true}`, la app quedó conectada a la base de datos.

## Rutas de la aplicación
| URL | Uso |
|---|---|
| `/` | Encuesta pública (enlace para los operarios) |
| `/admin` | Tablero con KPIs, gráficas y filtros por ruta y fecha |
| `/admin/respuestas` | Registro histórico de encuestas (permite eliminar respuestas) |
| `/admin/configuracion` | Editar, agregar, ordenar y desactivar preguntas y rutas |
| `/admin/qr` | Enlace público, botón de WhatsApp, descarga del QR y afiche imprimible |
| `/admin/exportar` | Excel con 4 hojas (respuestas, resumen, por ruta, recomendaciones), según los filtros aplicados |

**Google Sheets:** suba el Excel exportado a Google Drive y ábralo con Google Sheets.

## Notas
- El plan gratuito de Render "duerme" el servicio tras 15 minutos sin uso, así que la primera apertura puede tardar unos 30–50 segundos. Los datos no se pierden, porque están en Supabase.
- Supabase pausa los proyectos gratuitos tras 7 días sin actividad (se reactiva desde el panel de Supabase sin perder datos).
- Desactivar una pregunta o una ruta la oculta de la encuesta, pero conserva su historial. Al renombrar una ruta también se actualizan sus encuestas anteriores.
