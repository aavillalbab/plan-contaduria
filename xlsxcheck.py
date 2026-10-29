# -*- coding: utf-8 -*-
"""Autorrevisión básica de archivos .xlsx con la librería estándar (sin openpyxl)."""
import zipfile, re, unicodedata
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
IGNORAR = ("datos", "instrucciones")


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn").lower())


def read_book(path):
    """Devuelve {hoja: {'nums': [valores], 'formulas': n, 'sin_cache': n}}"""
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    book = {}
    for sh in wb.find("m:sheets", NS):
        name = sh.get("name")
        tgt = rmap.get(sh.get("{%s}id" % NS["r"]), "")
        tgt = tgt.lstrip("/")
        p = tgt if tgt.startswith("xl/") else "xl/" + tgt
        info = {"nums": [], "formulas": 0, "sin_cache": 0}
        if p in z.namelist():
            root = ET.fromstring(z.read(p))
            for c in root.iter("{%s}c" % NS["m"]):
                f = c.find("m:f", NS)
                v = c.find("m:v", NS)
                t = c.get("t")
                if f is not None:
                    info["formulas"] += 1
                    if v is None or v.text in (None, ""):
                        info["sin_cache"] += 1
                if v is not None and v.text not in (None, "") and t in (None, "n"):
                    try:
                        info["nums"].append(float(v.text))
                    except ValueError:
                        pass
        book[name] = info
    return book


def _hit(nums, value, tol, absolute, alts):
    objetivos = [value] + list(alts or [])
    for x in nums:
        for o in objetivos:
            a, b = (abs(x), abs(o)) if absolute else (x, o)
            if abs(a - b) <= max(tol, 0):
                return True
    return False


def autocheck(path, checks):
    try:
        book = read_book(path)
    except Exception as e:
        return {"ok": False, "error": "No pude leer el archivo como .xlsx (%s). Guárdalo desde Excel/LibreOffice como «Libro de Excel (.xlsx)»." % e}
    util = {n: i for n, i in book.items() if norm(n) not in IGNORAR}
    nmap = {norm(n): n for n in util}
    total = sum(c["puntos"] for c in checks)
    ganados = 0
    det = []
    sin_cache = sum(i["sin_cache"] for i in book.values())
    for c in checks:
        ok, nota = False, ""
        if c["tipo"] == "hojas":
            faltan = [n for n in c["names"] if norm(n) not in nmap]
            ok = not faltan
            if faltan:
                nota = "Faltan hojas: " + ", ".join(faltan)
        elif c["tipo"] == "formulas":
            real = nmap.get(norm(c.get("sheet", "")))
            n = book[real]["formulas"] if real else sum(i["formulas"] for i in util.values())
            ok = n >= c["min"]
            nota = "Encontré %d fórmulas (mínimo %d)." % (n, c["min"])
        elif c["tipo"] == "valor":
            real = nmap.get(norm(c.get("sheet", "")))
            pools = [util[real]["nums"]] if real else []
            pools.append([x for i in util.values() for x in i["nums"]])
            for pool in pools:
                if _hit(pool, c["value"], c.get("tol", 1), c.get("abs", True), c.get("alts")):
                    ok = True
                    break
        if ok:
            ganados += c["puntos"]
        det.append({"desc": c["desc"], "puntos": c["puntos"], "ok": ok, "pista": "" if ok else c.get("pista", ""), "nota": nota if not ok else ""})
    aviso = ""
    if sin_cache:
        aviso = "%d fórmulas no tienen valor guardado: abre el archivo en Excel o LibreOffice, guarda y vuelve a subirlo." % sin_cache
    return {"ok": True, "score": round(100.0 * ganados / total, 1) if total else 0, "ganados": ganados, "total": total, "detalle": det, "aviso": aviso}
