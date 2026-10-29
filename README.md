# Plan de estudio · Contaduría Pública (Colombia)

Aplicación web local con módulos y materias, flashcards, evaluaciones con puntaje ponderado,
cronograma configurable y progreso guardado en SQLite.

## Cómo iniciarla

Requisito: Python 3.8 o superior (no necesita instalar nada más).

- **Mac / Linux:** abre una terminal en esta carpeta y ejecuta `python3 server.py`
  (en Mac también puedes hacer doble clic en `iniciar.command`).
- **Windows:** doble clic en `iniciar.bat` (o `python server.py`).

Se abrirá el navegador en http://localhost:8765. Para detenerla, cierra la ventana o presiona Ctrl+C.

## Apariencia

En el menú lateral puedes elegir **Auto / Claro / Oscuro** (se recuerda en tu navegador). Las animaciones se desactivan solas si tu sistema tiene activada la opción «reducir movimiento».

## Dónde se guarda tu progreso

En `data/progreso.db` (SQLite). Sobrevive a reinicios del navegador y del computador.
Además se crea una copia diaria en `data/backups/` (las 14 más recientes) y puedes descargar
una copia desde **Ajustes**. Para mover tu progreso a otro equipo, copia la carpeta `data/`.

## Contenido

- 8 módulos, 30 materias y 110 temas. Cada tema tiene una **clase** escrita (con ejemplos resueltos) y enlaces a videos, lecturas y normas.
- 150 flashcards con nota relevante y 120 preguntas con retroalimentación.
- Las clases y enlaces están en `content/lessons/*.json` (mismo orden de temas que `content/mX.json`).
- Los enlaces externos pueden cambiar o caducar con el tiempo; si alguno falla, edítalo en ese archivo.
- Está en `content/*.json`: puedes editar, agregar materias, temas, flashcards o preguntas.
  Al reiniciar el servidor se sincronizan sin borrar tu progreso (los identificadores son estables).
  Formato de pregunta: `[enunciado, [4 opciones], índice_correcto, peso(1-3), retroalimentación]`.

## Talleres (Excel y trabajos escritos)

La sección **Talleres** tiene 16 ejercicios de Excel (libro diario y mayor, bancos, kardex, depreciación, matemática financiera, nómina, costos, presupuesto, razones financieras, VPN/TIR, renta, IVA, deterioro de cartera, muestreo de auditoría, consolidación, caja menor) y 4 trabajos escritos (informe financiero, caso de ética, memorando de IVA, control interno).

1. Descarga la plantilla `.xlsx` (trae los datos y hojas vacías) y resuélvela con fórmulas.
2. Súbela en el taller: se guarda en `data/entregas/` y se hace una **autorrevisión** automática de los resultados clave (es solo una vista previa).
3. Pulsa «Copiar solicitud de revisión», pégala en un chat con Claude adjuntando tu archivo, y registra la nota (0–5) y los comentarios en el mismo taller.
4. Tras tu primera entrega puedes ver los valores de control.

Los ejercicios están en `content/talleres.json` y se generan con `tools/gen_talleres.py` (`python3 gen_talleres.py` dentro de `tools/`). Las reglas de nómina y renta están simplificadas con fines didácticos; verifica con la norma vigente.

## Sistema de evaluación

- Cada pregunta tiene un peso (1, 2 o 3 puntos). Puntaje = puntos obtenidos / puntos posibles.
- Cada materia pertenece a un área; cada área tiene un peso (Ajustes).
  Nota ponderada = Σ(peso del área × % del área) ÷ Σ(pesos de las áreas evaluadas); nota 0–5 = ponderada ÷ 20.
- El umbral de aprobación (70% por defecto) se configura en Ajustes.

## Aviso

El contenido es una guía de estudio y repaso; las normas (UVT, tarifas, umbrales, etc.) cambian cada año.
Verifica siempre contra la norma vigente (Estatuto Tributario, DUR 2420 de 2015, circulares de la DIAN, etc.).
# plan-contaduria
