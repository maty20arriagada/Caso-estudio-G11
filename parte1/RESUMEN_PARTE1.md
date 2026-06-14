# Parte 1 — Análisis de productividad de la línea (Aserradero CMPC Mulchén)

Análisis de la salida de un modelo de simulación de eventos discretos de la línea
(5 réplicas, horizonte de 1 año). Todo el cálculo es **empírico** a partir de los
logs entregados; `parameters.csv`/`inputs_readme.md` no estaban en el paquete, por
lo que MTBF/MTTR, yields y capacidades se **estimaron de los datos**.

---

## 1. Datos, variables y unidades

| Archivo | Grano (una fila por…) | Uso principal |
|---|---|---|
| `calendar.csv` | día del horizonte | ventana operativa (turnos) |
| `log_arrivals.csv` | camión que llega con trozos | tasa de arribos |
| `station_events.csv` | intervalo de estado de una estación | **disponibilidad / utilización** |
| `batches.csv` | lote procesado por una estación | yields, tiempos, setup |
| `buffer_events.csv` | movimiento (PUT/GET) en un buffer | trazabilidad de inventario |
| `product_outputs.csv` | lote terminado que sale del sistema | throughput, lead time |
| `failures.csv` | falla en una estación | confiabilidad |
| `daily_wip.csv` | buffer × día | WIP |
| `daily_throughput.csv` | estación × día | producción diaria |

- **Volumen:** m³. **Tiempo:** horas (`*_h`) desde `t=0` (inicio del día 0).
- **Réplicas:** 5 (0–4), estadísticamente independientes → KPIs como **media ± IC95%**
  (t de Student, 4 g.l.).
- **Horizonte:** 365 días = 8.760 h. **Turno:** 16 h/día (07:00–23:00), 313 días
  operativos y 52 no operativos (1 día/semana).
- **Estaciones de turno:** aserradero, baño, drymill. **Continuas 24/7:** secado, impregnado.
- **Ruteo:** P1 `aserradero→baño`; P2 `aserradero→secado→drymill`;
  P3 `aserradero→secado→drymill→impregnado`.

### Warm-up (método de Welch)
El sistema arranca vacío. El throughput se estabiliza casi de inmediato (~60 m³/día),
mientras el WIP total crece sin acotarse (línea saturada). Se descartan los
**primeros 7 días** (168 h) para los KPIs estacionarios. → `figuras/warmup_welch.png`

---

## 2. Validación pedida: “no tiene sentido que fallen fuera de horario / días sin trabajo”

**Veredicto: la intuición es razonable, pero los datos son esencialmente consistentes; no hay error grueso.**

| Categoría de las 430 fallas | N | Veredicto |
|---|---:|---|
| Dentro de ventana operativa | 364 | esperado |
| 24/7 (secado/impregnado) fuera de turno | 18 | ✅ legítimo (operan en continuo) |
| Turno: *overrun* de lote (inició en turno, cerró después) | 40 | ✅ legítimo |
| Turno: lote iniciado en el borde (~2–20 min post-cierre) | 8 | ⚠️ efecto de borde (1,9%) |

- **Las 430 fallas (100%) ocurrieron con la máquina en `BUSY`**; ninguna con la máquina
  `IDLE`/`OFF_SHIFT`. El simulador modela **fallas dependientes de la operación**
  (el reloj de TBF avanza solo al procesar), tal como dice el enunciado.
- Las fallas “fuera de horario” de estaciones de turno se explican porque la regla solo
  prohíbe **iniciar** lotes fuera de turno, no **terminarlos** (overrun mediano ~0,9 h).
- Solo 8 fallas (1,9%) son un artefacto de borde del simulador, no fallas en día/hora sin operación.

Figuras: `fallas_descomposicion.png`, `fallas_hora_del_dia.png`, `fallas_por_ventana.png`.
Detalle: `VEREDICTO_fallas.md`, `tablas/fallas_clasificadas.csv`.

---

## 3. Disponibilidad, utilización y calidad (media de 5 réplicas)

| Estación | Tipo | Utilización | Disponibilidad | MTBF (h) | MTTR (h) | Fallas/año | Yield |
|---|---|---:|---:|---:|---:|---:|---:|
| **aserradero** | turno | **84,1 %** | **93,5 %** | **67** | 4,58 | **70** | **50,0 %** |
| secado | 24/7 | 37,9 % | 97,7 % | 360 | 7,88 | 9,6 | 97,0 % |
| drymill | turno | 25,4 % | 99,0 % | 365 | 3,62 | 3,6 | 95,0 % |
| impregnado | 24/7 | 6,4 % | 98,9 % | 449 | 5,15 | 1,2 | 98,8 % |
| baño | turno | 5,6 % | 99,4 % | 278 | 1,93 | 0,8 | 98,8 % |

Definiciones: Utilización = BUSY/tiempo programado; Disponibilidad = MTBF/(MTBF+MTTR) =
BUSY/(BUSY+DOWN); MTBF = horas BUSY/nº fallas; Yield = vol_out/vol_in.

**Composición del tiempo (% del total):**

| Estación | BUSY | SETUP | IDLE | BLOCKED | DOWN | OFF_SHIFT |
|---|---:|---:|---:|---:|---:|---:|
| aserradero | 54,0 | 6,4 | **0,0** | 0,0 | 3,7 | 35,8 |
| baño | 3,2 | 0,0 | 54,0 | 0,0 | 0,0 | 42,8 |
| secado | 37,9 | 4,3 | 56,9 | 0,0 | 0,9 | 0,0 |
| drymill | 14,7 | 3,3 | 39,8 | 0,0 | 0,1 | 42,1 |
| impregnado | 6,4 | 0,0 | 93,5 | 0,0 | 0,1 | 0,0 |

- El aserradero es la máquina **más exigida y menos confiable** (MTBF 67 h, 70 fallas/año,
  disponibilidad 93,5 %) y la única **nunca ociosa** (IDLE 0 %).
- El yield del aserradero (≈50 %) es la **principal pérdida de material** (aserrín, lampazos,
  corteza), típico de la recuperación de un aserradero. El resto de etapas conserva >95 %.
- `BLOCKED ≈ 0` en toda la línea: los buffers intermedios nunca saturan
  (niveles estacionarios ~7 m³).

Figuras: `composicion_estados.png`, `utilizacion_disponibilidad.png`, `yield_por_estacion.png`.

---

## 4. Cuello de botella

**El cuello de botella es el ASERRADERO**, confirmado por cinco evidencias independientes
(triangulación, Factory Physics / Teoría de Restricciones):

1. **Utilización 84,1 %**, 2,2× la siguiente estación (secado 37,9 %).
2. **IDLE 0 %** en el aserradero y **alta inanición aguas abajo** (secado 57 %, drymill 40 %,
   impregnado 94 % ociosos): la línea se hambrea por falta de alimentación.
3. **WIP en `log_yard` crece sin acotarse**: +21,2 m³/día (86 → 7.733 m³). Aguas abajo el WIP es estacionario.
4. **Balance arribos vs capacidad** (base estacionaria): llegan **150,6 m³/día-cal** y el aserradero
   procesa **129 m³/día-cal** → exceso de **21,6 m³/día**, que coincide con la pendiente de `log_yard`
   (consistencia interna).
5. **Concentración de fallas:** 82 % de todas las fallas ocurren en el aserradero.

`BLOCKED ≈ 0` indica que la restricción está en la **entrada** de la línea, no aguas abajo.

Figuras: `bottleneck_utilizacion.png`, `bottleneck_wip_balance.png`.

---

## 5. Propuesta de mejora (atacar la restricción)

El throughput de la línea está limitado por el aserradero; toda mejora debe ampliá­r su
capacidad efectiva. Aguas abajo hay **holgura amplia** (secado 38 %, drymill 25 %) para absorber más flujo.

- **A. Extender la operación del aserradero (palanca principal).** Hoy procesa ~150 m³ por día
  operativo en 16 h; arriban ~176 m³/día operativo. A **24 h/día** (mismo ritmo) procesaría
  **~226 m³/día (+50 %)**, superaría los arribos y **revertiría el backlog** de ~22 m³/día.
- **B. Reducir SETUP (6,4 % del tiempo)** con secuenciación/campañas por producto (SMED):
  el aserradero es la única estación que decide el producto del lote, por lo que cambia mucho.
- **C. Reducir DOWN (3,7 %) / subir MTBF (hoy 67 h, el más bajo)** con mantenimiento preventivo.

Las palancas B y C recuperan ~10 % de capacidad sin nuevas horas; la palanca A es la de mayor impacto.

---

## 6. Producción obtenida (insumo para la Parte 2)

Producción útil terminada (media de 5 réplicas, extrapolada a año completo):

| Producto | m³/año |
|---|---:|
| P1 (madera verde tratada) | ~6.919 |
| P2 (madera seca clasificada) | ~9.680 |
| P3 (madera impregnada) | ~5.556 |
| **Total** | **~22.155** |

Estos volúmenes satisfacen los mínimos comprometidos de la Parte 2 (P1≥4.000, P2≥6.000, P3≥3.000).

---

## 7. Limitaciones y supuestos

- **Faltan `parameters.csv` e `inputs_readme.md`**: MTBF/MTTR, yields, `warmup_days` y
  capacidades de buffers se estimaron empíricamente. Si se obtienen, permitirían contrastar
  valores nominales vs observados.
- **`BLOCKED` nunca se observó**: consistente con una línea restringida en la entrada
  (los buffers intermedios no saturan). No se pudo caracterizar el bloqueo.
- 8 fallas (1,9 %) con inicio de lote en el borde del turno: artefacto menor del simulador.

## Bibliografía de referencia
- Hopp, W. & Spearman, M. *Factory Physics* (utilización, cuello de botella, ley de Little).
- Goldratt, E. *La Meta* / Teoría de Restricciones (gestión de la restricción).
- Banks, Carson, Nelson & Nicol. *Discrete-Event System Simulation* (análisis de salida, warm-up).
- Law, A. *Simulation Modeling and Analysis* (método de Welch, réplicas e IC).
- Askin, R. & Goldberg, J. *Design and Analysis of Lean Production Systems*.
