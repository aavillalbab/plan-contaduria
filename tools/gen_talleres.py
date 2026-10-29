# -*- coding: utf-8 -*-
"""Genera content/talleres.json y static/plantillas/*.xlsx. Uso: python3 gen_talleres.py"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_template
import ex_a, ex_b, ex_c

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(ROOT, "static", "plantillas"), exist_ok=True)
out = []
fns = [ex_a.t01, ex_a.t02, ex_a.t03, ex_a.t04, ex_a.t05, ex_b.t06, ex_b.t07, ex_b.t08, ex_b.t09, ex_b.t10,
       ex_c.t11, ex_c.t12, ex_c.t13, ex_c.t14, ex_c.t15, ex_c.t16]
for fn in fns:
    ex, sheets = fn()
    f = ex["id"] + ".xlsx"
    write_template(os.path.join(ROOT, "static", "plantillas", f), ex["titulo"], sheets)
    ex["plantilla"] = f
    out.append(ex)
    print(ex["id"], ex["titulo"], "checks:", len(ex["checks"]), "pts:", sum(c["puntos"] for c in ex["checks"]), "rubrica:", sum(r["puntos"] for r in ex["rubrica"]))
for w in ex_c.trabajos():
    w["plantilla"] = None
    out.append(w)
    print(w["id"], w["titulo"], "rubrica:", sum(r["puntos"] for r in w["rubrica"]))
with open(os.path.join(ROOT, "content", "talleres.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print("OK", len(out))
