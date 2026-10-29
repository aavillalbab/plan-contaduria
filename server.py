#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plan de estudio - Contaduría Pública (Colombia)
Servidor local sin dependencias externas: Python 3.8+ (usa solo la biblioteca estándar).
El progreso se guarda en SQLite: data/progreso.db
Uso:  python3 server.py   ->  http://localhost:8765
"""
import datetime as dt
import glob
import json
import mimetypes
import os
import random
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import webbrowser
import base64
import xlsxcheck
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("PLAN_DB", os.path.join(BASE, "data", "progreso.db"))
CONTENT_DIR = os.path.join(BASE, "content")
STATIC_DIR = os.path.join(BASE, "static")
PORT = int(os.environ.get("PORT", "8765"))

AREAS = [
    ("CON", "Contabilidad y reporte financiero", 25, "#2563eb", 1),
    ("TRI", "Tributaria y aduanera", 20, "#d97706", 2),
    ("AUD", "Auditoría, revisoría fiscal y control", 20, "#7c3aed", 3),
    ("FIN", "Costos y finanzas", 15, "#059669", 4),
    ("LEG", "Legal, laboral y ética", 12, "#dc2626", 5),
    ("FUN", "Fundamentos, cuantitativas y TI", 8, "#0891b2", 6),
]
LEITNER = [0, 1, 3, 7, 14, 30]
DEFAULT_SCHEDULE = {
    "start_date": "",
    "weekly_minutes": {"0": 90, "1": 90, "2": 90, "3": 90, "4": 90, "5": 150, "6": 0},
    "modules": [],
    "depth": 1.0,
    "include_eval": True,
    "include_review": True,
    "review_day": 5,
    "max_session": 90,
    "order": "secuencial",
    "blocked": "",
    "target_date": "",
}
DEFAULT_SETTINGS = {"umbral": 70}

SCHEMA = """
CREATE TABLE IF NOT EXISTS areas(id TEXT PRIMARY KEY, nombre TEXT, peso REAL, color TEXT, orden INT);
CREATE TABLE IF NOT EXISTS modules(id TEXT PRIMARY KEY, orden INT, titulo TEXT, semestres TEXT, descripcion TEXT);
CREATE TABLE IF NOT EXISTS subjects(id TEXT PRIMARY KEY, module_id TEXT, orden INT, nombre TEXT, area_id TEXT, descripcion TEXT, recursos TEXT DEFAULT '[]');
CREATE TABLE IF NOT EXISTS topics(subject_id TEXT, idx INT, nombre TEXT, horas REAL, clase TEXT DEFAULT '', recursos TEXT DEFAULT '[]', PRIMARY KEY(subject_id, idx));
CREATE TABLE IF NOT EXISTS flashcards(id TEXT PRIMARY KEY, subject_id TEXT, front TEXT, back TEXT, nota TEXT, origin TEXT DEFAULT 'seed');
CREATE TABLE IF NOT EXISTS card_progress(card_id TEXT PRIMARY KEY, box INT DEFAULT 0, due TEXT, reps INT DEFAULT 0, lapses INT DEFAULT 0, last TEXT);
CREATE TABLE IF NOT EXISTS questions(id TEXT PRIMARY KEY, subject_id TEXT, enunciado TEXT, opciones TEXT, correcta INT, peso INT, retro TEXT, origin TEXT DEFAULT 'seed');
CREATE TABLE IF NOT EXISTS topic_progress(subject_id TEXT, idx INT, done INT DEFAULT 0, done_at TEXT, PRIMARY KEY(subject_id, idx));
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT, scope_id TEXT, scope_label TEXT, created TEXT, finished TEXT,
  status TEXT DEFAULT 'en_curso', n INT, score_pct REAL, puntos REAL, max_puntos REAL, nota REAL, ponderada REAL, resumen TEXT);
CREATE TABLE IF NOT EXISTS attempt_answers(attempt_id INT, pos INT, question_id TEXT, perm TEXT, chosen INT, correct INT, puntos REAL DEFAULT 0, max_puntos REAL,
  PRIMARY KEY(attempt_id, pos));
