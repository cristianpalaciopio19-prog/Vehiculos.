"""
Encuesta de satisfacción del servicio de transporte – Colombina
Flask + PostgreSQL (Supabase). Encuesta pública anónima + panel administrativo privado.
"""
import io
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps

import psycopg2
import psycopg2.extras
import qrcode
from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # https correcto en Render (enlace y QR)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar-esta-clave")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "colombina2026")
TZ = "America/Bogota"

ESCALA = {1: "Muy malo", 2: "Malo", 3: "Regular", 4: "Bueno", 5: "Excelente"}

SCHEMA = """
create table if not exists enc_rutas (
  id serial primary key, nombre text not null unique,
  activa boolean not null default true, orden int not null default 0);
create table if not exists enc_preguntas (
  id serial primary key, texto text not null,
  tipo text not null default 'escala', activa boolean not null default true,
  orden int not null default 0);
create table if not exists enc_respuestas (
  id bigserial primary key, creado timestamptz not null default now(),
  ruta text not null, comentario text);
create table if not exists enc_detalle (
  id bigserial primary key,
  respuesta_id bigint not null references enc_respuestas(id) on delete cascade,
  pregunta_id int references enc_preguntas(id) on delete set null,
  pregunta_texto text not null,
  valor smallint not null check (valor between 1 and 5));
create table if not exists enc_ajustes (
  clave text primary key, mime text, datos bytea,
  actualizado timestamptz not null default now());
"""


# ───────────────────────── Base de datos ─────────────────────────
def db():
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor,
                                connect_timeout=10)
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def q(sql, params=None, one=False, commit=False):
    conn = db()
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        rows = cur.fetchall() if cur.description else None
    if commit:
        conn.commit()
    if rows is None:
        return None
    return (rows[0] if rows else None) if one else rows


def init_db():
    if not DATABASE_URL:
        return
    try:
        with app.app_context():
            existe = q("select to_regclass('enc_respuestas') is not null as ok", one=True)
            if not existe["ok"]:
                q(SCHEMA, commit=True)
    except Exception as e:  # no detener el arranque si la BD tarda en responder
        print("Aviso init_db:", e)


init_db()


# ───────────────────────── Utilidades ─────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("login", next=request.path))
        return f(*a, **kw)
    return wrapper


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.template_filter("num")
def num(v, dec=2):
    """Formato colombiano: coma decimal."""
    return f"{v:.{dec}f}".replace(".", ",")


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


@app.template_filter("fecha")
def fecha(d, hora=True):
    s = f"{d.day} {MESES[d.month - 1]} {d.year}"
    if hora:
        h = d.strftime("%I:%M").lstrip("0")
        s += f", {h} {'a. m.' if d.hour < 12 else 'p. m.'}"
    return s


_logo_cache = {"v": None, "t": None}


def logo_version():
    """Devuelve un sello de versión del logo (o None si no se ha cargado). Cache de 60 s."""
    ahora = datetime.now()
    if _logo_cache["t"] and (ahora - _logo_cache["t"]).seconds < 60:
        return _logo_cache["v"]
    try:
        r = q("select extract(epoch from actualizado)::bigint as v from enc_ajustes where clave='logo'", one=True)
        _logo_cache["v"] = r["v"] if r else None
    except Exception:
        db().rollback()
        _logo_cache["v"] = None
    _logo_cache["t"] = ahora
    return _logo_cache["v"]


@app.context_processor
def inject_logo():
    return {"logo_v": logo_version()}


@app.before_request
def check_csrf():
    if request.method == "POST" and request.endpoint not in ("login",):
        token = request.form.get("csrf") or request.headers.get("X-CSRF")
        if not token or token != session.get("csrf"):
            abort(400, "Formulario expirado. Recargue la página e intente de nuevo.")


def filtros():
    ruta = request.args.get("ruta", "").strip()
    desde = request.args.get("desde", "").strip()
    hasta = request.args.get("hasta", "").strip()
    where, params = ["1=1"], []
    if ruta:
        where.append("r.ruta = %s")
        params.append(ruta)
    if desde:
        where.append(f"(r.creado at time zone '{TZ}')::date >= %s")
        params.append(desde)
    if hasta:
        where.append(f"(r.creado at time zone '{TZ}')::date <= %s")
        params.append(hasta)
    return {"ruta": ruta, "desde": desde, "hasta": hasta}, " and ".join(where), params


