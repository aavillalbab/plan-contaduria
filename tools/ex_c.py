# -*- coding: utf-8 -*-
import random
from common import *

UVT_ILUSTRATIVA = 50000


def tabla241(base):
    t = [(1090, 0, 0, 0), (1700, 0.19, 1090, 0), (4100, 0.28, 1700, 116), (8670, 0.33, 4100, 788), (18970, 0.35, 8670, 2296), (31000, 0.37, 18970, 5901), (float("inf"), 0.39, 31000, 10352)]
    prev = 0
    for lim, tasa, desde, fijo in t:
        if base <= lim:
            return (base - desde) * tasa + fijo if tasa else 0
    return 0


# ---------------------------------------------------------------- T11 renta PN
def t11():
    U = UVT_ILUSTRATIVA
    ing, aport = 120000000, 9600000
    dep, viv, prep, afc = 2, 8000000, 3000000, 10000000
    netos = ing - aport
    d_dep = min(dep, 4) * 72 * U
    d_viv = min(viv, 1200 * U)
    d_prep = min(prep, 16 * 12 * U)
    deducs = d_dep + d_viv + d_prep
    afc_e = min(afc, 0.3 * ing, 3800 * U)
    base25 = netos - deducs - afc_e
    ex25 = min(0.25 * base25, 790 * U)
    total = deducs + afc_e + ex25
    limite = min(0.4 * netos, 1340 * U)
    aceptado = min(total, limite)
    rlg = netos - aceptado
    uvt = rlg / U
    imp_uvt = tabla241(uvt)
    imp = imp_uvt * U
    enun = f"""## Contexto
Debes liquidar el **impuesto de renta de una persona natural residente**, empleada, aplicando la tabla del **art. 241 ET** y los límites a rentas exentas y deducciones. *La **UVT es ilustrativa** ({m(U)}) para este ejercicio, y las reglas se **simplifican** para practicar: en una declaración real consulta la UVT y las normas vigentes del año gravable.*

## Datos del contribuyente
{tmd(["Concepto", "Valor"], [["Ingresos brutos laborales del año", m(ing)], ["Aportes obligatorios a salud y pensión (ingreso no constitutivo de renta)", m(aport)], ["Dependientes económicos", f"{dep}"],
 ["Intereses pagados por crédito de vivienda", m(viv)], ["Pagos de medicina prepagada", m(prep)], ["Aportes voluntarios a cuenta AFC (renta exenta)", m(afc)]])}

## Reglas del ejercicio
- **Dependientes:** deducción de **72 UVT** por dependiente (máximo 4).
- **Intereses de vivienda:** deducción con límite de **1.200 UVT** al año.
- **Medicina prepagada:** deducción con límite de **16 UVT mensuales** (192 UVT al año).
- **AFC:** renta exenta con límite del **30%** del ingreso laboral y **3.800 UVT**.
- **Renta exenta del 25%** de los pagos laborales: se calcula sobre (ingresos netos − deducciones − otras rentas exentas) con tope de **790 UVT** al año.
- **Límite global:** rentas exentas + deducciones no pueden exceder el **40%** de los ingresos netos ni **1.340 UVT**.

**Tabla del art. 241 (UVT):**

{tmd(["Rango en UVT", "Tarifa marginal", "Impuesto"], [["0 – 1.090", "0%", "0"], [">1.090 – 1.700", "19%", "(Base − 1.090) × 19%"], [">1.700 – 4.100", "28%", "(Base − 1.700) × 28% + 116"], [">4.100 – 8.670", "33%", "(Base − 4.100) × 33% + 788"],
 [">8.670 – 18.970", "35%", "(Base − 8.670) × 35% + 2.296"], [">18.970 – 31.000", "37%", "(Base − 18.970) × 37% + 5.901"], [">31.000", "39%", "(Base − 31.000) × 39% + 10.352"]])}

## Qué debes hacer
1. Calcula los **ingresos netos**.
2. Calcula cada deducción y renta exenta aplicando sus **límites individuales**.
3. Aplica el **límite global del 40% / 1.340 UVT** y determina la **renta líquida gravable** en pesos y en UVT.
4. Calcula el **impuesto** con la tabla (usa `BUSCAR`/`SI` anidado o una tabla de rangos) y la **tarifa efectiva** sobre el ingreso bruto.
5. Escribe una nota explicando qué rubros quedaron limitados."""
    entrega = "Un **.xlsx** con las hojas **Parámetros**, **Depuración** y **Impuesto**."
    checks = [H(["Parámetros", "Depuración", "Impuesto"], 5),
              V("Ingresos netos", netos, 6, pista="Ingresos brutos − aportes obligatorios."),
              V("Total deducciones imputables (dependientes, vivienda, prepagada)", deducs, 10, pista="144 UVT + intereses vivienda + prepagada (con límites)."),
              V("Renta exenta del 25%", ex25, 12, tol=5, pista="25% × (netos − deducciones − AFC), con tope de 790 UVT."),
              V("Total deducciones y rentas exentas antes del límite", total, 8, pista="Deducciones + AFC + renta exenta del 25%."),
              V("Límite global (40% de los ingresos netos)", limite, 12, pista="Compara 40% de netos con 1.340 UVT: aplica el menor."),
              V("Renta líquida gravable", rlg, 14, pista="Ingresos netos − rentas exentas y deducciones aceptadas."),
              V("Renta líquida gravable en UVT", uvt, 8, tol=0.05, pista="Renta líquida / UVT."),
              V("Impuesto de renta en pesos", imp, 16, tol=50, pista="Segundo rango de la tabla: (UVT − 1.090) × 19%."),
              F("Depuración", 8, 9, "Depuración con fórmulas")]
    rub = [R("Depuración de ingresos y deducciones", 35, "Cada rubro con su límite individual."), R("Límite global", 20, "Aplica el menor entre 40% y 1.340 UVT."), R("Cálculo con la tabla", 25, "Rango y fórmula correctos; resultado en pesos."),
           R("Tarifa efectiva y nota", 10, "Explica rubros limitados."), R("Orden y fórmulas", 10, "Parámetros en celdas y formato claro.")]
    datos = [["UVT ilustrativa", U], [], ["Concepto", "Valor"], ["Ingresos brutos laborales", ing], ["Aportes obligatorios", aport], ["Dependientes", dep], ["Intereses de vivienda", viv], ["Medicina prepagada", prep], ["AFC", afc]]
    sheets = [instr_sheet("Renta de persona natural", ["UVT ilustrativa. Completa Parámetros, Depuración e Impuesto."]), {"name": "Datos", "rows": datos, "widths": [34, 18], "headers": [3], "note": "D97706"},
              blank("Parámetros", ["Parámetro", "Valor"], 15, [40, 18]), blank("Depuración", ["Concepto", "Valor"], 25, [52, 18]), blank("Impuesto", ["Concepto", "Valor"], 15, [40, 18])]
    return dict(id="t11", tipo="excel", titulo="Renta de persona natural: depuración y tabla del art. 241", nivel="Avanzado", minutos=120, subject_id="m4s2",
                objetivo="Depurar la cédula general aplicando límites y liquidar el impuesto con la tabla progresiva.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T12 IVA
def t12():
    ventas = [(12000000, 19), (8500000, 19), (5000000, 5), (3200000, 5), (15000000, 0), (4000000, "E"), (20000000, 19), (6750000, 19), (2500000, "E"), (9000000, 0)]
    compras = [(10000000, 19, "Sí"), (6000000, 19, "Sí"), (4000000, 5, "Sí"), (3000000, 19, "No"), (7500000, 19, "Sí"), (2000000, 19, "No"), (5000000, 0, "Sí")]
    b19 = sum(v for v, t in ventas if t == 19)
    b5 = sum(v for v, t in ventas if t == 5)
    exe = sum(v for v, t in ventas if t == 0)
    exc = sum(v for v, t in ventas if t == "E")
    gen = b19 * 0.19 + b5 * 0.05
    desc = sum(v * t / 100 for v, t, d in compras if d == "Sí")
    nodesc = sum(v * t / 100 for v, t, d in compras if d == "No")
    saldo = gen - desc
    tot_ing = b19 + b5 + exe + exc
    lab = lambda t: "19%" if t == 19 else "5%" if t == 5 else "Exento (0%)" if t == 0 else "Excluido"
    enun = f"""## Contexto
Una empresa comercial lleva el **libro de ventas y el libro de compras** de un período y debe **liquidar el IVA** a pagar o el saldo a favor. Algunas compras **no son descontables** (se usaron en actividades que no dan derecho o son de uso no relacionado con la actividad).

## Datos
**Ventas del período:**

{tmd(["N.º", "Base gravable / valor", "Tratamiento"], [[i + 1, m(v), lab(t)] for i, (v, t) in enumerate(ventas)])}

**Compras del período:**

{tmd(["N.º", "Base", "Tarifa IVA", "¿IVA descontable?"], [[i + 1, m(v), f"{t}%", d] for i, (v, t, d) in enumerate(compras)])}

## Qué debes hacer
1. Elabora el **libro de ventas** con base, tarifa, **IVA generado** y total facturado por documento.
2. Elabora el **libro de compras** con base, IVA y **clasificación** (descontable / no descontable). El IVA no descontable se lleva como mayor valor del costo o gasto.
3. Resume las **bases por tratamiento** (19%, 5%, exentas, excluidas) y el total de ingresos del período.
4. Calcula el **IVA generado**, el **IVA descontable** y el **saldo a pagar** (o a favor).
5. Explica en 3 líneas la diferencia entre **exento** y **excluido** y cómo afectó el resultado."""
    entrega = "Un **.xlsx** con las hojas **Libro de ventas**, **Libro de compras** y **Liquidación IVA**."
    checks = [H(["Libro de ventas", "Libro de compras", "Liquidación IVA"], 5),
              V("Base gravada al 19%", b19, 8, pista="Ventas 1, 2, 7 y 8."),
              V("Base gravada al 5%", b5, 6, pista="Ventas 3 y 4."),
              V("Ingresos por operaciones exentas", exe, 6, pista="Tarifa 0% con derecho a descuento."),
              V("Ingresos por operaciones excluidas", exc, 6, pista="No generan IVA ni dan derecho a descuento."),
              V("Total ingresos del período", tot_ing, 6, pista="Suma de todas las bases."),
              V("IVA generado", gen, 14, pista="19% sobre su base + 5% sobre su base."),
              V("IVA descontable", desc, 16, pista="Solo las compras marcadas como descontables."),
              V("IVA no descontable (mayor costo o gasto)", nodesc, 8, pista="Compras 4 y 6."),
              V("Saldo de IVA a pagar", saldo, 16, pista="IVA generado − IVA descontable."),
              F("Liquidación IVA", 4, 5, "Liquidación con fórmulas"), F("Libro de ventas", 8, 4, "Libro de ventas con fórmulas")]
    rub = [R("Libro de ventas", 20, "IVA por documento y totales."), R("Libro de compras", 25, "Clasificación descontable/no descontable."), R("Liquidación del IVA", 30, "IVA generado, descontable y saldo."),
           R("Exento vs. excluido", 15, "Explicación correcta y aplicada al caso."), R("Orden y fórmulas", 10, "Fórmulas y claridad.")]
    datos = [["Ventas"], ["N.º", "Base", "Tratamiento"]] + [[i + 1, v, lab(t)] for i, (v, t) in enumerate(ventas)] + [[], ["Compras"], ["N.º", "Base", "Tarifa", "¿Descontable?"]] + [[i + 1, v, f"{t}%", d] for i, (v, t, d) in enumerate(compras)]
    sheets = [instr_sheet("Libro de IVA y liquidación", ["Completa Libro de ventas, Libro de compras y Liquidación IVA."]), {"name": "Datos", "rows": datos, "widths": [8, 18, 18, 18], "headers": [2, len(ventas) + 5], "note": "D97706"},
              blank("Libro de ventas", ["N.º", "Base", "Tarifa", "IVA generado", "Total"], 12, [8, 16, 12, 16, 16]), blank("Libro de compras", ["N.º", "Base", "Tarifa", "IVA", "¿Descontable?", "IVA descontable", "IVA no descontable"], 10, [8, 16, 10, 14, 14, 16, 18]),
              blank("Liquidación IVA", ["Concepto", "Valor"], 15, [44, 18])]
    return dict(id="t12", tipo="excel", titulo="Libros de ventas y compras y liquidación del IVA", nivel="Intermedio", minutos=90, subject_id="m4s3",
                objetivo="Llevar libros auxiliares de IVA y liquidar el impuesto del período.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T13 deterioro cartera
def t13():
    tr = [("No vencida", 280000000, 0.01), ("1 a 30 días", 120000000, 0.03), ("31 a 60 días", 60000000, 0.08), ("61 a 90 días", 35000000, 0.20), ("Más de 90 días", 25000000, 0.50)]
    exist = 22000000
    prov = [s * p for _, s, p in tr]
    tot_c = sum(s for _, s, _ in tr)
    tot_p = sum(prov)
    ajuste = tot_p - exist
    cob = tot_p / tot_c
    enun = f"""## Contexto
Al cierre del período, la empresa aplica el **modelo simplificado de pérdida crediticia esperada (NIIF 9)** a sus cuentas por cobrar comerciales usando una **matriz de provisión** por antigüedad.

## Datos
{tmd(["Tramo de antigüedad", "Saldo de cartera", "Tasa de pérdida esperada"], [[a, m(s), f"{p:.0%}"] for a, s, p in tr])}

Provisión (deterioro acumulado) ya registrada al inicio del ajuste: **{m(exist)}**.

## Qué debes hacer
1. Calcula la **provisión requerida** por tramo y en total, y el **porcentaje de cobertura** sobre la cartera total.
2. Calcula el **ajuste** del período (gasto o recuperación) frente a la provisión existente.
3. Escribe el **asiento contable** del ajuste (gasto por deterioro de cartera / deterioro acumulado de cuentas por cobrar).
4. Construye un **gráfico de barras** de saldo vs. provisión por tramo.
5. Responde: ¿qué pasaría con la provisión si la cartera de más de 90 días subiera a $40.000.000? (usa la hoja para simularlo)."""
    entrega = "Un **.xlsx** con las hojas **Matriz**, **Asiento** y **Simulación**."
    sim = tot_p - tr[4][1] * tr[4][2] + 40000000 * tr[4][2]
    checks = [H(["Matriz", "Asiento", "Simulación"], 5),
              V("Total cartera", tot_c, 8, pista="Suma de los cinco tramos."),
              V("Provisión del tramo 31 a 60 días", prov[2], 8, pista="Saldo × 8%."),
              V("Provisión del tramo más de 90 días", prov[4], 8, pista="Saldo × 50%."),
              V("Provisión total requerida", tot_p, 18, pista="Suma de las provisiones por tramo."),
              V("Ajuste del período (gasto por deterioro)", ajuste, 18, pista="Provisión requerida − provisión existente."),
              V("Cobertura sobre la cartera total", cob, 10, tol=0.0005, alts=[cob * 100], pista="Provisión total / cartera total."),
              V("Provisión simulada con 40 millones en el tramo > 90 días", sim, 12, pista="Cambia el saldo del último tramo y recalcula."),
              F("Matriz", 6, 13, "Matriz con fórmulas")]
    rub = [R("Matriz de provisión", 35, "Tasas aplicadas por tramo y total."), R("Ajuste y asiento", 30, "Ajuste y asiento balanceado."), R("Gráfico", 10, "Gráfico legible y rotulado."),
           R("Simulación", 15, "Escenario correcto."), R("Orden y fórmulas", 10, "Parámetros y fórmulas.")]
    datos = [["Tramo", "Saldo", "Tasa"]] + [[a, s, p] for a, s, p in tr] + [[], ["Provisión existente", exist]]
    sheets = [instr_sheet("Deterioro de cartera (NIIF 9)", ["Completa: Matriz, Asiento y Simulación."]), {"name": "Datos", "rows": datos, "widths": [24, 18, 12], "headers": [1], "note": "D97706"},
              blank("Matriz", ["Tramo", "Saldo", "Tasa", "Provisión"], 10, [24, 18, 12, 18]), blank("Asiento", ["Código", "Cuenta", "Débito", "Crédito"], 8, [10, 44, 16, 16]), blank("Simulación", ["Concepto", "Valor"], 10, [40, 18])]
    return dict(id="t13", tipo="excel", titulo="Deterioro de cartera con matriz de provisión (NIIF 9)", nivel="Intermedio", minutos=75, subject_id="m5s2",
                objetivo="Aplicar el modelo simplificado de pérdida esperada y contabilizar el ajuste.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T14 muestreo auditoría
def t14():
    rnd = random.Random(7)
    pob = [rnd.randrange(800, 6000) * 1000 for _ in range(40)]
    diff = {6: 150000, 18: 420000, 30: -80000}  # sobrestimado positivo (libros > verificado)
    audit = [pob[i] - diff.get(i + 1, 0) for i in range(40)]
    idx = list(range(2, 41, 4))
    mb = sum(pob[i - 1] for i in idx)
    ma = sum(audit[i - 1] for i in idx)
    err = mb - ma
    ratio = err / mb
    total = sum(pob)
    proy = ratio * total
    bruto = sum(abs(pob[i - 1] - audit[i - 1]) for i in idx)
    err_items = sum(1 for i in idx if pob[i - 1] != audit[i - 1])
    tol = 1500000
    enun = f"""## Contexto
Eres auditor de una empresa. Debes **probar la existencia y exactitud** de las **40 facturas de ventas por cobrar** del período mediante **muestreo sistemático** y **proyectar el error** a toda la población. Los datos están en la hoja **Datos** de la plantilla (importe en libros e importe verificado por confirmación).

## Parámetros de la prueba
- **Población:** 40 facturas (N.º 1 a 40).
- **Selección sistemática:** toma **1 de cada 4**, comenzando por la factura **N.º 2** (2, 6, 10, …, 38), es decir, **10 ítems**.
- **Error tolerable (materialidad de ejecución):** **{m(tol)}** de error neto proyectado.

## Qué debes hacer
1. Calcula el **total de la población** en libros.
2. Selecciona la muestra y registra, por ítem, el importe en libros, el verificado y la **diferencia** (sobreestimación = libros > verificado).
3. Calcula el **error neto en la muestra**, el **error bruto** (suma de valores absolutos), el **número de ítems con error** y la **razón de error** (error neto / importe de la muestra).
4. **Proyecta el error** a la población (razón × total población).
5. Compara con el error tolerable y redacta la **conclusión del auditor** y qué procedimientos adicionales propondrías."""
    entrega = "Un **.xlsx** con las hojas **Población**, **Muestra** y **Conclusión**."
    checks = [H(["Población", "Muestra", "Conclusión"], 5),
              V("Total de la población en libros", total, 10, pista="Suma de las 40 facturas."),
              V("Importe en libros de la muestra", mb, 12, pista="Suma de las facturas 2, 6, 10, …, 38."),
              V("Error neto en la muestra", err, 14, pista="Libros − verificado (sobreestimaciones menos subestimaciones)."),
              V("Error bruto en la muestra", bruto, 10, pista="Suma de las diferencias en valor absoluto."),
              V("Ítems con error en la muestra", err_items, 8, tol=0.01, pista="Cuenta cuántas diferencias son distintas de cero."),
              V("Razón de error de la muestra", ratio, 10, tol=0.0002, alts=[ratio * 100], pista="Error neto / importe de la muestra."),
              V("Error neto proyectado a la población", proy, 18, tol=50, pista="Razón de error × total de la población."),
              F("Muestra", 8, 8, "Muestra con fórmulas (BUSCARV/INDICE)"), F("Población", 3, 5, "Población con fórmulas")]
    rub = [R("Selección de la muestra", 20, "Aplica 1 de cada 4 desde la factura 2."), R("Cálculo de errores", 25, "Neto, bruto y razón correctos."), R("Proyección", 20, "Proyecta a la población."),
           R("Conclusión del auditor", 25, "Compara con el error tolerable y propone procedimientos."), R("Papeles de trabajo", 10, "Referencias, marcas y orden.")]
    datos = [["N.º", "Cliente", "Importe en libros", "Importe verificado"]] + [[i + 1, f"Cliente {i + 1:02d}", pob[i], audit[i]] for i in range(40)]
    sheets = [instr_sheet("Muestreo de auditoría", ["Completa: Población, Muestra y Conclusión."]), {"name": "Datos", "rows": datos, "widths": [8, 16, 18, 18], "headers": [1], "freeze": "A2", "note": "D97706"},
              blank("Población", ["N.º", "Importe en libros"], 42, [8, 18]), blank("Muestra", ["N.º", "Libros", "Verificado", "Diferencia"], 12, [8, 16, 16, 16]), blank("Conclusión", ["Concepto", "Valor"], 12, [44, 18])]
    ex = dict(id="t14", tipo="excel", titulo="Papeles de trabajo de auditoría: muestreo y proyección del error", nivel="Avanzado", minutos=100, subject_id="m6s1",
              objetivo="Seleccionar una muestra, evaluar diferencias y proyectar el error a la población.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks)
    return ex, sheets


# ---------------------------------------------------------------- T15 consolidación
def t15():
    A = dict(caja=200, cxc=300, inv=250, inversion=480, ppe=1000, prov=400, obl=700, pat=1130)
    B = dict(caja=60, cxc=140, inv=200, ppe=400, prov=180, obl=120, pat=500)
    assert sum(A[k] for k in ("caja", "cxc", "inv", "inversion", "ppe")) == A["prov"] + A["obl"] + A["pat"]
    assert sum(B[k] for k in ("caja", "cxc", "inv", "ppe")) == B["prov"] + B["obl"] + B["pat"]
    pct, pnc_pct = 0.8, 0.2
    pnc = B["pat"] * pnc_pct
    gw = A["inversion"] + pnc - B["pat"]
    interco = 15
    cons = dict(caja=A["caja"] + B["caja"], cxc=A["cxc"] + B["cxc"] - interco, inv=A["inv"] + B["inv"], ppe=A["ppe"] + B["ppe"], gw=gw)
    ta = sum(cons.values())
    prov = A["prov"] + B["prov"] - interco
    obl = A["obl"] + B["obl"]
    pat_total = A["pat"] + pnc
    assert abs(ta - (prov + obl + pat_total)) < 1e-9
    enun = f"""## Contexto
La sociedad **A** adquirió el **80%** de las acciones de **B** en la fecha de adquisición por **{A['inversion']:,} millones**. Los activos netos identificables de B a valor razonable son iguales a su patrimonio contable (**{B['pat']:,} millones**). Debes elaborar el **estado de situación financiera consolidado** de la fecha de adquisición (NIIF 10 y NIIF 3). Cifras en **millones de pesos**.

## Datos
{tmd(["Cuenta", "A (matriz)", "B (subsidiaria)"], [["Caja", A['caja'], B['caja']], ["Cuentas por cobrar", A['cxc'], B['cxc']], ["Inventarios", A['inv'], B['inv']], ["Inversión en B", A['inversion'], "—"], ["Propiedad, planta y equipo", A['ppe'], B['ppe']],
 ["Proveedores", A['prov'], B['prov']], ["Obligaciones financieras", A['obl'], B['obl']], ["Patrimonio", A['pat'], B['pat']]])}

**Operaciones intragrupo:** las cuentas por cobrar de A incluyen **{interco} millones** que le debe B (registrados en proveedores de B).

## Qué debes hacer
1. Calcula la **participación no controladora (PNC)** y la **plusvalía** en la adquisición.
2. Elabora la **hoja de trabajo de consolidación**: columnas A, B, **eliminaciones/ajustes** (débitos y créditos) y **consolidado**.
3. Registra las eliminaciones: la **inversión de A contra el patrimonio de B**, el reconocimiento de la **PNC y la plusvalía**, y la **cuenta por cobrar/pagar intragrupo**.
4. Presenta el **estado de situación financiera consolidado** y verifica que **activos = pasivos + patrimonio**.
5. Explica en 3 líneas qué significa la PNC y por qué la plusvalía no se amortiza en NIIF plenas."""
    entrega = "Un **.xlsx** con las hojas **Hoja de trabajo** y **Consolidado**."
    checks = [H(["Hoja de trabajo", "Consolidado"], 5),
              V("Participación no controladora (millones)", pnc, 14, tol=0.01, pista="20% × patrimonio de B (valor razonable de activos netos)."),
              V("Plusvalía (millones)", gw, 20, tol=0.01, pista="Contraprestación + PNC − activos netos identificables."),
              V("Cuentas por cobrar consolidadas", cons["cxc"], 10, tol=0.01, pista="Suma menos la cuenta intragrupo."),
              V("Proveedores consolidados", prov, 10, tol=0.01, pista="Suma menos la cuenta intragrupo."),
              V("Total activos consolidados", ta, 14, tol=0.01, pista="Sin la inversión en B; con la plusvalía."),
              V("Patrimonio total consolidado (incluye PNC)", pat_total, 12, tol=0.01, pista="Patrimonio de A + PNC."),
              V("Patrimonio atribuible a la controladora", A["pat"], 6, tol=0.01, pista="Patrimonio de A."),
              F("Consolidado", 6, 9, "Consolidado con fórmulas")]
    rub = [R("PNC y plusvalía", 25, "Cálculo correcto con la fórmula de NIIF 3."), R("Eliminaciones", 30, "Eliminación de inversión y saldos intragrupo con partida doble."), R("Estado consolidado", 25, "Rubros y totales correctos; cuadre."),
           R("Explicación conceptual", 10, "PNC y plusvalía."), R("Orden y fórmulas", 10, "Hoja de trabajo clara.")]
    datos = [["Cuenta", "A", "B"], ["Caja", A["caja"], B["caja"]], ["Cuentas por cobrar", A["cxc"], B["cxc"]], ["Inventarios", A["inv"], B["inv"]], ["Inversión en B", A["inversion"], None], ["PPE", A["ppe"], B["ppe"]],
             ["Proveedores", A["prov"], B["prov"]], ["Obligaciones financieras", A["obl"], B["obl"]], ["Patrimonio", A["pat"], B["pat"]], [], ["Participación de A en B", pct], ["Saldo intragrupo (A por cobrar a B)", interco]]
    sheets = [instr_sheet("Estados financieros consolidados", ["Cifras en millones. Completa Hoja de trabajo y Consolidado."]), {"name": "Datos", "rows": datos, "widths": [34, 12, 12], "headers": [1], "note": "D97706"},
              blank("Hoja de trabajo", ["Cuenta", "A", "B", "Eliminaciones Dr", "Eliminaciones Cr", "Consolidado"], 15, [30, 12, 12, 16, 16, 14]), blank("Consolidado", ["Concepto", "Valor"], 20, [40, 14])]
    return dict(id="t15", tipo="excel", titulo="Consolidación de estados financieros: plusvalía y PNC", nivel="Avanzado", minutos=120, subject_id="m5s4",
                objetivo="Elaborar la hoja de trabajo de consolidación aplicando NIIF 10 y NIIF 3.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T16 caja menor
def t16():
    fondo = 800000
    vou = [("Papelería", 85000), ("Transporte", 62000), ("Cafetería", 118000), ("Fotocopias", 45000), ("Correo y mensajería", 36000), ("Aseo", 74000), ("Reparaciones locativas", 150000)]
    tot = sum(v for _, v in vou)
    esperado = fondo - tot
    contado = 218000
    falt = esperado - contado
    reemb = fondo - contado
    assert reemb == tot + falt
    enun = f"""## Contexto
La empresa maneja un **fondo fijo de caja menor** de **{m(fondo)}**. Al cierre debes elaborar el **arqueo**, registrar los gastos con sus comprobantes y calcular el **reembolso** que se solicita a tesorería.

## Datos
**Comprobantes de gasto del período:**

{tmd(["N.º", "Concepto", "Valor"], [[i + 1, c, m(v)] for i, (c, v) in enumerate(vou)])}

**Efectivo contado en el arqueo:** **{m(contado)}**. Cualquier **faltante** se registra como **cuenta por cobrar al responsable del fondo**.

## Qué debes hacer
1. Elabora el **libro de caja menor** (fecha, concepto, ingreso, egreso, saldo).
2. Elabora el **arqueo**: fondo, comprobantes, efectivo esperado, efectivo contado y diferencia.
3. Calcula el **valor del reembolso** para dejar el fondo en su valor fijo.
4. Escribe el **asiento de reembolso** (gastos por concepto, cuenta por cobrar por el faltante, y la salida de bancos).
5. Calcula el **porcentaje del fondo consumido** y comenta si el monto del fondo es adecuado."""
    entrega = "Un **.xlsx** con las hojas **Libro de caja menor**, **Arqueo** y **Reembolso**."
    checks = [H(["Libro de caja menor", "Arqueo", "Reembolso"], 5),
              V("Total de gastos con comprobante", tot, 14, pista="Suma de los 7 comprobantes."),
              V("Efectivo que debería haber en caja", esperado, 16, pista="Fondo − gastos con comprobante."),
              V("Faltante del arqueo", falt, 18, pista="Efectivo esperado − efectivo contado."),
              V("Valor del reembolso", reemb, 20, pista="Fondo − efectivo contado (gastos + faltante)."),
              V("Porcentaje del fondo consumido", tot / fondo, 8, tol=0.001, alts=[tot / fondo * 100], pista="Gastos / fondo."),
              F("Arqueo", 3, 11, "Arqueo con fórmulas"), F("Libro de caja menor", 6, 8, "Libro de caja con fórmulas")]
    rub = [R("Libro de caja menor", 25, "Registro ordenado con saldo."), R("Arqueo", 30, "Efectivo esperado, contado y diferencia."), R("Reembolso y asiento", 30, "Valor y asiento balanceado."),
           R("Análisis del fondo", 5, "Opina sobre la suficiencia del fondo."), R("Orden y fórmulas", 10, "Presentación.")]
    datos = [["Fondo fijo", fondo], ["Efectivo contado", contado], [], ["N.º", "Concepto", "Valor"]] + [[i + 1, c, v] for i, (c, v) in enumerate(vou)]
    sheets = [instr_sheet("Caja menor y arqueo", ["Completa: Libro de caja menor, Arqueo y Reembolso."]), {"name": "Datos", "rows": datos, "widths": [20, 28, 14], "headers": [4], "note": "D97706"},
              blank("Libro de caja menor", ["Fecha", "Concepto", "Ingreso", "Egreso", "Saldo"], 12, [12, 32, 14, 14, 14]), blank("Arqueo", ["Concepto", "Valor"], 10, [40, 16]), blank("Reembolso", ["Código", "Cuenta", "Débito", "Crédito"], 12, [10, 40, 14, 14])]
    return dict(id="t16", tipo="excel", titulo="Caja menor: libro, arqueo y reembolso", nivel="Básico", minutos=60, subject_id="m2s1",
                objetivo="Llevar el libro de caja menor y controlar el efectivo con un arqueo.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- trabajos escritos
def trabajos():
    out = []
    out.append(dict(id="w01", tipo="trabajo", titulo="Informe de análisis financiero para la gerencia", nivel="Intermedio", minutos=120, subject_id="m3s4",
        objetivo="Comunicar hallazgos financieros a un público no contable.",
        enunciado="""## Contexto
Eres el contador de **Comercial Andina S.A.S.** (usa los datos del **Taller T9**: estados y razones de los Años 1 y 2). El gerente no es contador y te pide un **informe ejecutivo** para decidir si solicita un **crédito de $400 millones** para ampliar bodega.

## Qué debes hacer
1. Resume en un párrafo la **situación general** (crecimiento, rentabilidad, liquidez y endeudamiento).
2. Incluye al menos **3 tablas o gráficos** con razones clave de ambos años y su interpretación.
3. Aplica **DuPont** para explicar qué impulsó el cambio del ROE.
4. Identifica **2 fortalezas y 2 riesgos** y sustenta con cifras.
5. Concluye con una **recomendación** sobre el crédito (sí/no/condicionado) y **3 acciones** concretas.

## Formato
Documento **Word o PDF**, de **2 a 3 páginas**, con portada simple, lenguaje claro y las cifras citadas con su fuente (hoja y celda de tu taller T9).""",
        entrega="Un archivo **.docx** o **.pdf** de 2 a 3 páginas.",
        rubrica=[R("Síntesis y claridad", 20, "Un gerente no contable entiende la situación en un minuto."), R("Uso correcto de razones", 25, "Cifras correctas y bien interpretadas."), R("DuPont", 15, "Explica los factores del cambio del ROE."),
                 R("Riesgos y fortalezas", 15, "Sustentados con datos."), R("Recomendación", 15, "Decisión argumentada y acciones concretas."), R("Redacción y presentación", 10, "Ortografía, formato y extensión.")], checks=[]))
    out.append(dict(id="w02", tipo="trabajo", titulo="Caso de ética profesional: presión del gerente", nivel="Básico", minutos=90, subject_id="m1s4",
        objetivo="Aplicar la Ley 43 de 1990 y los principios éticos a un dilema real.",
        enunciado="""## Caso
Eres contador público y llevas la contabilidad de una S.A.S. mediana. Al cierre del año, el gerente general te pide que **no reconozcas una provisión por un litigio laboral** cuya pérdida es probable (los abogados estiman $180 millones) porque «afectaría el crédito que estamos tramitando con el banco». Además, te solicita **fechar al 31 de diciembre** unas facturas de venta que en realidad se expidieron el 8 de enero. Te recuerda que él te paga los honorarios y que «otros contadores sí colaboran».

## Qué debes hacer
1. Identifica los **hechos relevantes** y los **riesgos** para ti, la empresa y terceros.
2. Analiza cada petición a la luz de los **principios éticos** (integridad, objetividad, independencia, responsabilidad, confidencialidad, competencia, etc.) y de la **Ley 43 de 1990** (fe pública).
3. Explica qué **normas de información financiera** estarían incumplidas (provisiones y corte de ingresos).
4. Describe tu **plan de acción** paso a paso (qué dirías, a quién escalarías, cómo dejarías evidencia y cuándo renunciarías).
5. Redacta un **breve mensaje al gerente** (máx. 150 palabras) explicando tu posición con respeto.

## Formato
Documento Word o PDF de **600 a 900 palabras**.""",
        entrega="Un archivo **.docx** o **.pdf** de 600 a 900 palabras.",
        rubrica=[R("Identificación de hechos y riesgos", 15, "Completa y ordenada."), R("Aplicación de principios y Ley 43", 30, "Cita y aplica los principios pertinentes."), R("Normas contables incumplidas", 15, "Provisión y corte de ingresos."),
                 R("Plan de acción", 20, "Realista, con evidencia y escalamiento."), R("Mensaje al gerente", 10, "Firme, claro y respetuoso."), R("Redacción", 10, "Claridad y extensión.")], checks=[]))
    out.append(dict(id="w03", tipo="trabajo", titulo="Memorando tributario: IVA exento vs. excluido", nivel="Avanzado", minutos=120, subject_id="m4s3",
        objetivo="Emitir un concepto técnico fundamentado sobre un caso de IVA.",
        enunciado="""## Caso
**Alimentos del Valle S.A.S.** produce y vende tres líneas: (1) **conservas** gravadas con IVA; (2) un **producto cuya venta está excluida** de IVA; (3) un producto que **exporta** (exento). Compra insumos y servicios comunes a las tres líneas y tiene dudas: ¿puede descontar todo el IVA que paga en sus compras? ¿Cómo se trata el IVA de los insumos de la línea excluida? ¿Qué pasa con el saldo a favor generado por las exportaciones?

## Qué debes hacer
Redacta un **memorando** dirigido a la gerencia financiera con la estructura: **Hechos · Problema jurídico · Marco normativo (cita las normas que consultes, verificando su vigencia) · Análisis · Conclusión y recomendaciones**. Incluye una **tabla comparativa** exento vs. excluido y un **ejemplo numérico** (con cifras ilustrativas) de IVA descontable, proporcionalidad y saldo a favor.

## Formato
Word o PDF de **2 a 3 páginas**. Cita tus fuentes (Estatuto Tributario, doctrina DIAN, etc.) y marca claramente lo que debe verificarse con la norma vigente.""",
        entrega="Un archivo **.docx** o **.pdf** de 2 a 3 páginas.",
        rubrica=[R("Hechos y problema jurídico", 15, "Bien planteados."), R("Marco normativo y citas", 25, "Normas pertinentes y vigencia verificada."), R("Análisis de exento vs. excluido", 25, "Efectos sobre descuento y devolución."),
                 R("Ejemplo numérico", 15, "Cifras coherentes con la teoría."), R("Conclusión y recomendaciones", 10, "Prácticas y concretas."), R("Estructura y redacción", 10, "Memorando profesional.")], checks=[]))
    out.append(dict(id="w04", tipo="trabajo", titulo="Informe de control interno (COSO) sobre un caso de tesorería y compras", nivel="Intermedio", minutos=120, subject_id="m6s3",
        objetivo="Detectar deficiencias de control y proponer mejoras bajo COSO.",
        enunciado="""## Caso
En una distribuidora de repuestos se observa lo siguiente: (a) **una misma persona** recibe los pagos de clientes, los registra, hace la conciliación bancaria y lleva los depósitos al banco; (b) las **compras se aprueban verbalmente** y no se exigen tres cotizaciones; (c) el **inventario** se cuenta una vez al año y las diferencias se ajustan sin revisión; (d) todos los usuarios del sistema contable comparten **la misma clave** de administrador; (e) no existe **código de conducta** ni línea de reporte de irregularidades; (f) la gerencia **no revisa** indicadores mensuales.

## Qué debes hacer
1. Elabora una **matriz** con columnas: deficiencia · riesgo · **componente COSO** relacionado · tipo de control faltante (preventivo/detectivo/correctivo) · **recomendación** · prioridad (alta/media/baja) y responsable sugerido.
2. Explica el concepto de **segregación de funciones** y propone cómo reorganizar el caso (a).
3. Propone **3 indicadores o controles de monitoreo** para la gerencia.
4. Redacta un **resumen ejecutivo** de media página para la junta.

## Formato
Word, PDF o Excel (la matriz en Excel y el resumen en Word son aceptables).""",
        entrega="Archivo(s) **.docx**, **.pdf** o **.xlsx** (matriz + resumen ejecutivo).",
        rubrica=[R("Identificación de deficiencias y riesgos", 25, "Las 6 situaciones con su riesgo."), R("Clasificación COSO y tipo de control", 20, "Componentes y tipos correctos."), R("Recomendaciones", 25, "Viables y priorizadas."),
                 R("Segregación de funciones", 10, "Propuesta clara."), R("Indicadores de monitoreo", 10, "Relevantes y medibles."), R("Resumen ejecutivo", 10, "Claro y breve.")], checks=[]))
    return out
