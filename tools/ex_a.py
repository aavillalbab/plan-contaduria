# -*- coding: utf-8 -*-
from common import *


# ---------------------------------------------------------------- T1 ciclo contable
def t01():
    ACC = [("1105", "Caja", "D"), ("1110", "Bancos", "D"), ("1305", "Clientes", "D"), ("1435", "Mercancías no fabricadas por la empresa (inventario)", "D"),
           ("1524", "Equipo de oficina (muebles y enseres)", "D"), ("1528", "Equipo de computación y comunicación", "D"), ("1592", "Depreciación acumulada", "C"),
           ("2205", "Proveedores nacionales", "C"), ("3105", "Capital suscrito y pagado", "C"), ("4135", "Ingresos por comercio al por mayor y al por menor", "C"),
           ("5105", "Gastos de personal", "D"), ("5120", "Arrendamientos", "D"), ("5135", "Servicios", "D"), ("5160", "Depreciaciones", "D"),
           ("5305", "Gastos financieros", "D"), ("6135", "Costo de ventas", "D")]
    ini = {"1105": 2000000, "1110": 8000000, "1435": 10000000, "1524": 6000000, "2205": 4000000, "3105": 22000000}
    tx = [
        ("3 ene", "Compra de mercancía a crédito (sin IVA)", [("1435", 5000000, 0), ("2205", 0, 5000000)]),
        ("5 ene", "Venta de contado por $9.000.000 (costo de la mercancía: $5.400.000)", [("1105", 9000000, 0), ("4135", 0, 9000000), ("6135", 5400000, 0), ("1435", 0, 5400000)]),
        ("8 ene", "Venta a crédito por $3.000.000 (costo: $1.800.000)", [("1305", 3000000, 0), ("4135", 0, 3000000), ("6135", 1800000, 0), ("1435", 0, 1800000)]),
        ("10 ene", "Pago a proveedores con transferencia bancaria", [("2205", 3000000, 0), ("1110", 0, 3000000)]),
        ("12 ene", "Consignación de efectivo en el banco", [("1110", 5000000, 0), ("1105", 0, 5000000)]),
        ("15 ene", "Pago del arriendo del local por transferencia", [("5120", 1200000, 0), ("1110", 0, 1200000)]),
        ("18 ene", "Cobro en efectivo a un cliente (abono)", [("1105", 2000000, 0), ("1305", 0, 2000000)]),
        ("20 ene", "Compra de un computador, pagado desde bancos", [("1528", 2400000, 0), ("1110", 0, 2400000)]),
        ("25 ene", "Pago de salarios por transferencia", [("5105", 2500000, 0), ("1110", 0, 2500000)]),
        ("28 ene", "Pago de servicios públicos en efectivo", [("5135", 450000, 0), ("1105", 0, 450000)]),
        ("30 ene", "El banco descuenta gastos bancarios", [("5305", 60000, 0), ("1110", 0, 60000)]),
        ("31 ene", "Ajuste: depreciación mensual del equipo de oficina", [("5160", 100000, 0), ("1592", 0, 100000)]),
    ]
    bal = {a[0]: 0 for a in ACC}
    tot_deb = tot_cred = 0
    for c, v in ini.items():
        side = dict((a[0], a[2]) for a in ACC)[c]
        bal[c] += v if side == "D" else -v
        tot_deb += v if side == "D" else 0
        tot_cred += v if side == "C" else 0
    for _, _, es in tx:
        for c, d, cr in es:
            bal[c] += d - cr
            tot_deb += d
            tot_cred += cr
    assert tot_deb == tot_cred
    nat = dict((a[0], a[2]) for a in ACC)
    sal_deb = sum(v for c, v in bal.items() if v > 0)
    sal_cred = sum(-v for c, v in bal.items() if v < 0)
    assert sal_deb == sal_cred
    ing = -bal["4135"]
    gastos = sum(bal[c] for c in ("5105", "5120", "5135", "5160", "5305"))
    costo = bal["6135"]
    util = ing - costo - gastos
    activos = bal["1105"] + bal["1110"] + bal["1305"] + bal["1435"] + bal["1524"] + bal["1528"] + bal["1592"]
    pas = -bal["2205"]
    patr = -bal["3105"] + util
    assert activos == pas + patr
    enun = f"""## Contexto
**Papelería El Estudiante S.A.S.** es una pequeña comercializadora. Durante enero lleva su contabilidad con el **sistema de inventario permanente** (cada venta genera su costo de ventas). Debes llevar el ciclo contable completo en Excel. *No consideres IVA ni retenciones.*

## Datos
**Plan de cuentas a usar** (basado en el PUC):

{tmd(["Código", "Cuenta", "Naturaleza"], [[a[0], a[1], "Débito" if a[2] == "D" else "Crédito"] for a in ACC])}

**Balance inicial (1 de enero):**

{tmd(["Código", "Cuenta", "Valor"], [[c, next(a[1] for a in ACC if a[0] == c), m(v)] for c, v in ini.items()])}

**Operaciones del mes:**

{tmd(["Fecha", "Operación", "Valor / detalle"], [[t[0], t[1], " · ".join((('Dr ' if d else 'Cr ') + c + ' ' + m(d or cr)) for c, d, cr in t[2])] for t in tx])}

> **Nota:** la columna de detalle es una *pista* de la mecánica; escribe tú los asientos con su descripción en el Libro Diario.

## Qué debes hacer
1. Registra el **asiento de apertura** (comprobante 0) y los 12 asientos del mes en el **Libro Diario** (fecha, comprobante, código, cuenta, descripción, débito, crédito). Verifica que cada asiento cuadre.
2. **Mayoriza** en el Libro Mayor: una sección o tabla por cuenta con movimientos y saldo final.
3. Elabora el **Balance de prueba** (saldos débito y crédito por cuenta) con totales iguales.
4. Elabora el **Estado de resultados** del mes y el **Estado de situación financiera** al 31 de enero.
5. Escribe 3 líneas de **conclusión** sobre el resultado del mes y la liquidez."""
    entrega = "Un archivo **.xlsx** con las hojas: **Diario**, **Mayor**, **Balance de prueba** y **Estados financieros**. Usa fórmulas (sumas, SUMAR.SI, BUSCARV/XLOOKUP) para que los totales y saldos se calculen solos."
    checks = [H(["Diario", "Mayor", "Balance de prueba", "Estados financieros"], 5),
              V("Total débitos del Libro Diario (incluye la apertura)", tot_deb, 8, sheet="Diario", label="total", pista="Suma de la columna Débito: apertura + 12 asientos. Debe ser igual a la de Crédito."),
              V("Total del Balance de prueba (saldos)", sal_deb, 8, sheet="Balance de prueba", label="total", pista="Suma los saldos débito; debe ser igual a la suma de saldos crédito."),
              V("Saldo de Caja", bal["1105"], 5, sheet="Mayor", pista="Caja: inicial + ventas contado + cobro − consignación − servicios."),
              V("Saldo de Bancos", bal["1110"], 5, sheet="Mayor", pista="Considera consignación, pagos, arriendo, computador, salarios y gastos bancarios."),
              V("Saldo de Clientes", bal["1305"], 4, sheet="Mayor", pista="Venta a crédito menos el abono."),
              V("Saldo del inventario de mercancías", bal["1435"], 5, sheet="Mayor", pista="Inicial + compra − costo de las dos ventas."),
              V("Saldo de Proveedores", -bal["2205"], 4, sheet="Mayor", pista="Inicial + compra a crédito − pago.", abs_=True),
              V("Ingresos del mes", ing, 5, sheet="Estados financieros", pista="Venta de contado + venta a crédito."),
              V("Costo de ventas", costo, 4, sheet="Estados financieros", pista="Suma de los costos de las dos ventas."),
              V("Utilidad neta del mes", util, 8, sheet="Estados financieros", label="utilidad", pista="Ingresos − costo de ventas − gastos (arriendo, salarios, servicios, financieros, depreciación)."),
              V("Total activos", activos, 6, sheet="Estados financieros", label="activo", pista="La depreciación acumulada resta."),
              V("Total patrimonio (capital + utilidad)", patr, 5, sheet="Estados financieros", label="patrimonio", pista="Capital + utilidad del período."),
              F("Balance de prueba", 8, 10, "Uso de fórmulas en el Balance de prueba"),
              F("Estados financieros", 5, 8, "Uso de fórmulas en los Estados financieros")]
    rub = [R("Libro Diario", 25, "Apertura y 12 asientos con fecha, comprobante, descripción y partida doble que cuadra."),
           R("Libro Mayor", 20, "Mayorización correcta por cuenta con saldo final y naturaleza adecuada."),
           R("Balance de prueba", 20, "Saldos correctos y totales iguales; ordenado por código."),
           R("Estados financieros", 25, "Estado de resultados y de situación financiera consistentes entre sí (A = P + Pat)."),
           R("Fórmulas, orden y conclusión", 10, "Uso de fórmulas, formato legible y conclusión breve.")]
    datos = [["Código", "Cuenta", "Naturaleza"]] + [[a[0], a[1], "Débito" if a[2] == "D" else "Crédito"] for a in ACC] + [[], ["Balance inicial (1 de enero)"], ["Código", "Cuenta", "Valor"]] + \
            [[c, next(a[1] for a in ACC if a[0] == c), v] for c, v in ini.items()] + [[], ["Operaciones del mes"], ["Fecha", "Operación"]] + [[t[0], t[1]] for t in tx]
    sheets = [instr_sheet("Papelería El Estudiante S.A.S. — Ciclo contable de enero", ["Lee el enunciado en la app. Completa las hojas: Diario, Mayor, Balance de prueba y Estados financieros.", "Usa fórmulas siempre que sea posible."]),
              {"name": "Datos", "rows": datos, "widths": [12, 52, 14], "headers": [1], "subs": [len(ACC) + 3, len(ACC) + 4 + len(ini) + 3], "note": "D97706"},
              blank("Diario", ["Fecha", "Comprobante", "Código", "Cuenta", "Descripción", "Débito", "Crédito"], 60, [10, 13, 10, 40, 40, 14, 14]),
              blank("Mayor", ["Código", "Cuenta", "Fecha", "Descripción", "Débito", "Crédito", "Saldo"], 80, [10, 36, 10, 36, 14, 14, 14]),
              blank("Balance de prueba", ["Código", "Cuenta", "Saldo débito", "Saldo crédito"], 20, [10, 46, 16, 16]),
              blank("Estados financieros", ["Concepto", "Valor"], 40, [48, 18])]
    ex = dict(id="t01", tipo="excel", titulo="Ciclo contable completo: Libro Diario, Mayor y Estados financieros", nivel="Básico", minutos=150, subject_id="m1s1",
              objetivo="Llevar la contabilidad en libros: registrar, mayorizar, probar y presentar estados financieros.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks)
    return ex, sheets


# ---------------------------------------------------------------- T2 bancos
def t02():
    libro = [("Saldo inicial", None, 12500000, "Saldo según libros al 1 de mes"), ("02", "Consignación", 4200000, ""), ("03", "Cheque 1001", -1850000, ""), ("10", "Consignación", 3600000, ""),
             ("12", "Cheque 1002", -2300000, ""), ("14", "Cheque 1003", -980000, ""), ("18", "Consignación", 5100000, ""), ("20", "Cheque 1004", -1450000, ""),
             ("22", "Cheque 1005", -620000, ""), ("30", "Consignación", 2750000, ""), ("30", "Cheque 1006", -1100000, "")]
    ext = [("Saldo inicial", 12500000), ("02 Consignación", 4200000), ("05 Cheque 1001", -1850000), ("10 Consignación", 3600000), ("15 Cheque 1002", -2300000),
           ("18 Consignación", 5100000), ("26 Cheque 1005", -620000), ("30 Nota débito: comisiones bancarias", -45000), ("30 Nota crédito: intereses de la cuenta", 18000)]
    sl = sum(x[2] for x in libro)
    se = sum(x[1] for x in ext)
    pend = 980000 + 1450000 + 1100000
    trans = 2750000
    conc = se + trans - pend
    assert conc == sl - 45000 + 18000
    enun = f"""## Contexto
Al cierre del mes debes **conciliar** el libro auxiliar de bancos de la empresa con el extracto del banco.

## Datos
**Libro de bancos (según la empresa):**

{tmd(["Día", "Detalle", "Valor"], [[x[0], x[1] or "", m(x[2])] for x in libro])}

**Extracto bancario:**

{tmd(["Detalle", "Valor"], [[x[0], m(x[1])] for x in ext])}

## Qué debes hacer
1. Registra el **Libro de bancos** con saldo acumulado y determina el **saldo en libros**.
2. Determina el **saldo del extracto**.
3. Identifica las **partidas conciliatorias**: cheques girados no cobrados, consignaciones en tránsito, notas débito/crédito no contabilizadas.
4. Elabora la **conciliación bancaria** hasta llegar al **saldo conciliado** por ambos lados (deben coincidir).
5. Escribe los **asientos de ajuste** que debe hacer la empresa (notas débito y crédito)."""
    entrega = "Un **.xlsx** con las hojas **Libro de bancos**, **Conciliación** y **Ajustes**. Ambos lados de la conciliación deben terminar en el mismo saldo."
    checks = [H(["Libro de bancos", "Conciliación", "Ajustes"], 5),
              V("Saldo en libros antes de ajustes", sl, 12, sheet="Libro de bancos", pista="Saldo inicial + consignaciones − cheques girados."),
              V("Saldo según extracto", se, 12, pista="Saldo inicial + movimientos del extracto."),
              V("Total de cheques pendientes de cobro", pend, 14, pista="Cheques 1003, 1004 y 1006."),
              V("Consignaciones en tránsito", trans, 10, pista="La consignación del día 30 que el banco aún no registra."),
              V("Saldo conciliado", conc, 18, pista="Extracto + consignaciones en tránsito − cheques pendientes."),
              V("Ajuste neto en libros (nota débito − nota crédito)", 27000, 7, pista="Comisiones 45.000 − intereses 18.000.", tol=1),
              F("Conciliación", 4, 12, "Uso de fórmulas en la conciliación")]
    rub = [R("Libro de bancos", 20, "Registro y saldo acumulado correctos."), R("Identificación de partidas", 25, "Clasifica bien cheques pendientes, consignaciones en tránsito y notas."),
           R("Conciliación", 30, "Ambos saldos terminan iguales con el formato estándar."), R("Asientos de ajuste", 15, "Asientos balanceados con las cuentas adecuadas."),
           R("Fórmulas y orden", 10, "Fórmulas y presentación clara.")]
    datos = [["Libro de bancos"], ["Día", "Detalle", "Valor"]] + [[x[0], x[1], x[2]] for x in libro] + [[], ["Extracto bancario"], ["Detalle", "Valor"]] + [[x[0], x[1]] for x in ext]
    sheets = [instr_sheet("Conciliación bancaria", ["Completa las hojas: Libro de bancos, Conciliación y Ajustes."]),
              {"name": "Datos", "rows": datos, "widths": [34, 28, 16], "headers": [2, len(libro) + 5], "note": "D97706"},
              blank("Libro de bancos", ["Día", "Detalle", "Ingreso", "Egreso", "Saldo"], 20, [10, 30, 16, 16, 16]),
              blank("Conciliación", ["Concepto", "Valor"], 25, [52, 18]), blank("Ajustes", ["Código", "Cuenta", "Débito", "Crédito"], 10, [10, 40, 16, 16])]
    return dict(id="t02", tipo="excel", titulo="Libro de bancos y conciliación bancaria", nivel="Básico", minutos=75, subject_id="m2s1",
                objetivo="Conciliar el libro de bancos con el extracto e identificar los ajustes contables.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T3 kardex
def t03():
    mov = [("Inventario inicial", "entrada", 100, 4000), ("Compra 1", "entrada", 200, 4200), ("Venta 1", "salida", 150, None), ("Compra 2", "entrada", 100, 4500), ("Venta 2", "salida", 180, None)]
    price = 8000
    # PEPS
    layers, cv_peps = [], 0
    for n, t, q, c in mov:
        if t == "entrada":
            layers.append([q, c])
        else:
            need = q
            while need:
                take = min(need, layers[0][0])
                cv_peps += take * layers[0][1]
                layers[0][0] -= take
                need -= take
                if layers[0][0] == 0:
                    layers.pop(0)
    inv_peps = sum(q * c for q, c in layers)
    # promedio
    qty = val = 0
    cv_avg = 0
    for n, t, q, c in mov:
        if t == "entrada":
            qty += q
            val += q * c
        else:
            avg = val / qty
            cv_avg += q * avg
            qty -= q
            val -= q * avg
    ventas = 330 * price
    enun = f"""## Contexto
Una papelería maneja un solo producto, el **cuaderno argollado**. Debes llevar su **kardex** con dos métodos de valoración y comparar el efecto en el costo de ventas y la utilidad bruta. Precio de venta: **{m(price)}** por unidad.

## Datos
{tmd(["Movimiento", "Tipo", "Unidades", "Costo unitario"], [[n, t, q, m(c) if c else "(según método)"] for n, t, q, c in mov])}

## Qué debes hacer
1. Elabora el **kardex PEPS (FIFO)** con columnas de entradas, salidas y saldo (unidades, costo unitario y valor).
2. Elabora el **kardex por promedio ponderado móvil**.
3. Calcula para cada método: **costo de ventas** e **inventario final**.
4. Calcula las **ventas** y la **utilidad bruta** con cada método y explica en 3 líneas por qué difieren (hay inflación de costos)."""
    entrega = "Un **.xlsx** con las hojas **Kardex PEPS**, **Kardex Promedio** y **Comparación**."
    checks = [H(["Kardex PEPS", "Kardex Promedio", "Comparación"], 5),
              V("Costo de ventas PEPS", cv_peps, 14, pista="Venta 1 consume 100@4.000 + 50@4.200; venta 2 consume 150@4.200 + 30@4.500."),
              V("Inventario final PEPS", inv_peps, 12, pista="Quedan 70 unidades al costo de la última compra."),
              V("Costo de ventas promedio ponderado", cv_avg, 14, tol=2, pista="Recalcula el promedio tras cada entrada."),
              V("Inventario final promedio", val, 12, tol=2, pista="70 unidades al último costo promedio."),
              V("Ventas totales", ventas, 6, pista="330 unidades × precio."),
              V("Utilidad bruta con PEPS", ventas - cv_peps, 8, pista="Ventas − costo de ventas PEPS."),
              V("Utilidad bruta con promedio", ventas - cv_avg, 8, tol=2, pista="Ventas − costo de ventas promedio."),
              F("Kardex PEPS", 6, 8, "Fórmulas en el kardex PEPS"), F("Kardex Promedio", 6, 8, "Fórmulas en el kardex por promedio")]
    rub = [R("Kardex PEPS", 30, "Capas de costo bien consumidas; saldos coherentes."), R("Kardex promedio", 30, "Promedio móvil recalculado en cada entrada."),
           R("Comparación", 25, "Costo de ventas, inventario y utilidad bruta con ambos métodos."), R("Explicación y orden", 15, "Explica el efecto de los costos crecientes.")]
    datos = [["Movimiento", "Tipo", "Unidades", "Costo unitario"]] + [[n, t, q, c] for n, t, q, c in mov] + [[], ["Precio de venta", price]]
    sheets = [instr_sheet("Kardex PEPS vs. promedio ponderado", ["Completa: Kardex PEPS, Kardex Promedio y Comparación."]),
              {"name": "Datos", "rows": datos, "widths": [26, 12, 12, 16], "headers": [1], "note": "D97706"},
              blank("Kardex PEPS", ["Fecha/Mov.", "Entrada u", "Entrada $/u", "Entrada $", "Salida u", "Salida $/u", "Salida $", "Saldo u", "Saldo $/u", "Saldo $"], 15, [16] * 10),
              blank("Kardex Promedio", ["Fecha/Mov.", "Entrada u", "Entrada $/u", "Entrada $", "Salida u", "Salida $/u", "Salida $", "Saldo u", "Saldo $/u", "Saldo $"], 15, [16] * 10),
              blank("Comparación", ["Concepto", "PEPS", "Promedio"], 12, [34, 18, 18])]
    return dict(id="t03", tipo="excel", titulo="Kardex: PEPS vs. promedio ponderado", nivel="Básico", minutos=75, subject_id="m2s1",
                objetivo="Valorar inventarios con dos métodos y analizar su efecto en la utilidad.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T4 depreciación
def t04():
    cost, resid, life = 48000000, 6000000, 5
    prod = [45000, 52000, 38000, 41000, 24000]
    est = 200000
    sln = (cost - resid) / life
    ddb, acc = [], 0
    for y in range(life):
        d = min((cost - acc) * 2 / life, cost - resid - acc)
        ddb.append(d)
        acc += d
    rate = (cost - resid) / est
    up = [p * rate for p in prod]
    enun = f"""## Contexto
Una empresa adquiere una **máquina industrial** y debe compararla bajo tres métodos de depreciación (NIC 16).

## Datos
- Costo de adquisición: **{m(cost)}**
- Valor residual: **{m(resid)}**
- Vida útil: **{life} años**
- Producción total estimada en la vida útil: **{est:,} unidades**

{tmd(["Año", "Unidades producidas"], [[i + 1, f"{p:,}".replace(",", ".")] for i, p in enumerate(prod)])}

## Qué debes hacer
1. Calcula la depreciación **línea recta** por año, con depreciación acumulada y valor en libros (usa la función `SLN`).
2. Calcula la depreciación por **saldo decreciente doble** (usa `DDB`) y verifica que el valor en libros **nunca baje del residual**.
3. Calcula la depreciación por **unidades de producción** (tasa por unidad × producción de cada año).
4. Elabora un cuadro comparativo y un **gráfico de líneas** del valor en libros por método.
5. Escribe el **asiento de depreciación del año 1** con cada método y comenta cuál elegirías para esta máquina y por qué."""
    entrega = "Un **.xlsx** con las hojas **Línea recta**, **Saldo decreciente**, **Unidades de producción** y **Comparativo** (incluye el gráfico)."
    checks = [H(["Línea recta", "Saldo decreciente", "Unidades de producción", "Comparativo"], 5),
              V("Depreciación anual en línea recta", sln, 10, pista="(Costo − residual) / vida útil."),
              V("Saldo decreciente: año 1", ddb[0], 10, pista="Valor en libros × 2/vida."),
              V("Saldo decreciente: año 2", ddb[1], 10, pista="Sobre el valor en libros del año 1."),
              V("Saldo decreciente: año 5 (limitado al residual)", ddb[4], 14, pista="No puedes depreciar por debajo del valor residual."),
              V("Tasa por unidad producida", rate, 8, tol=0.01, pista="(Costo − residual) / producción total estimada."),
              V("Unidades de producción: año 2", up[1], 10, pista="Producción del año 2 × tasa."),
              V("Valor en libros al final del año 5", resid, 8, pista="Debe ser igual al valor residual con los tres métodos."),
              F("Línea recta", 5, 7, "Fórmulas en línea recta"), F("Saldo decreciente", 5, 7, "Fórmulas en saldo decreciente"), F("Unidades de producción", 5, 6, "Fórmulas en unidades de producción")]
    rub = [R("Línea recta", 15, "Tabla anual completa con acumulada y valor en libros."), R("Saldo decreciente", 25, "Uso correcto de DDB y límite del residual."),
           R("Unidades de producción", 20, "Tasa y depreciación por año correctas."), R("Comparativo y gráfico", 20, "Cuadro y gráfico legibles."),
           R("Asiento y criterio", 20, "Asiento correcto y recomendación argumentada.")]
    datos = [["Costo", cost], ["Valor residual", resid], ["Vida útil (años)", life], ["Producción total estimada (u)", est], [], ["Año", "Unidades producidas"]] + [[i + 1, p] for i, p in enumerate(prod)]
    sheets = [instr_sheet("Depreciación: tres métodos", ["Completa las hojas pedidas e inserta un gráfico en Comparativo."]),
              {"name": "Datos", "rows": datos, "widths": [34, 18], "headers": [6], "note": "D97706"},
              blank("Línea recta", ["Año", "Depreciación", "Acumulada", "Valor en libros"], 8, [10, 16, 16, 16]),
              blank("Saldo decreciente", ["Año", "Depreciación", "Acumulada", "Valor en libros"], 8, [10, 16, 16, 16]),
              blank("Unidades de producción", ["Año", "Unidades", "Depreciación", "Acumulada", "Valor en libros"], 8, [10, 14, 16, 16, 16]),
              blank("Comparativo", ["Año", "Línea recta", "Saldo decreciente", "Unidades"], 8, [10, 18, 18, 18])]
    return dict(id="t04", tipo="excel", titulo="Depreciación de PPE con tres métodos (SLN, DDB y unidades)", nivel="Intermedio", minutos=90, subject_id="m5s1",
                objetivo="Aplicar NIC 16 en Excel y comparar métodos de depreciación.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets


# ---------------------------------------------------------------- T5 matemáticas financieras
def t05():
    P, i, n = 120000000, 0.018, 36
    pmt = P * i / (1 - (1 + i) ** -n)
    sal = P
    for k in range(12):
        sal = sal * (1 + i) - pmt
    tot_int = pmt * n - P
    ea = (1 + i) ** 12 - 1
    A, j, k2 = 5000000, 0.01, 24
    vf = A * ((1 + j) ** k2 - 1) / j
    L, il, nl = 2000000, 0.01, 36
    vp_l = L * (1 - (1 + il) ** -nl) / il * (1 + il)
    enun = f"""## Contexto
Resuelve tres problemas de matemáticas financieras construyendo un **modelo en Excel con funciones financieras** (`PAGO`, `VF`, `VA`, `PAGOINT`, `PAGOPRIN`).

## Datos
- **Problema 1 (crédito):** préstamo de **{m(P)}**, tasa **1,8% mensual**, **36 cuotas** mensuales fijas vencidas.
- **Problema 2 (ahorro programado):** depósitos de **{m(A)}** al final de cada mes durante **24 meses** a **1% mensual**.
- **Problema 3 (arrendamiento, NIIF 16):** cuotas de **{m(L)}** al **inicio** de cada mes durante **36 meses**; tasa de descuento **1% mensual**.

## Qué debes hacer
1. **Problema 1:** calcula la **cuota**, construye la **tabla de amortización** (interés, abono a capital y saldo de los 36 meses), el **total de intereses**, el **saldo después de la cuota 12** y la **tasa efectiva anual** equivalente.
2. **Problema 2:** calcula el **valor futuro** del ahorro y cuánto corresponde a intereses.
3. **Problema 3:** calcula el **valor presente** de los pagos del arrendamiento (anualidad **anticipada**), que sería el pasivo inicial por arrendamiento.
4. Parametriza tasas y plazos en celdas (sin escribirlos dentro de las fórmulas) y verifica con una segunda forma de cálculo (por ejemplo, fórmula manual vs. función)."""
    entrega = "Un **.xlsx** con las hojas **Crédito**, **Ahorro** y **Arrendamiento**."
    checks = [H(["Crédito", "Ahorro", "Arrendamiento"], 5),
              V("Cuota mensual del crédito", pmt, 18, tol=5, sheet="Crédito", pista="PAGO(tasa; 36; −préstamo)."),
              V("Total de intereses pagados", tot_int, 12, tol=100, sheet="Crédito", pista="Cuota × 36 − préstamo."),
              V("Saldo después de la cuota 12", sal, 14, tol=100, sheet="Crédito", pista="Saldo tras 12 períodos de amortización."),
              V("Tasa efectiva anual del crédito", ea, 10, tol=0.0005, abs_=True, sheet="Crédito", alts=[ea * 100], pista="(1 + 1,8%)^12 − 1."),
              V("Valor futuro del ahorro", vf, 14, tol=10, sheet="Ahorro", pista="VF con 24 pagos de 5.000.000 al 1%."),
              V("Valor presente del arrendamiento (anticipada)", vp_l, 14, tol=10, sheet="Arrendamiento", pista="Anualidad anticipada: multiplica por (1 + i)."),
              F("Crédito", 36, 13, "Tabla de amortización con fórmulas")]
    rub = [R("Crédito y amortización", 40, "Cuota, tabla de 36 filas, intereses y saldo."), R("Tasa efectiva", 10, "Conversión correcta de tasas."), R("Ahorro programado", 15, "VF correcto e intereses ganados."),
           R("Arrendamiento", 20, "Anualidad anticipada bien tratada."), R("Parametrización y verificación", 15, "Celdas de entrada, sin números dentro de fórmulas, doble verificación.")]
    datos = [["Problema 1"], ["Préstamo", P], ["Tasa mensual", i], ["Cuotas", n], [], ["Problema 2"], ["Depósito mensual", A], ["Tasa mensual", j], ["Meses", k2], [], ["Problema 3"], ["Cuota (inicio de mes)", L], ["Tasa mensual", il], ["Meses", nl]]
    sheets = [instr_sheet("Matemáticas financieras en Excel", ["Completa las tres hojas y parametriza los datos."]), {"name": "Datos", "rows": datos, "widths": [28, 18], "subs": [1, 6, 11], "note": "D97706"},
              blank("Crédito", ["Cuota #", "Saldo inicial", "Cuota", "Interés", "Abono a capital", "Saldo final"], 40, [10, 16, 14, 14, 16, 16]),
              blank("Ahorro", ["Concepto", "Valor"], 10, [36, 18]), blank("Arrendamiento", ["Concepto", "Valor"], 10, [36, 18])]
    return dict(id="t05", tipo="excel", titulo="Crédito, ahorro y arrendamiento con funciones financieras", nivel="Intermedio", minutos=90, subject_id="m1s2",
                objetivo="Aplicar PAGO, VF y VA, y construir una tabla de amortización.", enunciado=enun, entrega=entrega, rubrica=rub, checks=checks), sheets