def datos_filtrados():
    f, where, params = filtros()
    respuestas = q(f"""
        select r.id, r.ruta, r.comentario, r.creado at time zone '{TZ}' as fecha
        from enc_respuestas r where {where} order by r.creado desc""", params)
    detalle = q(f"""
        select d.respuesta_id, d.pregunta_id, d.pregunta_texto, d.valor
        from enc_detalle d join enc_respuestas r on r.id = d.respuesta_id
        where {where}""", params)
    return f, respuestas, detalle


def clasif(v):
    return "pos" if v >= 4 else ("reg" if v == 3 else "neg")


def calcular_estadisticas(respuestas, detalle):
    preguntas = q("select id, texto, activa, orden from enc_preguntas where tipo='escala' order by orden, id")
    textos = {p["id"]: p["texto"] for p in preguntas}
    total = len(respuestas)
    vals = [d["valor"] for d in detalle]
    prom = round(sum(vals) / len(vals), 2) if vals else 0
    dist = {k: 0 for k in range(1, 6)}
    for v in vals:
        dist[v] += 1
    n = len(vals) or 1
    pos = sum(dist[k] for k in (4, 5))
    reg = dist[3]
    neg = sum(dist[k] for k in (1, 2))

    # Por pregunta
    por_preg = {}
    for d in detalle:
        key = d["pregunta_id"] or d["pregunta_texto"]
        item = por_preg.setdefault(key, {"texto": textos.get(d["pregunta_id"], d["pregunta_texto"]),
                                         "orden": next((p["orden"] for p in preguntas if p["id"] == d["pregunta_id"]), 99),
                                         "vals": [], "dist": {k: 0 for k in range(1, 6)}})
        item["vals"].append(d["valor"])
        item["dist"][d["valor"]] += 1
    lista_preg = []
    for item in sorted(por_preg.values(), key=lambda x: x["orden"]):
        c = len(item["vals"])
        lista_preg.append({
            "texto": item["texto"], "n": c,
            "promedio": round(sum(item["vals"]) / c, 2),
            "dist": [item["dist"][k] for k in range(1, 6)],
            "pos": round(100 * sum(item["dist"][k] for k in (4, 5)) / c, 1),
            "reg": round(100 * item["dist"][3] / c, 1),
            "neg": round(100 * sum(item["dist"][k] for k in (1, 2)) / c, 1),
        })

    # Por ruta
    ruta_de = {r["id"]: r["ruta"] for r in respuestas}
    por_ruta = {}
    for d in detalle:
        rt = ruta_de.get(d["respuesta_id"])
        item = por_ruta.setdefault(rt, {"vals": [], "ids": set()})
        item["vals"].append(d["valor"])
        item["ids"].add(d["respuesta_id"])
    lista_ruta = sorted([{
        "ruta": k, "encuestas": len(v["ids"]),
        "promedio": round(sum(v["vals"]) / len(v["vals"]), 2),
        "pos": round(100 * sum(1 for x in v["vals"] if x >= 4) / len(v["vals"]), 1),
    } for k, v in por_ruta.items()], key=lambda x: x["promedio"], reverse=True)

    # Tendencia por semana
    sem = {}
    det_por_resp = {}
    for d in detalle:
        det_por_resp.setdefault(d["respuesta_id"], []).append(d["valor"])
    for r in respuestas:
        f = r["fecha"]
        lunes = (f - timedelta(days=f.weekday())).date()
        s = sem.setdefault(lunes, [])
        s.extend(det_por_resp.get(r["id"], []))
    tendencia = [{"semana": k.strftime("%d/%m/%Y"), "promedio": round(sum(v) / len(v), 2)}
                 for k, v in sorted(sem.items()) if v]

    return {
        "total": total, "promedio": prom,
        "pct_pos": round(100 * pos / n, 1) if vals else 0,
        "pct_reg": round(100 * reg / n, 1) if vals else 0,
        "pct_neg": round(100 * neg / n, 1) if vals else 0,
        "dist": [dist[k] for k in range(1, 6)],
        "preguntas": lista_preg, "rutas": lista_ruta, "tendencia": tendencia,
        "comentarios": [r for r in respuestas if r["comentario"]],
    }


# ───────────────────────── Encuesta pública ─────────────────────────
@app.route("/", methods=["GET"])
def encuesta():
    rutas = q("select nombre from enc_rutas where activa order by orden, nombre")
    preguntas = q("select id, texto from enc_preguntas where activa and tipo='escala' order by orden, id")
    return render_template("encuesta.html", rutas=rutas, preguntas=preguntas, escala=ESCALA)


