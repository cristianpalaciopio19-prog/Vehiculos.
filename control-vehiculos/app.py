import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash

from ocr_engine import procesar_pdf, RUTAS_OPERATIVAS, RUTAS_ADMINISTRATIVAS, MUNICIPIOS, factor_facturacion
import excel_store as store

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = 'set-colombina-control-vehiculos'
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

RUTAS_TODAS = sorted(RUTAS_OPERATIVAS) + sorted(RUTAS_ADMINISTRATIVAS)

PENDIENTES = {}


@app.route('/')
def inicio():
    resumen = store.resumen()
    viajes_recientes = store.listar_viajes()[:5]
    return render_template('inicio.html', resumen=resumen, viajes=viajes_recientes)


@app.route('/planillas')
def planillas():
    return render_template('planillas.html')


@app.route('/planillas/subir', methods=['POST'])
def subir_planilla():
    archivo = request.files.get('pdf')
    if not archivo or archivo.filename == '':
        flash('Selecciona un archivo PDF', 'error')
        return redirect(url_for('planillas'))
    if not archivo.filename.lower().endswith('.pdf'):
        flash('El archivo debe ser PDF', 'error')
        return redirect(url_for('planillas'))

    token = uuid.uuid4().hex[:10]
    ruta_pdf = os.path.join(UPLOAD_DIR, f'{token}.pdf')
    archivo.save(ruta_pdf)

    try:
        viajes_detectados = procesar_pdf(ruta_pdf)
    except MemoryError:
        flash('El PDF es muy grande para procesarlo en este servidor gratuito. Intenta con un PDF de menos páginas o más liviano.', 'error')
        return redirect(url_for('planillas'))
    except Exception as e:
        flash(f'Error procesando el PDF: {e}', 'error')
        return redirect(url_for('planillas'))

    PENDIENTES[token] = {
        'nombre_archivo': archivo.filename,
        'viajes': viajes_detectados,
    }
    return redirect(url_for('revisar_planilla', token=token))


@app.route('/planillas/revisar/<token>')
def revisar_planilla(token):
    datos = PENDIENTES.get(token)
    if not datos:
        flash('Esa planilla ya no está disponible, vuelve a subirla', 'error')
        return redirect(url_for('planillas'))
    return render_template(
        'revisar.html',
        token=token,
        nombre_archivo=datos['nombre_archivo'],
        viajes=datos['viajes'],
        rutas=RUTAS_TODAS,
        municipios=MUNICIPIOS,
    )


@app.route('/planillas/confirmar/<token>', methods=['POST'])
def confirmar_planilla(token):
    datos = PENDIENTES.get(token)
    if not datos:
        flash('Esa planilla ya no está disponible', 'error')
        return redirect(url_for('planillas'))

    indices = request.form.getlist('incluir')
    guardados = 0
    for idx in indices:
        i = int(idx)
        placa = request.form.get(f'placa_{i}', '').strip().upper()
        ruta = request.form.get(f'ruta_{i}', '').strip()
        municipio = request.form.get(f'municipio_{i}', '').strip()
        fecha = request.form.get(f'fecha_{i}', '').strip()
        km_raw = request.form.get(f'km_{i}', '').strip()
        if not placa or not km_raw:
            continue
        try:
            km = float(km_raw)
        except ValueError:
            continue
        factor = factor_facturacion(ruta)
        store.agregar_viaje(
            placa=placa, ruta=ruta, municipio=municipio, fecha_viaje=fecha,
            turno='', conductor='', km=km, factor=factor,
            origen=f"PDF:{datos['nombre_archivo']}", confianza='revisado'
        )
        guardados += 1

    del PENDIENTES[token]
    flash(f'{guardados} viaje(s) guardado(s) en el Excel', 'success')
    return redirect(url_for('lista_viajes'))


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        placa = request.form.get('placa', '').strip().upper()
        ruta = request.form.get('ruta', '').strip()
        municipio = request.form.get('municipio', '').strip()
        fecha = request.form.get('fecha', '').strip()
        turno = request.form.get('turno', '').strip()
        conductor = request.form.get('conductor', '').strip()
        km_raw = request.form.get('km', '').strip()

        if not placa or not km_raw:
            flash('Placa y kilómetros son obligatorios', 'error')
            return redirect(url_for('registro'))
        try:
            km = float(km_raw)
        except ValueError:
            flash('Kilómetros debe ser un número', 'error')
            return redirect(url_for('registro'))

        factor = factor_facturacion(ruta)
        store.agregar_viaje(
            placa=placa, ruta=ruta, municipio=municipio, fecha_viaje=fecha,
            turno=turno, conductor=conductor, km=km, factor=factor,
            origen='manual', confianza=''
        )
        flash('Viaje guardado', 'success')
        return redirect(url_for('lista_viajes'))

    return render_template('registro.html', rutas=RUTAS_TODAS, municipios=MUNICIPIOS)


@app.route('/viajes')
def lista_viajes():
    filtro_placa = request.args.get('placa', '').strip()
    filtro_municipio = request.args.get('municipio', '').strip()
    viajes = store.listar_viajes(filtro_placa or None, filtro_municipio or None)
    return render_template('lista.html', viajes=viajes, municipios=MUNICIPIOS,
                            filtro_placa=filtro_placa, filtro_municipio=filtro_municipio)


@app.route('/viajes/<placa>')
def detalle_vehiculo(placa):
    viajes = store.detalle_placa(placa)
    total_km = sum(v['km'] or 0 for v in viajes)
    return render_template('detalle.html', placa=placa, viajes=viajes, total_km=round(total_km, 1))


@app.route('/viajes/eliminar/<int:viaje_id>', methods=['POST'])
def eliminar_viaje(viaje_id):
    store.eliminar_viaje(viaje_id)
    flash('Viaje eliminado', 'success')
    return redirect(request.referrer or url_for('lista_viajes'))


@app.route('/descargar-excel')
def descargar_excel():
    store.inicializar_excel()
    return send_file(store.EXCEL_PATH, as_attachment=True, download_name='viajes_control_vehiculos.xlsx')


if __name__ == '__main__':
    store.inicializar_excel()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
