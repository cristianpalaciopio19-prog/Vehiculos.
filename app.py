import os
import io
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash

import excel_store as store
from datos_maestros import (
    VEHICULOS, KM_POR_RUTA, datos_por_placa, semana_operativa,
    datos_por_ruta, es_ruta_administrativa, RUTAS_ADMINISTRATIVAS, ahora_colombia
)
from qr_generator import generar_qr_bytes

BASE_DIR = os.path.dirname(__file__)

app = Flask(__name__)
app.secret_key = 'set-colombina-control-vehiculos'

RUTAS_TODAS = sorted(KM_POR_RUTA.keys()) + ['CASA DE LA CULTURA', 'REFUERZO ZARZAL', 'ADM Z', 'ADM R', 'ADM T']
MUNICIPIOS = ['Tuluá', 'La Paila', 'Andalucía', 'Zarzal', 'Bugalagrande', 'Roldanillo']
PLACAS_CONOCIDAS = sorted(VEHICULOS.keys())


@app.route('/')
def inicio():
    resumen = store.resumen()
    viajes_recientes = store.listar_viajes()[:5]
    return render_template('inicio.html', resumen=resumen, viajes=viajes_recientes)


@app.route('/api/datos-placa/<placa>')
def api_datos_placa(placa):
    return jsonify(datos_por_placa(placa))


@app.route('/api/km-ruta/<ruta>')
def api_km_ruta(ruta):
    return jsonify({'km': KM_POR_RUTA.get(ruta.strip().upper(), '')})


@app.route('/api/diagnostico-hora')
def diagnostico_hora():
    import datetime as dt
    return jsonify({
        'hora_colombia_calculada': ahora_colombia().strftime('%d/%m/%Y %H:%M:%S'),
        'hora_servidor_sin_tz': dt.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    })


@app.route('/api/datos-ruta/<ruta>')
def api_datos_ruta(ruta):
    return jsonify(datos_por_ruta(ruta))


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        placa = request.form.get('placa', '').strip().upper()
        numero_interno = request.form.get('numero_interno', '').strip()
        ruta = request.form.get('ruta', '').strip()
        municipio = request.form.get('municipio', '').strip()
        fecha = request.form.get('fecha', '').strip()
        turno = request.form.get('turno', '').strip()
        semana = request.form.get('semana', '').strip()
        conductor = request.form.get('conductor', '').strip()
        km_raw = request.form.get('km', '').strip()
        lleva_trae = request.form.get('lleva_trae_personal', '').strip()
        quien_diligencia = request.form.get('quien_diligencia', '').strip()

        if not placa:
            flash('La placa es obligatoria', 'error')
            return redirect(url_for('registro'))

        if not km_raw:
            if es_ruta_administrativa(ruta):
                km = 0
            else:
                flash('Kilómetros es obligatorio para rutas operativas', 'error')
                return redirect(url_for('registro'))
        else:
            try:
                km = float(km_raw)
            except ValueError:
                flash('Kilómetros debe ser un número', 'error')
                return redirect(url_for('registro'))

        store.agregar_viaje(
            placa=placa, numero_interno=numero_interno, ruta=ruta, municipio=municipio,
            fecha_viaje=fecha, turno=turno, semana=semana, conductor=conductor, km=km,
            lleva_trae_personal=lleva_trae, quien_diligencia=quien_diligencia
        )
        flash('Viaje guardado', 'success')
        return redirect(url_for('lista_viajes'))

    hoy = ahora_colombia()
    ruta_qr = request.args.get('ruta', '').strip().upper()
    datos_qr = {}
    es_qr_valido = ruta_qr in RUTAS_TODAS
    if es_qr_valido:
        datos_qr = datos_por_ruta(ruta_qr)

    return render_template(
        'registro.html', rutas=RUTAS_TODAS, municipios=MUNICIPIOS, placas=PLACAS_CONOCIDAS,
        fecha_hoy=hoy.strftime('%d/%m/%Y'),
        semana_hoy=f"Semana {semana_operativa(hoy.date())}",
        desde_qr=es_qr_valido,
        ruta_preseleccionada=ruta_qr if es_qr_valido else '',
        placa_preseleccionada=datos_qr.get('placa', ''),
        conductor_preseleccionado=datos_qr.get('conductor', ''),
        numero_interno_preseleccionado=datos_qr.get('numero_interno', ''),
        municipio_preseleccionado=datos_qr.get('municipio', ''),
        km_preseleccionado=datos_qr.get('km', ''),
        es_administrativa=datos_qr.get('es_administrativa', False),
    )


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


@app.route('/qr')
def qr_codigos():
    return render_template('qr.html', rutas=RUTAS_TODAS)


@app.route('/qr/imagen/<ruta>')
def qr_imagen(ruta):
    url_destino = url_for('registro', ruta=ruta, _external=True)
    png_bytes = generar_qr_bytes(url_destino)
    return send_file(io.BytesIO(png_bytes), mimetype='image/png')


@app.route('/descargar-excel')
def descargar_excel():
    store.inicializar_excel()
    return send_file(store.EXCEL_PATH, as_attachment=True, download_name='viajes_control_vehiculos.xlsx')


if __name__ == '__main__':
    store.inicializar_excel()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