@app.route("/enviar", methods=["POST"])
def enviar():
    ruta = request.form.get("ruta", "").strip()
    rutas_validas = {r["nombre"] for r in q("select nombre from enc_rutas where activa")}
    if ruta not in rutas_validas:
        flash("Seleccione una ruta válida.")
        return redirect(url_for("encuesta"))
    preguntas = q("select id, texto from enc_preguntas where activa and tipo='escala' order by orden, id")
    valores = []
    for p in preguntas:
        try:
            v = int(request.form.get(f"p{p['id']}", ""))
        except ValueError:
            v = 0
        if v not in ESCALA:
            flash("Por favor responda todas las preguntas.")
            return redirect(url_for("encuesta"))
        valores.append((p, v))
    comentario = (request.form.get("comentario") or "").strip()[:2000] or None

    conn = db()
    with conn.cursor() as cur:
        cur.execute("insert into enc_respuestas (ruta, comentario) values (%s, %s) returning id",
                    (ruta, comentario))
        rid = cur.fetchone()["id"]
        psycopg2.extras.execute_values(
            cur, "insert into enc_detalle (respuesta_id, pregunta_id, pregunta_texto, valor) values %s",
            [(rid, p["id"], p["texto"], v) for p, v in valores])
    conn.commit()
    session.pop("csrf", None)
    return redirect(url_for("gracias"))


@app.route("/gracias")
def gracias():
    return render_template("gracias.html")


@app.route("/logo")
def logo():
    r = q("select mime, datos from enc_ajustes where clave='logo'", one=True)
    if not r:
        abort(404)
    resp = send_file(io.BytesIO(bytes(r["datos"])), mimetype=r["mime"])
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.route("/qr.png")
def qr_png():
    url = request.url_root.rstrip("/") + url_for("encuesta")
    img = qrcode.make(url, box_size=12, border=2)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    descargar = request.args.get("descargar") == "1"
    return send_file(buf, mimetype="image/png", as_attachment=descargar,
                     download_name="QR_Encuesta_Transporte_Colombina.png")


# ───────────────────────── Administración ─────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session.permanent = True
            session["admin"] = True
            return redirect(request.args.get("next") or url_for("admin"))
        flash("Contraseña incorrecta.")
    return render_template("login.html")


@app.route("/admin/salir")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin")
@login_required
def admin():
    f, respuestas, detalle = datos_filtrados()
    stats = calcular_estadisticas(respuestas, detalle)
    rutas = q("select nombre from enc_rutas order by orden, nombre")
    return render_template("admin.html", s=stats, f=f, rutas=rutas, escala=ESCALA,
                           url_publica=request.url_root.rstrip("/") + url_for("encuesta"))


@app.route("/admin/respuestas")
@login_required
def admin_respuestas():
    f, respuestas, detalle = datos_filtrados()
    preguntas = q("select id, texto from enc_preguntas where tipo='escala' order by orden, id")
    por_resp = {}
    for d in detalle:
        por_resp.setdefault(d["respuesta_id"], {})[d["pregunta_id"]] = d["valor"]
    rutas = q("select nombre from enc_rutas order by orden, nombre")
    return render_template("respuestas.html", respuestas=respuestas, preguntas=preguntas,
                           por_resp=por_resp, f=f, rutas=rutas)


@app.route("/admin/respuestas/<int:rid>/eliminar", methods=["POST"])
@login_required
def eliminar_respuesta(rid):
    q("delete from enc_respuestas where id=%s", (rid,), commit=True)
    flash("Respuesta eliminada.")
    return redirect(request.referrer or url_for("admin_respuestas"))


