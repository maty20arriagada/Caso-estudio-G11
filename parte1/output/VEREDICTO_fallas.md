# Validacion: "no tiene sentido que las maquinas fallen fuera de horario"

## Veredicto
La hipotesis es una intuicion razonable, pero al contrastarla con los datos
el modelo resulta **esencialmente consistente**. No hay evidencia de un error
grueso de datos.

## Evidencia (430 fallas, 5 replicas)
1. **Las 430 fallas ocurrieron con la maquina en estado BUSY** (0 con la
   maquina IDLE u OFF_SHIFT). El simulador modela fallas *dependientes de la
   operacion* (el reloj de TBF avanza solo cuando la maquina procesa), tal como
   indica el PDF: "una falla ocurre durante el procesamiento de un lote".
2. **364 fallas dentro de la ventana operativa** (esperado).
3. **66 fallas fuera de la ventana**, descompuestas en:
   - 18 de estaciones 24/7 (secado/impregnado): **legitimas**, operan en continuo.
   - 40 de estaciones de turno: **overrun de lote** legitimo. La regla solo
     prohibe *iniciar* lotes fuera de turno, no *terminarlos*; un lote iniciado
     en turno puede cerrar pasado el horario (overrun mediano ~0.9 h).
   - 8 de estaciones de turno: el lote *inicio* entre 2 y 20 min despues
     del cierre (gap mediano 0.25 h). Es un **efecto de borde** del simulador,
     no una falla en dia/hora sin operacion. Representa 1.9% del total.

## Implicancia para la Parte 1
- Las fallas son un fenomeno real de la operacion, no ruido a eliminar.
- El aserradero concentra 352/430 fallas (82%): es la estacion mas expuesta,
  coherente con ser el **cuello de botella** (mas horas BUSY => mas fallas).
- Para KPIs estacionarios conviene tratar el warm-up (ver preguntas abiertas).