CREATE TABLE IF NOT EXISTS schedule_items(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, tipo TEXT, subject_id TEXT, topic_idx INT, titulo TEXT,
  minutos INT, parte INT DEFAULT 1, partes INT DEFAULT 1, status TEXT DEFAULT 'pending', origin TEXT DEFAULT 'auto');
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS notes(subject_id TEXT PRIMARY KEY, texto TEXT, updated TEXT);
CREATE TABLE IF NOT EXISTS activity(day TEXT PRIMARY KEY, n INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS entregas(id INTEGER PRIMARY KEY AUTOINCREMENT, ejercicio_id TEXT, filename TEXT, path TEXT, fecha TEXT, auto_score REAL, auto_detail TEXT, claude_nota REAL, claude_comentarios TEXT, estado TEXT DEFAULT 'entregado');
"""

_lock = threading.Lock()


def today():
    return dt.date.today().isoformat()


def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def rows(conn, sql, args=()):
    return [dict(r) for r in conn.execute(sql, args).fetchall()]


def one(conn, sql, args=()):
    r = conn.execute(sql, args).fetchone()
    return dict(r) if r else None


# ---------------------------------------------------------------- init / seed
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = connect()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    for tbl, col, ddl in (("topics", "clase", "TEXT DEFAULT ''"), ("topics", "recursos", "TEXT DEFAULT '[]'"), ("subjects", "recursos", "TEXT DEFAULT '[]'")):
        cols = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % tbl).fetchall()]
        if col not in cols:
            conn.execute("ALTER TABLE %s ADD COLUMN %s %s" % (tbl, col, ddl))
    for aid, nombre, peso, color, orden in AREAS:
        conn.execute("INSERT OR IGNORE INTO areas(id,nombre,peso,color,orden) VALUES(?,?,?,?,?)", (aid, nombre, peso, color, orden))
        conn.execute("UPDATE areas SET nombre=?, color=?, orden=? WHERE id=?", (nombre, color, orden, aid))
    seed_content(conn)
    conn.commit()
    conn.close()
    auto_backup()


def load_lessons():
    out = {}
    for path in sorted(glob.glob(os.path.join(CONTENT_DIR, "lessons", "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                out.update(json.load(fh))
        except Exception as exc:
            print("Aviso: no se pudo leer", path, exc)
    return out


def clean_resources(lst):
    res = []
    for r in lst or []:
        u = str(r.get("url", "")).strip()
        if u.startswith("https://") or u.startswith("http://"):
            res.append({"titulo": str(r.get("titulo", u))[:160], "url": u, "tipo": r.get("tipo", "articulo"), "fuente": str(r.get("fuente", ""))[:80]})
    return res


def seed_content(conn):
    seen_sub, seen_card, seen_q, seen_mod = set(), set(), set(), set()
    lessons = load_lessons()
    for path in sorted(glob.glob(os.path.join(CONTENT_DIR, "m*.json"))):
        with open(path, encoding="utf-8") as fh:
            mod = json.load(fh)
        seen_mod.add(mod["id"])
        conn.execute(
            "INSERT INTO modules(id,orden,titulo,semestres,descripcion) VALUES(?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET orden=excluded.orden,titulo=excluded.titulo,semestres=excluded.semestres,descripcion=excluded.descripcion",
            (mod["id"], mod["orden"], mod["titulo"], mod.get("semestres", ""), mod.get("descripcion", "")),
        )
        for so, s in enumerate(mod["materias"], 1):
            sid = s["id"]
            seen_sub.add(sid)
            les = lessons.get(sid, {})
            conn.execute(
                "INSERT INTO subjects(id,module_id,orden,nombre,area_id,descripcion,recursos) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET module_id=excluded.module_id,orden=excluded.orden,nombre=excluded.nombre,area_id=excluded.area_id,descripcion=excluded.descripcion,recursos=excluded.recursos",
                (sid, mod["id"], so, s["nombre"], s["area"], s.get("descripcion", ""), json.dumps(clean_resources(les.get("recursos")), ensure_ascii=False)),
            )
            conn.execute("DELETE FROM topics WHERE subject_id=?", (sid,))
            ltemas = les.get("temas", [])
            for i, (tn, th) in enumerate(s["temas"]):
                lt = ltemas[i] if i < len(ltemas) else {}
                conn.execute("INSERT INTO topics(subject_id,idx,nombre,horas,clase,recursos) VALUES(?,?,?,?,?,?)",
                             (sid, i, tn, th, lt.get("clase", ""), json.dumps(clean_resources(lt.get("recursos")), ensure_ascii=False)))
            for i, c in enumerate(s["cards"], 1):
                cid = "%s-c%d" % (sid, i)
                seen_card.add(cid)
                conn.execute(
                    "INSERT INTO flashcards(id,subject_id,front,back,nota,origin) VALUES(?,?,?,?,?,'seed') "
                    "ON CONFLICT(id) DO UPDATE SET subject_id=excluded.subject_id,front=excluded.front,back=excluded.back,nota=excluded.nota",
                    (cid, sid, c[0], c[1], c[2] if len(c) > 2 else ""),
                )
            for i, q in enumerate(s["qs"], 1):
                qid = "%s-q%d" % (sid, i)
                seen_q.add(qid)
                conn.execute(
                    "INSERT INTO questions(id,subject_id,enunciado,opciones,correcta,peso,retro,origin) VALUES(?,?,?,?,?,?,?,'seed') "
                    "ON CONFLICT(id) DO UPDATE SET subject_id=excluded.subject_id,enunciado=excluded.enunciado,opciones=excluded.opciones,"
                    "correcta=excluded.correcta,peso=excluded.peso,retro=excluded.retro",
                    (qid, sid, q[0], json.dumps(q[1], ensure_ascii=False), q[2], q[3], q[4]),
                )
    # limpiar contenido sembrado que ya no existe (nunca toca el contenido del usuario)
    for (table, col, seen, extra) in (
        ("flashcards", "id", seen_card, " AND origin='seed'"),
        ("questions", "id", seen_q, " AND origin='seed'"),
    ):
        for r in conn.execute("SELECT %s FROM %s WHERE 1=1%s" % (col, table, extra)).fetchall():
            if r[0] not in seen:
                conn.execute("DELETE FROM %s WHERE %s=?" % (table, col), (r[0],))
    for r in conn.execute("SELECT id FROM subjects").fetchall():
        if r[0] not in seen_sub:
            conn.execute("DELETE FROM subjects WHERE id=?", (r[0],))
            conn.execute("DELETE FROM topics WHERE subject_id=?", (r[0],))
    for r in conn.execute("SELECT id FROM modules").fetchall():
        if r[0] not in seen_mod:
            conn.execute("DELETE FROM modules WHERE id=?", (r[0],))


def auto_backup():
    """Copia diaria de la base de datos (conserva las 14 más recientes)."""
    try:
        if not os.path.exists(DB_PATH):
            return
        bdir = os.path.join(os.path.dirname(DB_PATH), "backups")
        os.makedirs(bdir, exist_ok=True)
        dest = os.path.join(bdir, "progreso-%s.db" % dt.date.today().strftime("%Y%m%d"))
        if not os.path.exists(dest):
            src = sqlite3.connect(DB_PATH)
            dst = sqlite3.connect(dest)
            src.backup(dst)
            dst.close()
            src.close()
        files = sorted(glob.glob(os.path.join(bdir, "progreso-*.db")))
        for old in files[:-14]:
            os.remove(old)
    except Exception as exc:  # pragma: no cover
        print("Aviso: no se pudo crear la copia de seguridad:", exc)


# ---------------------------------------------------------------- settings
def get_setting(conn, key, default):
    r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if not r:
        return json.loads(json.dumps(default))
    try:
        v = json.loads(r[0])
    except Exception:
        return default
    if isinstance(default, dict) and isinstance(v, dict):
        m = json.loads(json.dumps(default))
        m.update(v)
        return m
    return v


def set_setting(conn, key, value):
    conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value, ensure_ascii=False)))


def bump(conn):
    d = today()
    conn.execute("INSERT INTO activity(day,n) VALUES(?,1) ON CONFLICT(day) DO UPDATE SET n=n+1", (d,))


# ---------------------------------------------------------------- scoring helpers
def latest_answers(conn):
    """Último resultado conocido por pregunta (en todos los intentos)."""
    out = {}
    for r in conn.execute(
        "SELECT aa.question_id q, aa.correct c FROM attempt_answers aa JOIN attempts a ON a.id=aa.attempt_id "
        "WHERE aa.chosen IS NOT NULL ORDER BY a.id, aa.pos"
    ).fetchall():
        out[r["q"]] = r["c"]
    return out


def mastery_tables(conn):
    latest = latest_answers(conn)
    qs = rows(conn, "SELECT q.id, q.peso, q.subject_id, s.area_id, s.module_id FROM questions q JOIN subjects s ON s.id=q.subject_id")
    by_sub, by_area, by_mod = {}, {}, {}
    for q in qs:
        for key, tbl in ((q["subject_id"], by_sub), (q["area_id"], by_area), (q["module_id"], by_mod)):
            t = tbl.setdefault(key, {"total": 0, "answered": 0, "pts": 0.0, "max": 0.0})
            t["total"] += 1
            if q["id"] in latest:
                t["answered"] += 1
                t["max"] += q["peso"]
                if latest[q["id"]]:
                    t["pts"] += q["peso"]
    for tbl in (by_sub, by_area, by_mod):
        for t in tbl.values():
            t["pct"] = round(100.0 * t["pts"] / t["max"], 1) if t["max"] else None
    return by_sub, by_area, by_mod


def weighted_average(items, weights):
    """items: {area: pct|None}; weights: {area: peso}"""
    num = den = 0.0
    for a, pct in items.items():
        if pct is None:
            continue
        w = weights.get(a, 0)
        num += w * pct
        den += w
    return round(num / den, 1) if den else None


def level_label(pct, umbral):
    if pct is None:
        return "Sin datos"
    if pct >= 90:
        return "Dominio"
    if pct >= umbral:
        return "Aprobado"
    if pct >= 50:
        return "En desarrollo"
    return "Refuerzo prioritario"


# ---------------------------------------------------------------- API: bootstrap
def api_bootstrap(conn, q, b):
    areas = rows(conn, "SELECT * FROM areas ORDER BY orden")
    by_sub, by_area, by_mod = mastery_tables(conn)
    tp = {(r["subject_id"], r["idx"]): r for r in rows(conn, "SELECT * FROM topic_progress")}
    cards = {r["subject_id"]: r["n"] for r in rows(conn, "SELECT subject_id, COUNT(*) n FROM flashcards GROUP BY subject_id")}
    qn = {r["subject_id"]: r["n"] for r in rows(conn, "SELECT subject_id, COUNT(*) n FROM questions GROUP BY subject_id")}
    mods = rows(conn, "SELECT * FROM modules ORDER BY orden")
    subs = rows(conn, "SELECT * FROM subjects ORDER BY module_id, orden")
    tops = rows(conn, "SELECT subject_id, idx, nombre, horas, (clase != '') AS tiene_clase, recursos FROM topics ORDER BY subject_id, idx")
    notes = {r["subject_id"]: r["texto"] for r in rows(conn, "SELECT * FROM notes")}
    topics_by_sub = {}
    for t in tops:
        d = tp.get((t["subject_id"], t["idx"]))
        t["done"] = bool(d and d["done"])
        t["tiene_clase"] = bool(t["tiene_clase"])
        t["n_recursos"] = len(json.loads(t.pop("recursos") or "[]"))
        topics_by_sub.setdefault(t["subject_id"], []).append(t)
    for s in subs:
        s["temas"] = topics_by_sub.get(s["id"], [])
        s["recursos"] = json.loads(s.get("recursos") or "[]")
        s["n_cards"] = cards.get(s["id"], 0)
        s["n_questions"] = qn.get(s["id"], 0)
        s["mastery"] = by_sub.get(s["id"], {}).get("pct")
        s["answered"] = by_sub.get(s["id"], {}).get("answered", 0)
        s["nota"] = notes.get(s["id"], "")
        s["horas"] = sum(t["horas"] for t in s["temas"])
        s["done_horas"] = sum(t["horas"] for t in s["temas"] if t["done"])
    for m in mods:
        m["materias"] = [s for s in subs if s["module_id"] == m["id"]]
        m["mastery"] = by_mod.get(m["id"], {}).get("pct")
    return {"areas": areas, "modules": mods, "settings": get_setting(conn, "app", DEFAULT_SETTINGS), "today": today()}


def api_stats(conn, q, b):
    areas = rows(conn, "SELECT * FROM areas ORDER BY orden")
    weights = {a["id"]: a["peso"] for a in areas}
    by_sub, by_area, by_mod = mastery_tables(conn)
    for a in areas:
        a.update({"mastery": by_area.get(a["id"], {}).get("pct"), "answered": by_area.get(a["id"], {}).get("answered", 0),
                  "total": by_area.get(a["id"], {}).get("total", 0)})
    glob_score = weighted_average({a["id"]: a["mastery"] for a in areas}, weights)
    t = one(conn, "SELECT COUNT(*) n, COALESCE(SUM(horas),0) h FROM topics")
    d = one(conn, "SELECT COUNT(*) n, COALESCE(SUM(t.horas),0) h FROM topic_progress p JOIN topics t ON t.subject_id=p.subject_id AND t.idx=p.idx WHERE p.done=1")
    tc = one(conn, "SELECT COUNT(*) n FROM flashcards")["n"]
    due = one(conn, "SELECT COUNT(*) n FROM flashcards f LEFT JOIN card_progress p ON p.card_id=f.id WHERE p.card_id IS NULL OR p.due<=?", (today(),))["n"]
    mastered = one(conn, "SELECT COUNT(*) n FROM card_progress WHERE box>=4")["n"]
    attempts = rows(conn, "SELECT id, scope_label, finished, nota, ponderada, score_pct FROM attempts WHERE status='finalizada' ORDER BY id DESC LIMIT 8")
    # racha
    days = {r["day"] for r in rows(conn, "SELECT day FROM activity WHERE n>0")}
    streak = 0
    cur = dt.date.today()
    if cur.isoformat() not in days:
        cur -= dt.timedelta(days=1)
    while cur.isoformat() in days:
        streak += 1
        cur -= dt.timedelta(days=1)
    td = today()
    sched_today = rows(conn, "SELECT si.*, s.nombre AS materia FROM schedule_items si LEFT JOIN subjects s ON s.id=si.subject_id WHERE fecha=? ORDER BY id", (td,))
    overdue = one(conn, "SELECT COUNT(*) n FROM schedule_items WHERE status='pending' AND fecha<?", (td,))["n"]
    active = one(conn, "SELECT id FROM attempts WHERE status='en_curso' ORDER BY id DESC LIMIT 1")
    return {
        "areas": areas, "global": glob_score, "temas_total": t["n"], "temas_hechos": d["n"], "horas_total": t["h"], "horas_hechas": d["h"],
        "cards_total": tc, "cards_due": due, "cards_dominadas": mastered, "attempts": attempts, "racha": streak,
        "hoy": sched_today, "atrasadas": overdue, "intento_activo": active["id"] if active else None,
        "talleres_total": len(load_talleres()), "talleres_entregados": one(conn, "SELECT COUNT(DISTINCT ejercicio_id) n FROM entregas")["n"],
        "talleres_calificados": one(conn, "SELECT COUNT(DISTINCT ejercicio_id) n FROM entregas WHERE claude_nota IS NOT NULL")["n"],
        "n_intentos": one(conn, "SELECT COUNT(*) n FROM attempts WHERE status='finalizada'")["n"],
    }


# ---------------------------------------------------------------- topics
def sync_schedule_for_topic(conn, sid, idx, done):
    if done:
        conn.execute("UPDATE schedule_items SET status='done' WHERE subject_id=? AND topic_idx=? AND tipo='estudio' AND status='pending'", (sid, idx))
    else:
        conn.execute("UPDATE schedule_items SET status='pending' WHERE subject_id=? AND topic_idx=? AND tipo='estudio' AND status='done'", (sid, idx))


def api_topic_toggle(conn, q, b):
    sid, idx, done = b["subject_id"], int(b["idx"]), 1 if b.get("done") else 0
    conn.execute(
        "INSERT INTO topic_progress(subject_id,idx,done,done_at) VALUES(?,?,?,?) "
        "ON CONFLICT(subject_id,idx) DO UPDATE SET done=excluded.done, done_at=excluded.done_at",
        (sid, idx, done, now() if done else None),
    )
    sync_schedule_for_topic(conn, sid, idx, done)
    if done:
        bump(conn)
    return {"ok": True}


def api_notes(conn, sid, b):
    conn.execute("INSERT INTO notes(subject_id,texto,updated) VALUES(?,?,?) ON CONFLICT(subject_id) DO UPDATE SET texto=excluded.texto, updated=excluded.updated",
                 (sid, b.get("texto", ""), now()))
    return {"ok": True}


def api_lesson(conn, q, b):
    sid, idx = q["subject"], int(q["idx"])
    t = one(conn, "SELECT t.*, s.nombre AS materia, s.area_id, s.module_id, s.recursos AS recursos_materia FROM topics t JOIN subjects s ON s.id=t.subject_id WHERE t.subject_id=? AND t.idx=?", (sid, idx))
    if not t:
        raise ValueError("Tema no encontrado")
    prog = one(conn, "SELECT done FROM topic_progress WHERE subject_id=? AND idx=?", (sid, idx))
    total = one(conn, "SELECT COUNT(*) n FROM topics WHERE subject_id=?", (sid,))["n"]
    t["recursos"] = json.loads(t["recursos"] or "[]")
    t["recursos_materia"] = json.loads(t.pop("recursos_materia") or "[]")
    t["done"] = bool(prog and prog["done"])
    t["total_temas"] = total
    t["modulo"] = one(conn, "SELECT titulo FROM modules WHERE id=?", (t["module_id"],))["titulo"]
    t["n_cards"] = one(conn, "SELECT COUNT(*) n FROM flashcards WHERE subject_id=?", (sid,))["n"]
    t["temas"] = rows(conn, "SELECT idx, nombre, (clase != '') AS tiene_clase FROM topics WHERE subject_id=? ORDER BY idx", (sid,))
    return t


# ---------------------------------------------------------------- flashcards
def api_cards(conn, q, b):
    where, args = [], []
    if q.get("subject"):
        where.append("f.subject_id=?")
        args.append(q["subject"])
    if q.get("module"):
        where.append("s.module_id=?")
        args.append(q["module"])
    if q.get("area"):
        where.append("s.area_id=?")
        args.append(q["area"])
    if q.get("due") == "1":
        where.append("(p.card_id IS NULL OR p.due<=?)")
        args.append(today())
    sql = ("SELECT f.id, f.subject_id, f.front, f.back, f.nota, f.origin, s.nombre AS materia, s.area_id, COALESCE(p.box,0) AS box, p.due, COALESCE(p.reps,0) AS reps "
           "FROM flashcards f JOIN subjects s ON s.id=f.subject_id LEFT JOIN card_progress p ON p.card_id=f.id")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY s.module_id, s.orden, f.id"
    out = rows(conn, sql, args)
    if q.get("shuffle") == "1":
        random.shuffle(out)
    lim = int(q.get("limit", 0) or 0)
    return out[:lim] if lim else out


def api_card_review(conn, q, b):
    cid, rating = b["card_id"], int(b["rating"])  # 0 otra vez, 1 difícil, 2 bien, 3 fácil
    cur = one(conn, "SELECT * FROM card_progress WHERE card_id=?", (cid,)) or {"box": 0, "reps": 0, "lapses": 0}
    box = cur["box"]
    lapses = cur["lapses"]
    if rating == 0:
        box, lapses = 0, lapses + 1
    elif rating == 1:
        box = max(1, box)
    elif rating == 2:
        box = min(5, box + 1)
    else:
        box = min(5, box + 2)
    due = dt.date.today() + dt.timedelta(days=LEITNER[box] if rating else 0)
    conn.execute(
        "INSERT INTO card_progress(card_id,box,due,reps,lapses,last) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(card_id) DO UPDATE SET box=excluded.box,due=excluded.due,reps=excluded.reps,lapses=excluded.lapses,last=excluded.last",
        (cid, box, due.isoformat(), cur["reps"] + 1, lapses, now()),
    )
    bump(conn)
    return {"box": box, "due": due.isoformat()}


def api_card_create(conn, q, b):
    sid = b["subject_id"]
    front, back = (b.get("front") or "").strip(), (b.get("back") or "").strip()
    if not front or not back or not one(conn, "SELECT id FROM subjects WHERE id=?", (sid,)):
        raise ValueError("Completa materia, pregunta y respuesta.")
    cid = "u-%s-%d" % (sid, int(dt.datetime.now().timestamp() * 1000))
    conn.execute("INSERT INTO flashcards(id,subject_id,front,back,nota,origin) VALUES(?,?,?,?,?,'user')", (cid, sid, front, back, (b.get("nota") or "").strip()))
    return {"id": cid}


def api_card_delete(conn, q, b):
    conn.execute("DELETE FROM flashcards WHERE id=? AND origin='user'", (b["id"],))
    conn.execute("DELETE FROM card_progress WHERE card_id=?", (b["id"],))
    return {"ok": True}


# ---------------------------------------------------------------- quiz
def scope_label(conn, scope, sid):
    if scope == "subject":
        return "Materia: " + one(conn, "SELECT nombre FROM subjects WHERE id=?", (sid,))["nombre"]
    if scope == "module":
        return "Módulo: " + one(conn, "SELECT titulo FROM modules WHERE id=?", (sid,))["titulo"]
    if scope == "area":
        return "Área: " + one(conn, "SELECT nombre FROM areas WHERE id=?", (sid,))["nombre"]
    return "Simulacro general"


def quiz_payload(conn, attempt_id):
    att = one(conn, "SELECT * FROM attempts WHERE id=?", (attempt_id,))
    rs = rows(conn,
              "SELECT aa.pos, aa.question_id, aa.perm, aa.chosen, aa.correct, aa.puntos, aa.max_puntos, q.enunciado, q.opciones, q.correcta, q.peso, q.retro, "
              "s.nombre AS materia, s.area_id FROM attempt_answers aa JOIN questions q ON q.id=aa.question_id JOIN subjects s ON s.id=q.subject_id "
              "WHERE aa.attempt_id=? ORDER BY aa.pos", (attempt_id,))
    qs = []
    for r in rs:
        perm = json.loads(r["perm"])
        opts = json.loads(r["opciones"])
        item = {"pos": r["pos"], "id": r["question_id"], "enunciado": r["enunciado"], "opciones": [opts[p] for p in perm], "peso": r["peso"],
                "materia": r["materia"], "area": r["area_id"], "chosen": r["chosen"]}
        if r["chosen"] is not None:
            item.update({"correct": bool(r["correct"]), "correcta": perm.index(r["correcta"]), "retro": r["retro"], "puntos": r["puntos"]})
        qs.append(item)
    return {"attempt": att, "questions": qs}


def api_quiz_start(conn, q, b):
    scope, sid = b.get("scope", "subject"), b.get("id")
    n = int(b.get("n") or 0)
    where, args = "", []
    if scope == "subject":
        where, args = "WHERE q.subject_id=?", [sid]
    elif scope == "module":
        where, args = "WHERE s.module_id=?", [sid]
    elif scope == "area":
        where, args = "WHERE s.area_id=?", [sid]
    pool = rows(conn, "SELECT q.id, q.opciones, q.peso, q.subject_id FROM questions q JOIN subjects s ON s.id=q.subject_id " + where, args)
    if not pool:
        raise ValueError("No hay preguntas para esta selección.")
    default_n = {"subject": 0, "module": 15, "area": 15, "all": 25}.get(scope, 15)
    n = n or default_n or len(pool)
    latest = latest_answers(conn)

    def key(qq):
        boost = 2.0 if qq["id"] not in latest else (1.0 if not latest[qq["id"]] else 0.0)
        return random.random() - boost

    pool.sort(key=key)
    chosen = pool[:min(n, len(pool))]
    random.shuffle(chosen)
    # cerrar intentos abandonados del mismo alcance no es necesario: se conservan hasta finalizar
    cur = conn.execute("INSERT INTO attempts(scope,scope_id,scope_label,created,status,n) VALUES(?,?,?,?, 'en_curso', ?)",
                       (scope, sid, scope_label(conn, scope, sid), now(), len(chosen)))
    aid = cur.lastrowid
    for i, qq in enumerate(chosen):
        perm = list(range(len(json.loads(qq["opciones"]))))
        random.shuffle(perm)
        conn.execute("INSERT INTO attempt_answers(attempt_id,pos,question_id,perm,max_puntos) VALUES(?,?,?,?,?)", (aid, i, qq["id"], json.dumps(perm), qq["peso"]))
    return quiz_payload(conn, aid)


def api_quiz_active(conn, q, b):
    a = one(conn, "SELECT id FROM attempts WHERE status='en_curso' ORDER BY id DESC LIMIT 1")
    return quiz_payload(conn, a["id"]) if a else {"attempt": None, "questions": []}


def api_quiz_answer(conn, q, b):
    aid, pos, chosen = int(b["attempt_id"]), int(b["pos"]), int(b["chosen"])
    r = one(conn, "SELECT aa.*, q.correcta, q.retro, q.peso FROM attempt_answers aa JOIN questions q ON q.id=aa.question_id WHERE aa.attempt_id=? AND aa.pos=?", (aid, pos))
    if not r:
        raise ValueError("Pregunta no encontrada")
    perm = json.loads(r["perm"])
    if r["chosen"] is None:
        ok = 1 if perm[chosen] == r["correcta"] else 0
        pts = float(r["peso"]) if ok else 0.0
        conn.execute("UPDATE attempt_answers SET chosen=?, correct=?, puntos=? WHERE attempt_id=? AND pos=?", (chosen, ok, pts, aid, pos))
        bump(conn)
    else:
        ok, pts, chosen = r["correct"], r["puntos"], r["chosen"]
    return {"correct": bool(ok), "correcta": perm.index(r["correcta"]), "retro": r["retro"], "puntos": pts, "max": r["peso"], "chosen": chosen}


def api_quiz_finish(conn, q, b):
    aid = int(b["attempt_id"])
    att = one(conn, "SELECT * FROM attempts WHERE id=?", (aid,))
    if not att:
        raise ValueError("Intento no encontrado")
    umbral = get_setting(conn, "app", DEFAULT_SETTINGS)["umbral"]
    weights = {a["id"]: a["peso"] for a in rows(conn, "SELECT id, peso FROM areas")}
    rs = rows(conn,
              "SELECT aa.pos, aa.perm, aa.chosen, aa.correct, aa.puntos, aa.max_puntos, q.enunciado, q.opciones, q.correcta, q.retro, q.subject_id, "
              "s.nombre AS materia, s.area_id FROM attempt_answers aa JOIN questions q ON q.id=aa.question_id JOIN subjects s ON s.id=q.subject_id "
              "WHERE aa.attempt_id=? ORDER BY aa.pos", (aid,))
    areas, subs, fallos = {}, {}, []
    tp = tm = 0.0
    for r in rs:
        for key, tbl in ((r["area_id"], areas), (r["subject_id"], subs)):
            t = tbl.setdefault(key, {"pts": 0.0, "max": 0.0, "n": 0, "ok": 0, "nombre": r["materia"] if tbl is subs else key})
            t["pts"] += r["puntos"] or 0
            t["max"] += r["max_puntos"]
            t["n"] += 1
            t["ok"] += 1 if r["correct"] else 0
        tp += r["puntos"] or 0
        tm += r["max_puntos"]
        if not r["correct"]:
            perm, opts = json.loads(r["perm"]), json.loads(r["opciones"])
            fallos.append({"pos": r["pos"], "enunciado": r["enunciado"], "peso": r["max_puntos"], "materia": r["materia"],
                           "tu_respuesta": opts[perm[r["chosen"]]] if r["chosen"] is not None else None, "correcta": opts[r["correcta"]], "retro": r["retro"]})
    for tbl in (areas, subs):
        for t in tbl.values():
            t["pct"] = round(100.0 * t["pts"] / t["max"], 1) if t["max"] else 0
            t["nivel"] = level_label(t["pct"], umbral)
    pct = round(100.0 * tp / tm, 1) if tm else 0
    pond = weighted_average({k: v["pct"] for k, v in areas.items()}, weights) or 0
    nota = round(pond / 20.0, 1)
    recs = []
    for sid, t in sorted(subs.items(), key=lambda kv: kv[1]["pct"]):
        if t["pct"] < umbral:
            recs.append("Refuerza «%s» (%s%%): repasa sus flashcards y vuelve a evaluarla." % (t["nombre"], t["pct"]))
    if not recs:
        recs.append("Excelente: superaste el umbral en todas las materias evaluadas. Avanza al siguiente tema o programa un repaso espaciado.")
    resumen = {"areas": areas, "materias": subs, "fallos": fallos, "recomendaciones": recs[:6], "nivel": level_label(pond, umbral), "aprobado": pond >= umbral, "umbral": umbral}
    conn.execute("UPDATE attempts SET status='finalizada', finished=?, score_pct=?, puntos=?, max_puntos=?, nota=?, ponderada=?, resumen=? WHERE id=?",
                 (now(), pct, tp, tm, nota, pond, json.dumps(resumen, ensure_ascii=False), aid))
    bump(conn)
    return attempt_detail(conn, aid)


def attempt_detail(conn, aid):
    a = one(conn, "SELECT * FROM attempts WHERE id=?", (aid,))
    if not a:
        raise ValueError("Intento no encontrado")
    a["resumen"] = json.loads(a["resumen"]) if a["resumen"] else None
    payload = quiz_payload(conn, aid)
    return {"attempt": a, "questions": payload["questions"]}


def api_attempts(conn, q, b):
    return rows(conn, "SELECT id, scope, scope_label, created, finished, status, n, score_pct, puntos, max_puntos, nota, ponderada FROM attempts ORDER BY id DESC LIMIT 100")


def api_attempt_discard(conn, q, b):
    aid = int(b["id"])
    conn.execute("DELETE FROM attempt_answers WHERE attempt_id=?", (aid,))
    conn.execute("DELETE FROM attempts WHERE id=?", (aid,))
    return {"ok": True}


# ---------------------------------------------------------------- schedule
def parse_blocked(txt):
    out = []
    for line in (txt or "").replace(";", "\n").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\s*(?:\.\.|a|al|-{1,2}>?|–|—)?\s*(\d{4}-\d{2}-\d{2})?$", line)
        if m:
            a = dt.date.fromisoformat(m.group(1))
            c = dt.date.fromisoformat(m.group(2)) if m.group(2) else a
            out.append((a, c))
    return out


def gen_schedule(conn, cfg):
    cfg = dict(DEFAULT_SCHEDULE, **cfg)
    start = dt.date.fromisoformat(cfg["start_date"]) if cfg.get("start_date") else dt.date.today()
    start = max(start, dt.date.today())
    weekly = {int(k): int(v or 0) for k, v in cfg["weekly_minutes"].items()}
    blocked = parse_blocked(cfg.get("blocked", ""))
    depth = max(0.25, float(cfg.get("depth") or 1))
    max_session = max(20, int(cfg.get("max_session") or 90))
    mods = rows(conn, "SELECT * FROM modules ORDER BY orden")
    selected = cfg.get("modules") or [m["id"] for m in mods]
    done_topics = {(r["subject_id"], r["idx"]) for r in rows(conn, "SELECT * FROM topic_progress WHERE done=1")}
    done_min = {}
    for r in rows(conn, "SELECT subject_id, topic_idx, SUM(minutos) m FROM schedule_items WHERE tipo='estudio' AND status='done' GROUP BY subject_id, topic_idx"):
        done_min[(r["subject_id"], r["topic_idx"])] = r["m"]
    done_eval = {r["subject_id"] for r in rows(conn, "SELECT subject_id FROM schedule_items WHERE tipo='evaluacion' AND status='done' AND subject_id IS NOT NULL")}
    done_mod_tasks = {r["titulo"] for r in rows(conn, "SELECT titulo FROM schedule_items WHERE origin='auto' AND status='done' AND tipo IN ('repaso','evaluacion') AND subject_id IS NULL")}
    # lista de materias
    subs = []
    for m in mods:
        if m["id"] not in selected:
            continue
        for s in rows(conn, "SELECT * FROM subjects WHERE module_id=? ORDER BY orden", (m["id"],)):
            s["modulo"] = m["titulo"]
            s["topics"] = rows(conn, "SELECT * FROM topics WHERE subject_id=? ORDER BY idx", (s["id"],))
            subs.append(s)
    if cfg.get("order") == "intercalado":  # alterna áreas consecutivas cuando es posible
        rest, ordered, last = subs[:], [], None
        while rest:
            pick = next((s for s in rest if s["area_id"] != last), rest[0])
            rest.remove(pick)
            ordered.append(pick)
            last = pick["area_id"]
        subs = ordered
    remaining_in_mod = {}
    for s in subs:
        remaining_in_mod[s["module_id"]] = remaining_in_mod.get(s["module_id"], 0) + 1
    mod_title = {m["id"]: m["titulo"] for m in mods}
    tasks, uid = [], 0
    for s in subs:
        for t in s["topics"]:
            if (s["id"], t["idx"]) in done_topics:
                continue
            need = int(round(t["horas"] * 60 * depth / 5.0) * 5) - done_min.get((s["id"], t["idx"]), 0)
            if need < 10:
                need = 10
            uid += 1
            tasks.append({"uid": uid, "tipo": "estudio", "subject_id": s["id"], "topic_idx": t["idx"], "titulo": "%s · %s" % (s["nombre"], t["nombre"]), "minutos": need})
        if cfg.get("include_eval") and s["id"] not in done_eval:
            uid += 1
            tasks.append({"uid": uid, "tipo": "evaluacion", "subject_id": s["id"], "topic_idx": None, "titulo": "Evaluación: " + s["nombre"], "minutos": 30})
        remaining_in_mod[s["module_id"]] -= 1
        if remaining_in_mod[s["module_id"]] == 0 and cfg.get("include_eval"):
            t1, t2 = "Repaso de flashcards del módulo: " + mod_title[s["module_id"]], "Evaluación integral del módulo: " + mod_title[s["module_id"]]
            if t1 not in done_mod_tasks:
                uid += 1
                tasks.append({"uid": uid, "tipo": "repaso", "subject_id": None, "topic_idx": None, "titulo": t1, "minutos": 30})
            if t2 not in done_mod_tasks:
                uid += 1
                tasks.append({"uid": uid, "tipo": "evaluacion", "subject_id": None, "topic_idx": None, "titulo": t2, "minutos": 45})
    conn.execute("DELETE FROM schedule_items WHERE origin IN ('auto','moved') AND status='pending'")
    items, day, guard, cur = [], start, 0, None
    queue = list(tasks)
    review_day = int(cfg.get("review_day", 5))

    def blocked_day(d):
        return any(a <= d <= c for a, c in blocked)

    while (queue or cur) and guard < 3000:
        guard += 1
        cap = weekly.get(day.weekday(), 0)
        if cap <= 0 or blocked_day(day):
            day += dt.timedelta(days=1)
            continue
        left = cap
        if cfg.get("include_review") and day.weekday() == review_day and cap >= 40:
            items.append({"uid": None, "fecha": day.isoformat(), "tipo": "repaso", "subject_id": None, "topic_idx": None,
                          "titulo": "Repaso semanal: flashcards pendientes (repetición espaciada)", "minutos": 20})
            left -= 20
        while left >= 10 and (cur or queue):
            if not cur:
                cur = dict(queue.pop(0))
                cur["rem"] = cur["minutos"]
            if left < 20 and cur["rem"] > left:
                break
            chunk = min(cur["rem"], max_session, left)
            if 0 < cur["rem"] - chunk < 10 and cur["rem"] <= left:
                chunk = cur["rem"]
            items.append({"uid": cur["uid"], "fecha": day.isoformat(), "tipo": cur["tipo"], "subject_id": cur["subject_id"], "topic_idx": cur["topic_idx"],
                          "titulo": cur["titulo"], "minutos": chunk})
            cur["rem"] -= chunk
            left -= chunk
            if cur["rem"] <= 0:
                cur = None
        day += dt.timedelta(days=1)
    counts = {}
    for it in items:
        if it["uid"]:
            counts[it["uid"]] = counts.get(it["uid"], 0) + 1
    seen = {}
    for it in items:
        parte, partes = 1, 1
        if it["uid"]:
            seen[it["uid"]] = seen.get(it["uid"], 0) + 1
            parte, partes = seen[it["uid"]], counts[it["uid"]]
        conn.execute("INSERT INTO schedule_items(fecha,tipo,subject_id,topic_idx,titulo,minutos,parte,partes,status,origin) VALUES(?,?,?,?,?,?,?,?, 'pending','auto')",
                     (it["fecha"], it["tipo"], it["subject_id"], it["topic_idx"], it["titulo"], it["minutos"], parte, partes))
    total_min = sum(i["minutos"] for i in items)
    study_items = [i for i in items if i["fecha"]]
    fin = max([i["fecha"] for i in study_items]) if study_items else None
    info = {"fin": fin, "minutos_pendientes": total_min, "sesiones": len(items), "aviso": None}
    tgt = cfg.get("target_date")
    if tgt and fin:
        if fin > tgt:
            weeks = max(1.0, ((dt.date.fromisoformat(tgt) - start).days + 1) / 7.0)
            need = total_min / 60.0 / weeks
            info["aviso"] = "Con esta configuración terminarías el %s, después de tu meta (%s). Necesitarías ≈ %.1f horas por semana." % (fin, tgt, need)
        else:
            info["aviso"] = "Con esta configuración terminas el %s, antes de tu meta (%s)." % (fin, tgt)
    return info


def api_schedule_get(conn, q, b):
    items = rows(conn,
                 "SELECT si.*, s.nombre AS materia, s.area_id, m.titulo AS modulo FROM schedule_items si LEFT JOIN subjects s ON s.id=si.subject_id "
                 "LEFT JOIN modules m ON m.id=s.module_id ORDER BY fecha, id")
    cfg = get_setting(conn, "schedule_config", DEFAULT_SCHEDULE)
    pend = [i for i in items if i["status"] == "pending"]
    return {"config": cfg, "items": items, "today": today(),
            "resumen": {"total": len(items), "hechas": sum(1 for i in items if i["status"] == "done"), "pendientes": len(pend),
                        "min_pendientes": sum(i["minutos"] for i in pend), "fin": max([i["fecha"] for i in pend]) if pend else None}}


def api_schedule_generate(conn, q, b):
    cfg = dict(DEFAULT_SCHEDULE, **(b.get("config") or {}))
    if not cfg.get("start_date"):
        cfg["start_date"] = today()
    set_setting(conn, "schedule_config", cfg)
    info = gen_schedule(conn, cfg)
    res = api_schedule_get(conn, q, b)
    res["info"] = info
    return res


def api_schedule_item(conn, q, b):
    iid = int(b["id"])
    it = one(conn, "SELECT * FROM schedule_items WHERE id=?", (iid,))
    if not it:
        raise ValueError("Sesión no encontrada")
    if b.get("delete"):
        conn.execute("DELETE FROM schedule_items WHERE id=?", (iid,))
        return {"ok": True}
    if b.get("fecha"):
        dt.date.fromisoformat(b["fecha"])
        conn.execute("UPDATE schedule_items SET fecha=?, origin=CASE WHEN origin='auto' AND status='pending' THEN 'moved' ELSE origin END WHERE id=?", (b["fecha"], iid))
    if b.get("status") in ("pending", "done", "skipped"):
        conn.execute("UPDATE schedule_items SET status=? WHERE id=?", (b["status"], iid))
        if b["status"] == "done":
            bump(conn)
        if it["tipo"] == "estudio" and it["subject_id"] is not None:
            left = one(conn, "SELECT COUNT(*) n FROM schedule_items WHERE tipo='estudio' AND subject_id=? AND topic_idx=? AND status!='done'", (it["subject_id"], it["topic_idx"]))["n"]
            if b["status"] == "done" and left == 0:
                conn.execute("INSERT INTO topic_progress(subject_id,idx,done,done_at) VALUES(?,?,1,?) ON CONFLICT(subject_id,idx) DO UPDATE SET done=1, done_at=excluded.done_at",
                             (it["subject_id"], it["topic_idx"], now()))
            elif b["status"] == "pending":
                conn.execute("INSERT INTO topic_progress(subject_id,idx,done,done_at) VALUES(?,?,0,NULL) ON CONFLICT(subject_id,idx) DO UPDATE SET done=0, done_at=NULL",
                             (it["subject_id"], it["topic_idx"]))
    return {"ok": True}


def api_schedule_add(conn, q, b):
    f = b.get("fecha") or today()
    dt.date.fromisoformat(f)
    titulo = (b.get("titulo") or "").strip() or "Sesión de estudio"
    conn.execute("INSERT INTO schedule_items(fecha,tipo,subject_id,topic_idx,titulo,minutos,status,origin) VALUES(?,?,?,?,?,?, 'pending','manual')",
                 (f, "manual", b.get("subject_id") or None, None, titulo, int(b.get("minutos") or 30)))
    return {"ok": True}


# ---------------------------------------------------------------- settings / admin
def api_areas_put(conn, q, b):
    for aid, peso in (b.get("weights") or {}).items():
        peso = float(peso)
        if peso < 0 or peso > 100:
            raise ValueError("Los pesos deben estar entre 0 y 100.")
        conn.execute("UPDATE areas SET peso=? WHERE id=?", (peso, aid))
    return {"ok": True}


def api_settings_put(conn, q, b):
    cur = get_setting(conn, "app", DEFAULT_SETTINGS)
    if "umbral" in b:
        u = float(b["umbral"])
        if not 1 <= u <= 100:
            raise ValueError("El umbral debe estar entre 1 y 100.")
        cur["umbral"] = u
    set_setting(conn, "app", cur)
    return cur

# ---------------------------------------------------------------- talleres
ENTREGAS_DIR = os.path.join(os.path.dirname(DB_PATH), "entregas")
MAX_UPLOAD = 15 * 1024 * 1024


def load_talleres():
    p = os.path.join(CONTENT_DIR, "talleres.json")
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _tmap():
    return {t["id"]: t for t in load_talleres()}


def _entrega_row(e):
    e = dict(e)
    e["auto_detail"] = json.loads(e["auto_detail"]) if e.get("auto_detail") else None
    e.pop("path", None)
    return e


def api_talleres(conn, q, b):
    subs = {s["id"]: s["nombre"] for s in rows(conn, "SELECT id, nombre FROM subjects")}
    out = []
    for t in load_talleres():
        es = rows(conn, "SELECT auto_score, claude_nota, estado FROM entregas WHERE ejercicio_id=? ORDER BY id", (t["id"],))
        notas = [e["claude_nota"] for e in es if e["claude_nota"] is not None]
        autos = [e["auto_score"] for e in es if e["auto_score"] is not None]
        out.append({"id": t["id"], "tipo": t["tipo"], "titulo": t["titulo"], "nivel": t["nivel"], "minutos": t["minutos"],
                    "subject_id": t["subject_id"], "materia": subs.get(t["subject_id"], ""), "objetivo": t.get("objetivo", ""),
                    "entregas": len(es), "mejor_nota": max(notas) if notas else None,
                    "mejor_auto": max(autos) if autos else None,
                    "estado": "calificado" if notas else ("entregado" if es else "pendiente")})
    return {"talleres": out}


def api_taller(conn, q, b):
    t = _tmap().get(q.get("id"))
    if not t:
        raise KeyError("taller no existe")
    es = [_entrega_row(e) for e in rows(conn, "SELECT * FROM entregas WHERE ejercicio_id=? ORDER BY id DESC", (t["id"],))]
    reveal = q.get("reveal") == "1" and len(es) > 0
    checks = []
    for c in t.get("checks", []):
        d = {"desc": c["desc"], "puntos": c["puntos"], "tipo": c["tipo"]}
        if reveal and c["tipo"] == "valor":
            d["value"] = c["value"]
            d["pista"] = c.get("pista", "")
        checks.append(d)
    subj = one(conn, "SELECT nombre FROM subjects WHERE id=?", (t["subject_id"],))
    return {"id": t["id"], "tipo": t["tipo"], "titulo": t["titulo"], "nivel": t["nivel"], "minutos": t["minutos"],
            "subject_id": t["subject_id"], "materia": subj["nombre"] if subj else "", "objetivo": t.get("objetivo", ""),
            "enunciado": t["enunciado"], "entrega": t["entrega"], "rubrica": t["rubrica"], "plantilla": t.get("plantilla"),
            "checks": checks, "revelado": reveal, "entregas": es, "puede_revelar": len(es) > 0}


def api_taller_entrega(conn, q, b):
    t = _tmap().get(b.get("id"))
    if not t:
        raise KeyError("taller no existe")
    name = os.path.basename(str(b.get("filename") or "entrega"))
    name = re.sub(r"[^\w.\- ()]", "_", name)[:120] or "entrega"
    raw = base64.b64decode(b.get("data") or "")
    if not raw:
        raise ValueError("archivo vacío")
    if len(raw) > MAX_UPLOAD:
        raise ValueError("archivo mayor a 15 MB")
    d = os.path.join(ENTREGAS_DIR, t["id"])
    os.makedirs(d, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(d, stamp + "_" + name)
    with open(path, "wb") as fh:
        fh.write(raw)
    auto, detail = None, None
    if name.lower().endswith(".xlsx") and t.get("checks"):
        res = xlsxcheck.autocheck(path, t["checks"])
        detail = res
        if res.get("ok"):
            auto = res["score"]
    cur = conn.execute("INSERT INTO entregas(ejercicio_id,filename,path,fecha,auto_score,auto_detail) VALUES(?,?,?,?,?,?)",
                       (t["id"], name, path, now(), auto, json.dumps(detail, ensure_ascii=False) if detail else None))
    bump(conn)
    return {"ok": True, "id": cur.lastrowid, "auto": detail, "ruta": os.path.relpath(path, BASE) if path.startswith(BASE) else path}


def api_taller_calificar(conn, q, b):
    nota = float(b.get("nota"))
    if not 0 <= nota <= 5:
        raise ValueError("la nota debe estar entre 0 y 5")
    eid = b.get("entrega_id")
    if eid is None:
        last = one(conn, "SELECT id FROM entregas WHERE ejercicio_id=? ORDER BY id DESC LIMIT 1", (b.get("id"),))
        if not last:
            raise ValueError("primero registra una entrega")
        eid = last["id"]
    conn.execute("UPDATE entregas SET claude_nota=?, claude_comentarios=?, estado='calificado' WHERE id=?",
                 (nota, str(b.get("comentarios") or "")[:6000], int(eid)))
    return {"ok": True}


def api_taller_borrar(conn, q, b):
    e = one(conn, "SELECT path FROM entregas WHERE id=?", (int(b.get("entrega_id")),))
    if e:
        try:
            os.remove(e["path"])
        except OSError:
            pass
        conn.execute("DELETE FROM entregas WHERE id=?", (int(b.get("entrega_id")),))
    return {"ok": True}



def api_reset(conn, q, b):
    what = b.get("what")
    for t in ("topic_progress", "card_progress", "attempt_answers", "attempts", "schedule_items", "activity", "entregas"):
        conn.execute("DELETE FROM %s" % t)
    if what == "todo":
        conn.execute("DELETE FROM notes")
        conn.execute("DELETE FROM settings")
        conn.execute("DELETE FROM flashcards WHERE origin='user'")
        for aid, nombre, peso, color, orden in AREAS:
            conn.execute("UPDATE areas SET peso=? WHERE id=?", (peso, aid))
    return {"ok": True}


# ---------------------------------------------------------------- HTTP
ROUTES = {
    ("GET", "/api/bootstrap"): api_bootstrap,
    ("GET", "/api/stats"): api_stats,
    ("POST", "/api/topic"): api_topic_toggle,
    ("GET", "/api/lesson"): api_lesson,
    ("GET", "/api/flashcards"): api_cards,
    ("POST", "/api/flashcards/review"): api_card_review,
    ("POST", "/api/flashcards/create"): api_card_create,
    ("POST", "/api/flashcards/delete"): api_card_delete,
    ("POST", "/api/quiz/start"): api_quiz_start,
    ("GET", "/api/quiz/active"): api_quiz_active,
    ("POST", "/api/quiz/answer"): api_quiz_answer,
    ("POST", "/api/quiz/finish"): api_quiz_finish,
    ("POST", "/api/quiz/discard"): api_attempt_discard,
    ("GET", "/api/attempts"): api_attempts,
    ("GET", "/api/schedule"): api_schedule_get,
    ("POST", "/api/schedule/generate"): api_schedule_generate,
    ("POST", "/api/schedule/item"): api_schedule_item,
    ("POST", "/api/schedule/add"): api_schedule_add,
    ("POST", "/api/areas"): api_areas_put,
    ("POST", "/api/settings"): api_settings_put,
    ("GET", "/api/talleres"): api_talleres,
    ("GET", "/api/taller"): api_taller,
    ("POST", "/api/taller/entrega"): api_taller_entrega,
    ("POST", "/api/taller/calificar"): api_taller_calificar,
    ("POST", "/api/taller/borrar"): api_taller_borrar,
    ("POST", "/api/reset"): api_reset,
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if not isinstance(body, (bytes, bytearray)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _handle(self, method):
        url = urlparse(self.path)
        path = url.path
        if not path.startswith("/api/"):
            return self._static(path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        body = {}
        if method == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            if n:
                try:
                    body = json.loads(self.rfile.read(n).decode("utf-8"))
                except Exception:
                    return self._send(400, {"error": "JSON inválido"})
        if path == "/api/backup" and method == "GET":
            return self._backup()
        m = re.match(r"^/api/attempts/(\d+)$", path)
        m2 = re.match(r"^/api/notes/([\w-]+)$", path)
        conn = connect()
        try:
            with _lock:
                if m and method == "GET":
                    res = attempt_detail(conn, int(m.group(1)))
                elif m2 and method == "POST":
                    res = api_notes(conn, m2.group(1), body)
                else:
                    fn = ROUTES.get((method, path))
                    if not fn:
                        return self._send(404, {"error": "No encontrado"})
                    res = fn(conn, q, body)
                conn.commit()
            return self._send(200, res)
        except (ValueError, KeyError, TypeError) as exc:
            conn.rollback()
            return self._send(400, {"error": "Solicitud inválida: %s" % exc})
        except Exception as exc:  # pragma: no cover
            conn.rollback()
            return self._send(500, {"error": "Error interno: %s" % exc})
        finally:
            conn.close()

    def _backup(self):
        tmp = tempfile.mktemp(suffix=".db")
        try:
            src = sqlite3.connect(DB_PATH)
            dst = sqlite3.connect(tmp)
            src.backup(dst)
            dst.close()
            src.close()
            with open(tmp, "rb") as fh:
                data = fh.read()
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        name = "progreso-contaduria-%s.db" % dt.date.today().strftime("%Y%m%d")
        self._send(200, data, "application/octet-stream", {"Content-Disposition": 'attachment; filename="%s"' % name})

    def _static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        full = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip("/")))
        if not full.startswith(STATIC_DIR) or not os.path.isfile(full):
            return self._send(404, b"No encontrado", "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as fh:
            self._send(200, fh.read(), ctype)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


def main():
    init_db()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = "http://localhost:%d" % PORT
    print("=" * 60)
    print(" Plan de estudio · Contaduría Pública (Colombia)")
    print(" Abre:", url)
    print(" Progreso guardado en:", DB_PATH)
    print(" Para detener el servidor: Ctrl+C")
    print("=" * 60)
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido. Tu progreso quedó guardado.")


if __name__ == "__main__":
    main()