@app.route("/admin/configuracion", methods=["GET", "POST"])
@login_required
def configuracion():
    if request.method == "POST":
        acc = request.form.get("accion")
        if acc == "logo_subir":
            f = request.files.get("logo")
            tipos = {"image/png", "image/jpeg", "image/svg+xml", "image/webp"}
            if f and f.mimetype in tipos:
                datos = f.read()
                if len(datos) > 2 * 1024 * 1024:
                    flash("El logo debe pesar menos de 2 MB.")
                else:
                    q("""insert into enc_ajustes (clave, mime, datos, actualizado) values ('logo', %s, %s, now())
                         on conflict (clave) do update set mime=excluded.mime, datos=excluded.datos, actualizado=now()""",
                      (f.mimetype, psycopg2.Binary(datos)), commit=True)
                    _logo_cache["t"] = None
                    flash("Logo actualizado.")
            else:
                flash("Seleccione una imagen PNG, JPG, SVG o WEBP.")
            return redirect(url_for("configuracion") + "#logo")
        elif acc == "logo_quitar":
            q("delete from enc_ajustes where clave='logo'", commit=True)
            _logo_cache["t"] = None
            flash("Logo eliminado.")
            return redirect(url_for("configuracion") + "#logo")
        elif acc == "ruta_agregar":
            nombre = request.form.get("nombre", "").strip().upper()
            if nombre:
                q("""insert into enc_rutas (nombre, orden)
                     values (%s, coalesce((select max(orden) from enc_rutas),0)+1)
                     on conflict (nombre) do update set activa=true""", (nombre,), commit=True)
                flash(f"Ruta {nombre} guardada.")
        elif acc == "ruta_editar":
            rid = int(request.form["id"])
            nombre = request.form.get("nombre", "").strip().upper()
            viejo = q("select nombre from enc_rutas where id=%s", (rid,), one=True)
            if nombre and viejo:
                try:
                    q("update enc_rutas set nombre=%s where id=%s", (nombre, rid))
                    if request.form.get("propagar"):
                        q("update enc_respuestas set ruta=%s where ruta=%s", (nombre, viejo["nombre"]))
                    db().commit()
                    flash("Ruta actualizada.")
                except psycopg2.errors.UniqueViolation:
                    db().rollback()
                    flash("Ya existe una ruta con ese nombre.")
        elif acc == "ruta_toggle":
            q("update enc_rutas set activa = not activa where id=%s", (int(request.form["id"]),), commit=True)
        elif acc == "preg_agregar":
            texto = request.form.get("texto", "").strip()
            if texto:
                q("""insert into enc_preguntas (texto, orden)
                     values (%s, coalesce((select max(orden) from enc_preguntas),0)+1)""", (texto,), commit=True)
                flash("Pregunta agregada.")
        elif acc == "preg_editar":
            texto = request.form.get("texto", "").strip()
            if texto:
                q("update enc_preguntas set texto=%s where id=%s", (texto, int(request.form["id"])), commit=True)
                flash("Pregunta actualizada.")
        elif acc == "preg_toggle":
            q("update enc_preguntas set activa = not activa where id=%s", (int(request.form["id"]),), commit=True)
        elif acc in ("preg_subir", "preg_bajar"):
            pid = int(request.form["id"])
            lista = q("select id from enc_preguntas order by orden, id")
            ids = [p["id"] for p in lista]
            i = ids.index(pid)
            j = i - 1 if acc == "preg_subir" else i + 1
            if 0 <= j < len(ids):
                ids[i], ids[j] = ids[j], ids[i]
                for n, x in enumerate(ids, 1):
                    q("update enc_preguntas set orden=%s where id=%s", (n, x))
                db().commit()
        return redirect(url_for("configuracion") + request.form.get("ancla", ""))

    rutas = q("""select r.*, (select count(*) from enc_respuestas e where e.ruta=r.nombre) as n
                 from enc_rutas r order by orden, nombre""")
    preguntas = q("""select p.*, (select count(*) from enc_detalle d where d.pregunta_id=p.id) as n
                     from enc_preguntas p order by orden, id""")
    return render_template("configuracion.html", rutas=rutas, preguntas=preguntas)


@app.route("/admin/qr")
@login_required
def admin_qr():
    return render_template("qr.html", url_publica=request.url_root.rstrip("/") + url_for("encuesta"))


# ───────────────────────── Exportación Excel ─────────────────────────
NAVY = "102A5C"
GOLD = "F2A900"


def _encabezado(ws, fila, cols):
    for c, titulo in enumerate(cols, 1):
        cell = ws.cell(row=fila, column=c, value=titulo)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _anchos(ws, anchos):
    for i, w in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


