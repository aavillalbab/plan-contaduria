# -*- coding: utf-8 -*-
from common import *


# ---------------------------------------------------------------- T6 nómina
def t06():
    SMM, AUX = 1500000, 200000
    emp = [("Ana Ruiz", 1500000), ("Luis Mora", 2800000), ("Marta Pinto", 3600000), ("Jorge Silva", 6000000)]
    res = []
    for nom, sal in emp:
        aux = AUX if sal <= 2 * SMM else 0
        dev = sal + aux
        salud, pen = sal * 0.04, sal * 0.04
        fsp = sal * 0.01 if sal >= 4 * SMM else 0
        ded = salud + pen + fsp
        neto = dev - ded
        ap_pen, ap_arl, ap_caja = sal * 0.12, sal * 0.00522, sal * 0.04
        aportes = ap_pen + ap_arl + ap_caja
        ces = dev / 12
        intc = ces * 0.01
        prima = dev / 12
        vac = sal / 24
        prov = ces + intc + prima + vac
        res.append(dict(nom=nom, sal=sal, aux=aux, dev=dev, ded=ded, neto=neto, aportes=aportes, prov=prov, costo=dev + aportes + prov))
    tot = {k: sum(r[k] for r in res) for k in ("dev", "ded", "neto", "aportes", "prov", "costo")}
    enun = f"""## Contexto
Debes liquidar la **nómina mensual** de una empresa con 4 empleados, con sus aportes y provisiones de prestaciones. *Los valores del salario mínimo y del auxilio de transporte son **ilustrativos** para este ejercicio; en un caso real usa los vigentes. Las reglas se simplifican para practicar.*

## Parámetros
{tmd(["Parámetro", "Valor / regla"], [["SMMLV ilustrativo", m(SMM)], ["Auxilio de transporte ilustrativo", m(AUX) + " (si el salario es ≤ 2 SMMLV)"],
 ["Descuentos al empleado", "Salud 4% y pensión 4% sobre el salario; fondo de solidaridad pensional 1% si el salario es ≥ 4 SMMLV"],
 ["Aportes del empleador", "Pensión 12%, ARL 0,522% (riesgo I, ilustrativo) y caja de compensación 4%, sobre el salario"],
 ["Exoneración", "Salud del empleador, SENA e ICBF exonerados (todos los salarios son < 10 SMMLV)"],
 ["Provisiones mensuales", "Cesantías = (salario + auxilio)/12 · Intereses sobre cesantías = 1% de las cesantías del mes · Prima = (salario + auxilio)/12 · Vacaciones = salario × 15/360"],
 ["Base del auxilio", "El auxilio no hace parte de la base de aportes ni de vacaciones; sí de cesantías y prima"]])}

**Empleados (30 días trabajados):**

{tmd(["Empleado", "Salario mensual"], [[n, m(s)] for n, s in emp])}

## Qué debes hacer
1. Elabora la **planilla de nómina**: salario, auxilio, devengado, descuentos y **neto a pagar** de cada empleado.
2. Calcula los **aportes del empleador** por empleado y en total.
3. Calcula las **provisiones de prestaciones** (cesantías, intereses, prima y vacaciones).
4. Calcula el **costo total mensual** para la empresa (devengado + aportes + provisiones).
5. Escribe el **asiento contable** de causación de la nómina (gastos de personal, deducciones por pagar, salarios por pagar, aportes y provisiones)."""
    entrega = "Un **.xlsx** con las hojas **Nómina**, **Aportes y provisiones** y **Asiento**. Parametriza porcentajes en celdas."
    checks = [H(["Nómina", "Aportes y provisiones", "Asiento"], 5),
              V("Neto a pagar de Ana Ruiz", res[0]["neto"], 8, tol=5, pista="Salario + auxilio − 4% − 4%."),
              V("Neto a pagar de Jorge Silva (incluye FSP)", res[3]["neto"], 10, tol=5, pista="No recibe auxilio y paga 1% adicional al fondo de solidaridad."),
              V("Total devengado", tot["dev"], 8, tol=5, pista="Suma de salarios + auxilios."),
              V("Total descuentos a empleados", tot["ded"], 10, tol=10, pista="Salud, pensión y FSP."),
              V("Total neto a pagar", tot["neto"], 8, tol=10, pista="Devengado − descuentos."),
              V("Total aportes del empleador", tot["aportes"], 14, tol=20, pista="Pensión 12% + ARL + caja 4% sobre salarios."),
              V("Total provisiones de prestaciones", tot["prov"], 14, tol=20, pista="Cesantías, intereses, prima y vacaciones."),
              V("Costo total mensual para la empresa", tot["costo"], 12, tol=30, pista="Devengado + aportes + provisiones."),
              F("Nómina", 12, 11, "Fórmulas en la planilla de nómina")]
    rub = [R("Planilla de nómina", 30, "Devengado, auxilio, descuentos y neto por empleado."), R("Aportes", 20, "Porcentajes y bases correctos con la exoneración."), R("Provisiones", 20, "Cesantías, intereses, prima y vacaciones con sus bases."),
           R("Asiento contable", 20, "Cuentas adecuadas y partida doble."), R("Parametrización y orden", 10, "Porcentajes en celdas y formato claro.")]
    datos = [["SMMLV ilustrativo", SMM], ["Auxilio de transporte ilustrativo", AUX], [], ["Empleado", "Salario"]] + [[n, s] for n, s in emp]
    sheets = [instr_sheet("Nómina, aportes y provisiones", ["Completa: Nómina, Aportes y provisiones y Asiento."]), {"name": "Datos", "rows": datos, "widths": [34, 16], "headers": [4], "note": "D97706"},
              blank("Nómina", ["Empleado", "Salario", "Auxilio", "Devengado", "Salud 4%", "Pensión 4%", "FSP 1%", "Total descuentos", "Neto a pagar"], 8, [20] + [14] * 8),
              blank("Aportes y provisiones", ["Empleado", "Pensión 12%", "ARL", "Caja 4%", "Total aportes", "Cesantías", "Intereses", "Prima", "Vacaciones", "Total provisiones", "Costo total"], 8, [20] + [14] * 10),
              blank("Asiento", ["Código", "Cuenta", "Débito", "Crédito"], 15, [10, 44, 16, 16])]
    return dict(id="t06", tipo="excel", titulo="Nómina, aportes y provisiones de prestaciones", nivel="Intermedio", minutos=100, subject_id="m7s1",
                objetivo="Liquidar nómina y calcular el costo laboral total de una empresa.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T7 costos
def t07():
    cif_p, h_p = 18000000, 1500
    tarifa = cif_p / h_p
    mod_h = 9000
    ords = [("101", "10 escritorios", 3200000, 120, 10), ("102", "8 bibliotecas", 5100000, 200, 8), ("103", "5 mesas de comedor", 2450000, 90, 5)]
    calc = []
    for o, d, mpd, h, u in ords:
        mod = h * mod_h
        cif = h * tarifa
        tot = mpd + mod + cif
        calc.append(dict(o=o, d=d, mpd=mpd, h=h, u=u, mod=mod, cif=cif, tot=tot, unit=tot / u))
    cif_apl = sum(c["cif"] for c in calc)
    cif_real = 5050000
    sub = cif_real - cif_apl
    price, cv, cf = 1500000, 900000, 24000000
    mc = price - cv
    pe_u = cf / mc
    pe_p = pe_u * price
    util_obj = 18000000
    u_obj = (cf + util_obj) / mc
    enun = f"""## Contexto
Una carpintería usa **costeo por órdenes de producción** con **tasa predeterminada de CIF**. Además, para uno de sus productos quiere conocer el **punto de equilibrio**.

## Parte A: costeo por órdenes
- CIF presupuestados del año: **{m(cif_p)}**; horas de MOD presupuestadas: **{h_p:,}**. La base de aplicación son las **horas de MOD**.
- Tarifa de MOD: **{m(mod_h)}** por hora.
- CIF **reales** incurridos en el período: **{m(cif_real)}**.

{tmd(["Orden", "Producto", "Materia prima directa", "Horas MOD", "Unidades"], [[o, d, m(mpd), h, u] for o, d, mpd, h, u in ords])}

## Parte B: punto de equilibrio
Producto "silla ejecutiva": precio de venta **{m(price)}**, costo variable unitario **{m(cv)}**, costos fijos mensuales **{m(cf)}**.

## Qué debes hacer
1. Calcula la **tasa predeterminada de CIF** y elabora la **hoja de costos** de cada orden (MPD, MOD, CIF aplicados, costo total y costo unitario).
2. Calcula los **CIF aplicados** del período y la **sub o sobreaplicación** frente a los reales; indica cómo la ajustarías contablemente.
3. Calcula el **margen de contribución**, el **punto de equilibrio en unidades y en pesos** y las unidades necesarias para una **utilidad de {m(util_obj)}**.
4. Construye un **gráfico** de ingresos totales vs. costos totales que muestre el punto de equilibrio.
5. Calcula el margen de seguridad si se venden **65 unidades**."""
    entrega = "Un **.xlsx** con las hojas **Órdenes**, **CIF** y **Equilibrio** (con el gráfico)."
    checks = [H(["Órdenes", "CIF", "Equilibrio"], 5),
              V("Tasa predeterminada de CIF por hora", tarifa, 8, pista="CIF presupuestados / horas presupuestadas."),
              V("Costo total de la orden 101", calc[0]["tot"], 8, pista="MPD + MOD (120 h) + CIF aplicados."),
              V("Costo unitario de la orden 102", calc[1]["unit"], 8, pista="Costo total de la orden / 8 unidades."),
              V("Costo total de la orden 103", calc[2]["tot"], 8, pista="MPD + MOD (90 h) + CIF aplicados."),
              V("CIF aplicados del período", cif_apl, 10, pista="410 horas × tarifa."),
              V("CIF subaplicados", sub, 10, pista="CIF reales − CIF aplicados (positivo = subaplicación)."),
              V("Margen de contribución unitario", mc, 6, pista="Precio − costo variable unitario."),
              V("Punto de equilibrio en unidades", pe_u, 8, pista="Costos fijos / margen de contribución."),
              V("Punto de equilibrio en pesos", pe_p, 8, pista="Unidades de equilibrio × precio."),
              V("Unidades para utilidad objetivo", u_obj, 10, pista="(Costos fijos + utilidad) / margen de contribución."),
              F("Órdenes", 10, 7, "Fórmulas en las hojas de costos"), F("Equilibrio", 4, 5, "Fórmulas en el análisis de equilibrio")]
    rub = [R("Hojas de costos por orden", 30, "MPD, MOD y CIF aplicados correctamente por orden."), R("Tasa y sub/sobreaplicación", 20, "Tasa predeterminada y ajuste explicado."),
           R("Punto de equilibrio", 25, "Cálculo en unidades, pesos y utilidad objetivo."), R("Gráfico y margen de seguridad", 15, "Gráfico legible; margen de seguridad correcto."),
           R("Orden y fórmulas", 10, "Parametrización y claridad.")]
    datos = [["CIF presupuestados", cif_p], ["Horas MOD presupuestadas", h_p], ["Tarifa MOD por hora", mod_h], ["CIF reales", cif_real], [], ["Orden", "Producto", "MPD", "Horas MOD", "Unidades"]] + [[o, d, mpd, h, u] for o, d, mpd, h, u in ords] + \
            [[], ["Precio", price], ["Costo variable unitario", cv], ["Costos fijos mensuales", cf]]
    sheets = [instr_sheet("Costos por órdenes y punto de equilibrio", ["Completa: Órdenes, CIF y Equilibrio (con gráfico)."]), {"name": "Datos", "rows": datos, "widths": [28, 22, 16, 12, 12], "headers": [6], "note": "D97706"},
              blank("Órdenes", ["Orden", "MPD", "Horas MOD", "MOD", "CIF aplicados", "Costo total", "Unidades", "Costo unitario"], 6, [10, 16, 12, 16, 16, 16, 10, 16]),
              blank("CIF", ["Concepto", "Valor"], 10, [40, 18]), blank("Equilibrio", ["Concepto", "Valor"], 14, [40, 18])]
    return dict(id="t07", tipo="excel", titulo="Costos por órdenes (CIF predeterminado) y punto de equilibrio", nivel="Intermedio", minutos=100, subject_id="m3s1",
                objetivo="Costear órdenes de producción y analizar el equilibrio costo-volumen-utilidad.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T8 presupuesto
def t08():
    price = 50000
    uni = {"Ene": 1000, "Feb": 1200, "Mar": 1500, "Abr": 1300}
    inv0 = 200
    meses = ["Ene", "Feb", "Mar"]
    sig = {"Ene": "Feb", "Feb": "Mar", "Mar": "Abr"}
    prod = {}
    inv_prev = inv0
    for mes in meses:
        fin = 0.2 * uni[sig[mes]]
        prod[mes] = uni[mes] + fin - inv_prev
        inv_prev = fin
    mat_u = 12000
    mod_u = 5000
    comp = {mes: prod[mes] * mat_u for mes in meses}
    cobr, pagos, netos, caja = {}, {}, {}, {}
    rec_dic, pag_dic, c0 = 18000000, 9000000, 5000000
    prev_ventas = 0
    prev_comp = 0
    cash = c0
    for mes in meses:
        v = uni[mes] * price
        cobr[mes] = 0.6 * v + (0.4 * prev_ventas if prev_ventas else rec_dic)
        pm = 0.5 * comp[mes] + (0.5 * prev_comp if prev_comp else pag_dic)
        pagos[mes] = pm + prod[mes] * mod_u + 3000000 + 2500000 + 0.02 * v + 8000000
        netos[mes] = cobr[mes] - pagos[mes]
        cash += netos[mes]
        caja[mes] = cash
        prev_ventas, prev_comp = v, comp[mes]
    enun = f"""## Contexto
Una empresa comercializa un solo producto y necesita su **presupuesto maestro del primer trimestre** (enero a marzo): ventas, producción, compras de materiales, mano de obra y **flujo de caja**.

## Datos
{tmd(["Mes", "Unidades a vender"], [[k, f"{v:,}".replace(",", ".")] for k, v in uni.items()])}

- Precio de venta: **{m(price)}** por unidad. Inventario inicial de producto terminado en enero: **{inv0} unidades**.
- **Inventario final deseado:** 20% de las ventas del mes siguiente.
- Materiales: **2 kg por unidad a $6.000/kg** (sin inventario de materiales: se compra lo que se usa).
- Mano de obra directa: **0,5 horas por unidad a $10.000/hora**, pagada en el mes.
- **Ventas:** 60% de contado y 40% a crédito, cobradas el mes siguiente. Cuentas por cobrar de diciembre: **{m(rec_dic)}** (se cobran en enero).
- **Compras de materiales:** 50% se paga en el mes y 50% el mes siguiente. Cuentas por pagar de diciembre: **{m(pag_dic)}** (se pagan en enero).
- Pagos fijos mensuales: CIF en efectivo **{m(3000000)}**, administración **{m(2500000)}** y cuota de un préstamo **{m(8000000)}**. Comisión de ventas: **2% de las ventas del mes**, pagada en el mes.
- Caja inicial: **{m(c0)}**.

## Qué debes hacer
1. Presupuesto de **ventas** (unidades y valor) y de **producción** (unidades).
2. Presupuesto de **compras de materiales** y de **mano de obra directa**.
3. **Presupuesto de cobros** y de **pagos** por mes.
4. **Flujo de caja** mensual con saldo final de caja de cada mes. Señala si algún mes requiere financiación."""
    entrega = "Un **.xlsx** con las hojas **Ventas y producción**, **Compras y MOD** y **Flujo de caja**."
    checks = [H(["Ventas y producción", "Compras y MOD", "Flujo de caja"], 5),
              V("Producción de enero (unidades)", prod["Ene"], 8, pista="Ventas + inventario final deseado − inventario inicial."),
              V("Producción de febrero (unidades)", prod["Feb"], 8, pista="Usa el inventario final de enero como inicial."),
              V("Producción de marzo (unidades)", prod["Mar"], 8, pista="Inventario final de marzo = 20% de las ventas de abril."),
              V("Compras de materiales de enero", comp["Ene"], 8, pista="Producción × 2 kg × $6.000."),
              V("Cobros de enero", cobr["Ene"], 10, pista="60% de enero + cuentas por cobrar de diciembre."),
              V("Cobros de febrero", cobr["Feb"], 8, pista="60% de febrero + 40% de enero."),
              V("Pagos totales de enero", pagos["Ene"], 12, tol=5, pista="Materiales (50% + deuda de diciembre), MOD, CIF, administración, comisión y préstamo."),
              V("Saldo de caja al final de enero", caja["Ene"], 8, tol=5, pista="Caja inicial + cobros − pagos."),
              V("Saldo de caja al final de marzo", caja["Mar"], 12, tol=10, pista="Acumula los tres meses."),
              F("Flujo de caja", 8, 13, "Fórmulas en el flujo de caja")]
    rub = [R("Presupuesto de ventas y producción", 25, "Inventarios finales y producción correctos."), R("Compras y MOD", 20, "Costos por unidad y pagos."), R("Cobros y pagos", 25, "Aplicación de los plazos de cobro y pago."),
           R("Flujo de caja", 20, "Saldos mensuales consistentes; identifica necesidades de financiación."), R("Orden y fórmulas", 10, "Parametrización, formato y claridad.")]
    datos = [["Mes", "Unidades"]] + [[k, v] for k, v in uni.items()] + [[], ["Precio", price], ["Inventario inicial (u)", inv0], ["Caja inicial", c0], ["CxC diciembre", rec_dic], ["CxP diciembre", pag_dic]]
    sheets = [instr_sheet("Presupuesto maestro trimestral", ["Completa las tres hojas con fórmulas y parámetros en celdas."]), {"name": "Datos", "rows": datos, "widths": [28, 16], "headers": [1], "note": "D97706"},
              blank("Ventas y producción", ["Concepto", "Ene", "Feb", "Mar"], 12, [36, 16, 16, 16]), blank("Compras y MOD", ["Concepto", "Ene", "Feb", "Mar"], 12, [36, 16, 16, 16]),
              blank("Flujo de caja", ["Concepto", "Ene", "Feb", "Mar"], 20, [36, 16, 16, 16])]
    return dict(id="t08", tipo="excel", titulo="Presupuesto maestro y flujo de caja trimestral", nivel="Avanzado", minutos=120, subject_id="m3s2",
                objetivo="Construir un presupuesto operativo y de caja enlazado con fórmulas.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T9 razones
def t09():
    d = {
        "Año 1": dict(caja=120, cxc=360, inv=340, af=980, prov=330, ofc=130, ocp=80, pl=460, pat=800, ven=3150.0, cv=2047.5, gop=650.0, intr=80.0),
        "Año 2": dict(caja=150, cxc=420, inv=380, af=1050, prov=330, ofc=150, ocp=120, pl=500, pat=900, ven=3600.0, cv=2340.0, gop=720.0, intr=90.0),
    }
    out = {}
    for y, x in d.items():
        ac = x["caja"] + x["cxc"] + x["inv"]
        ta = ac + x["af"]
        pc = x["prov"] + x["ofc"] + x["ocp"]
        pt = pc + x["pl"]
        assert abs(ta - (pt + x["pat"])) < 1e-9, (y, ta, pt + x["pat"])
        ub = x["ven"] - x["cv"]
        uo = ub - x["gop"]
        uai = uo - x["intr"]
        un = uai * 0.65
        out[y] = dict(ac=ac, ta=ta, pc=pc, pt=pt, ub=ub, uo=uo, uai=uai, un=un, rc=ac / pc, pa=(ac - x["inv"]) / pc, end=pt / ta, mb=ub / x["ven"], mn=un / x["ven"],
                      roa=un / ta, roe=un / x["pat"], dso=x["cxc"] / x["ven"] * 365, rot=x["cv"] / x["inv"], mult=ta / x["pat"], rotact=x["ven"] / ta)
    o1, o2 = out["Año 1"], out["Año 2"]
    crec = d["Año 2"]["ven"] / d["Año 1"]["ven"] - 1
    f = lambda y, k: d[y][k]
    enun = f"""## Contexto
Debes analizar la situación financiera de **Comercial Andina S.A.S.** comparando dos años. Cifras en **millones de pesos**. Tarifa de impuesto de renta para el ejercicio: **35%** sobre la utilidad antes de impuestos.

## Estado de situación financiera
{tmd(["Cuenta", "Año 1", "Año 2"], [["Caja y bancos", f('Año 1', 'caja'), f('Año 2', 'caja')], ["Cuentas por cobrar", f('Año 1', 'cxc'), f('Año 2', 'cxc')], ["Inventarios", f('Año 1', 'inv'), f('Año 2', 'inv')], ["Propiedad, planta y equipo (neto)", f('Año 1', 'af'), f('Año 2', 'af')],
 ["Proveedores", f('Año 1', 'prov'), f('Año 2', 'prov')], ["Obligaciones financieras de corto plazo", f('Año 1', 'ofc'), f('Año 2', 'ofc')], ["Otros pasivos corrientes", f('Año 1', 'ocp'), f('Año 2', 'ocp')], ["Pasivos de largo plazo", f('Año 1', 'pl'), f('Año 2', 'pl')], ["Patrimonio", f('Año 1', 'pat'), f('Año 2', 'pat')]])}

## Estado de resultados
{tmd(["Concepto", "Año 1", "Año 2"], [["Ventas", f('Año 1', 'ven'), f('Año 2', 'ven')], ["Costo de ventas", f('Año 1', 'cv'), f('Año 2', 'cv')], ["Gastos operacionales", f('Año 1', 'gop'), f('Año 2', 'gop')], ["Gastos financieros (intereses)", f('Año 1', 'intr'), f('Año 2', 'intr')]])}

## Qué debes hacer
1. Arma los estados completos (subtotales: activo corriente, activos totales, pasivo corriente, utilidad bruta, operacional, antes de impuestos y neta).
2. Haz el **análisis vertical** y **horizontal** (variación absoluta y porcentual).
3. Calcula las razones de **liquidez** (corriente, prueba ácida), **endeudamiento**, **actividad** (rotación de inventarios con costo de ventas y días de cartera sobre ventas, 365 días) y **rentabilidad** (margen bruto, margen neto, ROA, ROE).
4. Aplica **DuPont**: margen neto × rotación de activos × multiplicador de capital = ROE.
5. Redacta una **interpretación de 5 a 8 líneas**: ¿mejoró la empresa? ¿cuál es su principal riesgo?"""
    entrega = "Un **.xlsx** con las hojas **Estados**, **Análisis** y **Razones** (la interpretación va en la hoja Razones o en un trabajo aparte)."
    pct_alt = lambda v: [v * 100]
    checks = [H(["Estados", "Análisis", "Razones"], 4),
              V("Total activos Año 2", o2["ta"], 5, pista="Suma de activos corrientes y PPE."),
              V("Utilidad neta Año 2", o2["un"], 8, tol=0.01, pista="Utilidad antes de impuestos × (1 − 35%)."),
              V("Razón corriente Año 2", o2["rc"], 7, tol=0.01, pista="Activo corriente / pasivo corriente."),
              V("Prueba ácida Año 2", o2["pa"], 7, tol=0.01, pista="(Activo corriente − inventarios) / pasivo corriente."),
              V("Endeudamiento Año 2", o2["end"], 7, tol=0.001, alts=pct_alt(o2["end"]), pista="Pasivo total / activo total."),
              V("Margen neto Año 2", o2["mn"], 7, tol=0.0005, alts=pct_alt(o2["mn"]), pista="Utilidad neta / ventas."),
              V("ROE Año 2", o2["roe"], 8, tol=0.001, alts=pct_alt(o2["roe"]), pista="Utilidad neta / patrimonio."),
              V("ROA Año 2", o2["roa"], 6, tol=0.001, alts=pct_alt(o2["roa"]), pista="Utilidad neta / activo total."),
              V("Días de cartera Año 2", o2["dso"], 7, tol=0.1, pista="Cuentas por cobrar / ventas × 365."),
              V("Rotación de inventarios Año 2", o2["rot"], 6, tol=0.01, pista="Costo de ventas / inventarios."),
              V("Crecimiento de ventas", crec, 6, tol=0.001, alts=pct_alt(crec), pista="Ventas Año 2 / Año 1 − 1."),
              V("Multiplicador de capital Año 1", o1["mult"], 6, tol=0.01, pista="Activo total / patrimonio."),
              F("Razones", 14, 10, "Razones calculadas con fórmulas")]
    rub = [R("Estados completos", 15, "Subtotales y cuadre del balance."), R("Análisis vertical y horizontal", 20, "Variaciones y estructura."), R("Razones financieras", 30, "Fórmulas y resultados correctos para ambos años."),
           R("DuPont", 10, "Descomposición correcta del ROE."), R("Interpretación", 25, "Conclusiones con datos, riesgo principal y recomendaciones.")]
    datos = [["Cuenta", "Año 1", "Año 2"]] + [["Caja y bancos", 120, 150], ["Cuentas por cobrar", 360, 420], ["Inventarios", 340, 380], ["PPE (neto)", 980, 1050], ["Proveedores", 330, 330], ["Obligaciones financieras CP", 130, 150], ["Otros pasivos corrientes", 80, 120],
                                      ["Pasivos de largo plazo", 460, 500], ["Patrimonio", 800, 900], [], ["Ventas", 3150, 3600], ["Costo de ventas", 2047.5, 2340], ["Gastos operacionales", 650, 720], ["Gastos financieros", 80, 90], ["Tasa de impuesto", 0.35, 0.35]]
    sheets = [instr_sheet("Análisis financiero y DuPont", ["Cifras en millones de pesos. Completa Estados, Análisis y Razones."]), {"name": "Datos", "rows": datos, "widths": [34, 14, 14], "headers": [1], "numfmt": "#,##0.00", "note": "D97706"},
              blank("Estados", ["Concepto", "Año 1", "Año 2"], 30, [40, 14, 14]), blank("Análisis", ["Concepto", "% vertical A1", "% vertical A2", "Var. absoluta", "Var. %"], 30, [40, 14, 14, 14, 14]),
              blank("Razones", ["Razón", "Año 1", "Año 2", "Interpretación"], 22, [34, 14, 14, 50])]
    return dict(id="t09", tipo="excel", titulo="Análisis financiero: razones y DuPont (dos años)", nivel="Intermedio", minutos=120, subject_id="m3s4",
                objetivo="Calcular e interpretar razones financieras y descomponer el ROE.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T10 proyecto
def t10():
    inv, fl, salv, r = 250.0, [70.0, 85.0, 95.0, 100.0, 110.0], 40.0, 0.14
    cfs = [-inv] + fl[:4] + [fl[4] + salv]
    npv = lambda rate, c: sum(x / (1 + rate) ** t for t, x in enumerate(c))
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid, cfs) > 0:
            lo = mid
        else:
            hi = mid
    tir = (lo + hi) / 2
    vpn = npv(r, cfs)
    cum, pb = 0.0, None
    for t, x in enumerate(fl, 1):
        if cum + x >= inv and pb is None:
            pb = t - 1 + (inv - cum) / x
        cum += x
    cum, pbd = 0.0, None
    for t, x in enumerate(cfs[1:], 1):
        pv = x / (1 + r) ** t
        if cum + pv >= inv and pbd is None:
            pbd = t - 1 + (inv - cum) / pv
        cum += pv
    pv_ben = npv(r, [0] + cfs[1:])
    bc = pv_ben / inv
    cfs_s = [-inv] + [x * 0.9 for x in fl[:4]] + [fl[4] * 0.9 + salv]
    vpn_s = npv(r, cfs_s)
    enun = f"""## Contexto
Una empresa evalúa **ampliar su planta** con una inversión inicial y flujos netos de caja esperados durante 5 años. Cifras en **millones de pesos**; tasa de descuento (costo de oportunidad): **{r:.0%}**.

## Datos
- Inversión inicial (año 0): **{inv:,.0f}**
- Valor de salvamento al final del año 5 (se suma al flujo del año 5): **{salv:,.0f}**

{tmd(["Año", "Flujo neto de caja"], [[i + 1, f"{x:,.0f}"] for i, x in enumerate(fl)])}

## Qué debes hacer
1. Construye el **flujo de caja del proyecto** (años 0 a 5) incluyendo el valor de salvamento.
2. Calcula **VPN** (`VNA`), **TIR** (`TIR`), **relación beneficio/costo**, **período de recuperación simple** y **descontado**.
3. **Análisis de sensibilidad:** ¿cuánto sería el VPN si los flujos operativos fueran **10% menores**? Haz una tabla variando la tasa de descuento del 8% al 20%.
4. Redacta tu **recomendación** (aceptar o rechazar) y qué variable vigilarías."""
    entrega = "Un **.xlsx** con las hojas **Flujo**, **Indicadores** y **Sensibilidad**."
    checks = [H(["Flujo", "Indicadores", "Sensibilidad"], 5),
              V("VPN del proyecto (millones)", vpn, 18, tol=0.05, pista="VNA de los flujos 1 a 5 (con salvamento) menos la inversión."),
              V("TIR del proyecto", tir, 14, tol=0.0005, alts=[tir * 100], pista="Función TIR sobre los flujos 0 a 5."),
              V("Relación beneficio/costo", bc, 10, tol=0.005, pista="VP de los flujos / inversión inicial."),
              V("Período de recuperación simple (años)", pb, 12, tol=0.02, pista="Años hasta que el flujo acumulado cubre la inversión (sin salvamento)."),
              V("Período de recuperación descontado (años)", pbd, 14, tol=0.05, pista="Igual, pero con flujos descontados."),
              V("VPN con flujos operativos 10% menores", vpn_s, 14, tol=0.05, pista="Reduce los flujos 1 a 5 un 10% (el salvamento no cambia)."),
              F("Indicadores", 4, 7, "Indicadores con fórmulas"), F("Sensibilidad", 6, 6, "Tabla de sensibilidad con fórmulas")]
    rub = [R("Flujo de caja", 15, "Estructura y valor de salvamento."), R("Indicadores", 35, "VPN, TIR, B/C y payback simple y descontado."), R("Sensibilidad", 20, "Escenario −10% y tabla por tasa."),
           R("Recomendación", 20, "Decisión argumentada con los indicadores."), R("Orden y fórmulas", 10, "Funciones financieras y formato.")]
    datos = [["Inversión", inv], ["Tasa de descuento", r], ["Valor de salvamento (año 5)", salv], [], ["Año", "Flujo neto"]] + [[i + 1, x] for i, x in enumerate(fl)]
    sheets = [instr_sheet("Evaluación de un proyecto de inversión", ["Cifras en millones de pesos. Completa Flujo, Indicadores y Sensibilidad."]), {"name": "Datos", "rows": datos, "widths": [30, 14], "headers": [5], "numfmt": "#,##0.00", "note": "D97706"},
              blank("Flujo", ["Año", "Flujo"], 8, [10, 16]), blank("Indicadores", ["Indicador", "Valor"], 12, [36, 16]), blank("Sensibilidad", ["Tasa de descuento", "VPN"], 15, [20, 16])]
    return dict(id="t10", tipo="excel", titulo="Evaluación de proyectos: VPN, TIR, B/C y sensibilidad", nivel="Intermedio", minutos=100, subject_id="m3s3",
                objetivo="Evaluar financieramente una inversión con funciones de Excel.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets
