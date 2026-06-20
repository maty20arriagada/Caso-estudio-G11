# Auditoría de consistencia interna — Parte 1

**Resultado: 11/11 verificaciones PASS** · warm-up = 9 días · periodo estacionario [216, 8760] h

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| 1 | Particion temporal: estados suman 8760 h por (rep,estacion) | ✅ PASS | min=8760.000 h, max=8760.000 h (esperado 8760) |
| 2 | DOWN == suma de reparaciones (confiabilidad consistente) | ✅ PASS | max|Δ|=0.0000 h sobre 23 pares (rep,estacion) |
| 3 | OFF_SHIFT solo en estaciones de turno (24/7 = 0) | ✅ PASS | aserradero=3138h; bano=3747h; secado=0h; drymill=3684h; impregnado=0h |
| 4 | Toda falla ocurre con la maquina en BUSY | ✅ PASS | 100.0% de 430 fallas (esperado 100%) |
| 5 | Balance de materia por lote (in = out + scrap) | ✅ PASS | max|Δ|=1.00e-03 m3 (= redondeo a 3 decimales del CSV) en 22687 lotes |
| 6 | KPIs en rango valido (utilizacion, disponibilidad, yield en [0,1]) | ✅ PASS | util[0.05,0.86] disp[0.92,1.00] yield[0.50,0.99] |
| 7 | Throughput: terminado == salida de la ultima estacion (por ruta) | ✅ PASS | P1:0.30%; P2:0.03%; P3:0.10% |
| 8 | Balance log_yard: arribos - procesado == nivel final | ✅ PASS | arribos=54839, procesado=47078, Δ=7761 vs nivel=7733 m3 (0.4%) |
| 9 | Conservacion en buffers (cumsum Δ = nivel registrado) | ✅ PASS | max|Δ|=1.73e-11 m3 en 47565 eventos |
| 10 | batch_id unico por (replica, estacion) | ✅ PASS | sin duplicados |
| 11 | Arribos de camiones dentro de la ventana operativa | ✅ PASS | 100.00% de 9615 arribos en ventana 07-23 de dias operativos |