@app.route("/admin/exportar")
@login_required
def exportar():
    f, respuestas, detalle = datos_filtrados()
    stats = calcular_estadisticas(respuestas, detalle)
    preguntas = q("select id, texto from enc_preguntas where tipo='escala' order by orden, id")
    por_resp = {}
    for d in detalle:
        por_resp.setdefault(d["respuesta_id"], {})[d["pregunta_id"]] = d["valor"]

    wb = Workbook()
    # Hoja 1: respuestas (una fila por encuesta)
    ws = wb.active
    ws.title = "Respuestas"
    cols = ["ID", "Fecha", "Hora", "Ruta"] + [f"P{i+2}. {p['texto']}" for i, p in enumerate(preguntas)] + \
           ["Promedio", "Recomendaciones / sugerencias"]
    _encabezado(ws, 1, cols)
    ws.row_dimensions[1].height = 75
    for fila, r in enumerate(reversed(respuestas), 2):
        vals = por_resp.get(r["id"], {})
        notas = [vals.get(p["id"]) for p in preguntas]
        validas = [v for v in notas if v]
        ws.append([r["id"], r["fecha"].date(), r["fecha"].strftime("%H:%M"), r["ruta"], *notas,
                   round(sum(validas) / len(validas), 2) if validas else None, r["comentario"] or ""])
        ws.cell(row=fila, column=2).number_format = "DD/MM/YYYY"
    _anchos(ws, [7, 12, 8, 9] + [16] * len(preguntas) + [10, 60])
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = ws.dimensions

    # Hoja 2: resumen por pregunta
    ws2 = wb.create_sheet("Resumen por pregunta")
    ws2["A1"] = "Encuesta de satisfacción del servicio de transporte – Colombina"
    ws2["A1"].font = Font(bold=True, size=14, color=NAVY)
    filtro_txt = f"Ruta: {f['ruta'] or 'Todas'} | Desde: {f['desde'] or '—'} | Hasta: {f['hasta'] or '—'}"
    ws2["A2"] = f"{filtro_txt} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws2["A4"], ws2["B4"] = "Total encuestas", stats["total"]
    ws2["A5"], ws2["B5"] = "Calificación promedio general", stats["promedio"]
    ws2["A6"], ws2["B6"] = "% Positivas (4-5)", stats["pct_pos"] / 100
    ws2["A7"], ws2["B7"] = "% Regulares (3)", stats["pct_reg"] / 100
    ws2["A8"], ws2["B8"] = "% Negativas (1-2)", stats["pct_neg"] / 100
    for c in ("B6", "B7", "B8"):
        ws2[c].number_format = "0.0%"
    for rr in range(4, 9):
        ws2.cell(row=rr, column=1).font = Font(bold=True)
    cols2 = ["Pregunta", "Respuestas", "Promedio", "Muy malo", "Malo", "Regular", "Bueno", "Excelente",
             "% Positivas", "% Regulares", "% Negativas"]
    _encabezado(ws2, 10, cols2)
    for i, p in enumerate(stats["preguntas"], 11):
        ws2.append([p["texto"], p["n"], p["promedio"], *p["dist"], p["pos"] / 100, p["reg"] / 100, p["neg"] / 100])
        for c in (9, 10, 11):
            ws2.cell(row=i, column=c).number_format = "0.0%"
        ws2.cell(row=i, column=1).alignment = Alignment(wrap_text=True)
    _anchos(ws2, [60, 12, 10, 10, 8, 9, 8, 10, 12, 12, 12])

    # Hoja 3: por ruta
    ws3 = wb.create_sheet("Satisfacción por ruta")
    _encabezado(ws3, 1, ["Ruta", "Encuestas", "Promedio", "% Positivas"])
    for i, r in enumerate(stats["rutas"], 2):
        ws3.append([r["ruta"], r["encuestas"], r["promedio"], r["pos"] / 100])
        ws3.cell(row=i, column=4).number_format = "0.0%"
    _anchos(ws3, [12, 12, 12, 14])

    # Hoja 4: comentarios
    ws4 = wb.create_sheet("Recomendaciones")
    _encabezado(ws4, 1, ["Fecha", "Ruta", "Recomendación / sugerencia"])
    for i, r in enumerate(stats["comentarios"], 2):
        ws4.append([r["fecha"].date(), r["ruta"], r["comentario"]])
        ws4.cell(row=i, column=1).number_format = "DD/MM/YYYY"
        ws4.cell(row=i, column=3).alignment = Alignment(wrap_text=True, vertical="top")
    _anchos(ws4, [12, 10, 90])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    nombre = f"Encuesta_Transporte_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=nombre,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/salud")
def salud():
    try:
        q("select 1")
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
