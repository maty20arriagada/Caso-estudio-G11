"""
modelo_distribucion.py
=========================================================================
Modelo de distribucion de madera desde la planta CMPC Mulchen
usando Programacion Lineal (PuLP + CBC solver, open source).

Minimiza el costo total de transporte sujeto a:
- Toda la produccion debe distribuirse.
- Minimo contractual y capacidad maxima por destino-producto.

Entradas:
- distancias.json       : distancias desde Mulchen a cada destino (km)
- Produccion de Parte 1 : P1, P2, P3 en m3/ano

Salidas:
- solucion_distribucion.csv  : plan optimo de despachos
- solucion_distribucion.json : datos para el dashboard
- modelo_distribucion.lp     : formulacion matematica exportada
=========================================================================
"""

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pulp

PARTE2 = Path(__file__).resolve().parent
BASE = PARTE2.parent

DESTINOS = [
    "Puerto_Coronel",
    "Puerto_San_Vicente",
    "Puerto_Lirquen",
    "Reman_Coronel",
    "Reman_Los_Angeles",
    "Plywood_Collipulli",
]

PRODUCTOS = ["P1", "P2", "P3"]

COSTO_KM = 100.0


def build_bounds():
    L = {(i, j): 0.0 for i in DESTINOS for j in PRODUCTOS}
    U = {(i, j): 0.0 for i in DESTINOS for j in PRODUCTOS}

    L["Puerto_Coronel", "P1"] = 1200.0
    U["Puerto_Coronel", "P1"] = 12000.0
    L["Reman_Coronel", "P1"] = 1500.0
    U["Reman_Coronel", "P1"] = 8000.0
    L["Reman_Los_Angeles", "P1"] = 1300.0
    U["Reman_Los_Angeles", "P1"] = 6000.0

    L["Puerto_Lirquen", "P2"] = 1500.0
    U["Puerto_Lirquen", "P2"] = 8000.0
    L["Puerto_San_Vicente", "P2"] = 1500.0
    U["Puerto_San_Vicente", "P2"] = 8000.0
    L["Reman_Los_Angeles", "P2"] = 1500.0
    U["Reman_Los_Angeles", "P2"] = 5000.0
    L["Plywood_Collipulli", "P2"] = 1500.0
    U["Plywood_Collipulli", "P2"] = 5000.0

    L["Puerto_Coronel", "P3"] = 1200.0
    U["Puerto_Coronel", "P3"] = 10000.0
    L["Puerto_San_Vicente", "P3"] = 800.0
    U["Puerto_San_Vicente", "P3"] = 12000.0
    L["Plywood_Collipulli", "P3"] = 1000.0
    U["Plywood_Collipulli", "P3"] = 4000.0

    return L, U


def load_distances():
    p = PARTE2 / "distancias.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return data["distancias"], data.get("rutas", {})
    print("Aviso: distancias.json no encontrado. Ejecute kml_parser.py primero.")
    return None, {}


def load_produccion():
    default = {"P1": 6919.0, "P2": 9680.0, "P3": 5556.0}

    sources = [
        BASE / "parte1" / "RESUMEN_PARTE1.md",
    ]
    for src in sources:
        if src.exists():
            text = src.read_text(encoding="utf-8")
            import re
            found = {}
            for line in text.splitlines():
                m = re.match(r"\|\s*(P\d).*?\|\s*~?([\d.,]+)\s*\|", line)
                if m:
                    found[m.group(1)] = float(m.group(2).replace(",", "").replace(".", ""))
            if len(found) == 3:
                return found

    print("Aviso: usando produccion por defecto (RESUMEN_PARTE1.md).")
    return default


def load_produccion_por_replica():
    """
    Carga la produccion de cada replica desde product_outputs.csv.
    Retorna dict: {replica: {producto: m³}}
    """
    csv_path = BASE / "data" / "product_outputs.csv"
    if not csv_path.exists():
        return {}

    df = pd.read_csv(csv_path)
    prod = df.groupby(["replication", "product"])["volume_m3"].sum()
    replicas = {}
    for (rep, product), vol in prod.items():
        replicas.setdefault(int(rep), {})[product] = round(float(vol), 2)
    return replicas


def validar_factibilidad(produccion, L, U):
    errores = []
    for j in PRODUCTOS:
        min_total = sum(L[i, j] for i in DESTINOS)
        max_total = sum(U[i, j] for i in DESTINOS)
        disponible = produccion[j]
        if disponible < min_total or disponible > max_total:
            errores.append(
                f"  {j}: produccion={disponible:,.2f} m3; "
                f"rango admisible=[{min_total:,.2f}, {max_total:,.2f}] m3."
            )
    if errores:
        raise ValueError(
            "El problema no es factible con los datos ingresados:\n"
            + "\n".join(errores)
            + "\n"
        )


def construir_modelo(produccion, distancia):
    model = pulp.LpProblem("distribucion_madera_mulchen", pulp.LpMinimize)

    x = {}
    for i in DESTINOS:
        for j in PRODUCTOS:
            x[i, j] = pulp.LpVariable(
                f"x_{i}_{j}", lowBound=0.0, cat=pulp.LpContinuous
            )

    model += pulp.lpSum(
        COSTO_KM * distancia[i] * x[i, j]
        for i in DESTINOS
        for j in PRODUCTOS
    ), "Costo_Total_Transporte"

    for j in PRODUCTOS:
        model += (
            pulp.lpSum(x[i, j] for i in DESTINOS) == produccion[j],
            f"Asignacion_Total_{j}",
        )

    L, U = build_bounds()
    for i in DESTINOS:
        for j in PRODUCTOS:
            if L[i, j] > 0 or U[i, j] > 0:
                model += (x[i, j] >= L[i, j], f"Minimo_{i}_{j}")
                model += (x[i, j] <= U[i, j], f"Maximo_{i}_{j}")
            else:
                model += (x[i, j] == 0.0, f"Nulo_{i}_{j}")

    return model, x


def exportar_resultados(model, x, distancia, rutas):
    print("\n" + "=" * 72)
    print("PLAN OPTIMO DE DISTRIBUCION")
    print("=" * 72)

    filas = []

    for j in PRODUCTOS:
        print(f"\nProducto {j}:")
        total_producto = 0.0
        for i in DESTINOS:
            volumen = pulp.value(x[i, j])
            if volumen is None or volumen < 1e-6:
                continue
            costo = COSTO_KM * distancia[i] * volumen
            total_producto += volumen
            print(
                f"  {i.replace('_', ' '):28s}"
                f"{volumen:12,.2f} m3"
                f" | costo: ${costo:,.0f} CLP"
            )
            filas.append({
                "destino": i,
                "producto": j,
                "distancia_km": distancia[i],
                "volumen_m3": round(volumen, 2),
                "costo_clp": round(costo, 2),
            })
        print(f"  Total distribuido de {j}: {total_producto:,.2f} m3")

    obj = pulp.value(model.objective)
    print("\n" + "-" * 72)
    print(f"Costo total minimo: ${obj:,.0f} CLP")
    print("-" * 72)

    csv_out = PARTE2 / "solucion_distribucion.csv"
    with open(csv_out, "w", newline="", encoding="utf-8-sig") as f:
        fields = ["destino", "producto", "distancia_km", "volumen_m3", "costo_clp"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(filas)
    print(f"\nResultados guardados en: {csv_out}")

    origen = {"nombre": "Planta Aserradero CMPC Mulchen", "lon": -72.2412, "lat": -37.7165}

    destinos_geo = {
        "Puerto_Coronel":       {"nombre": "Puerto Coronel",              "lon": -73.1432, "lat": -37.0298},
        "Puerto_San_Vicente":   {"nombre": "Puerto San Vicente",           "lon": -73.1311, "lat": -36.7214},
        "Puerto_Lirquen":       {"nombre": "Puerto Lirquen",              "lon": -72.9764, "lat": -36.7095},
        "Reman_Coronel":        {"nombre": "Planta Reman. CMPC Coronel",  "lon": -73.1345, "lat": -37.0253},
        "Reman_Los_Angeles":    {"nombre": "Planta Reman. CMPC Los Angeles","lon": -72.6975, "lat": -37.2618},
        "Plywood_Collipulli":   {"nombre": "Planta Plywood CMPC Collipulli","lon": -72.419,  "lat": -37.9547},
    }

    produccion_total = {}
    for j in PRODUCTOS:
        total = 0.0
        for i in DESTINOS:
            v = pulp.value(x[i, j])
            if v and v > 1e-6:
                total += v
        produccion_total[j] = round(total, 2)

    json_out = PARTE2 / "solucion_distribucion.json"
    json_out.write_text(
        json.dumps({
            "origen": origen,
            "destinos": destinos_geo,
            "distancias": distancia,
            "rutas": rutas,
            "costos_unitarios": {i: COSTO_KM * distancia[i] for i in DESTINOS},
            "produccion": produccion_total,
            "despachos": filas,
            "costo_total_clp": round(obj, 2),
            "productos": PRODUCTOS,
            "destinos_list": DESTINOS,
            "parte1": {
                "fuente": "RESUMEN_PARTE1.md",
                "produccion_total_m3": round(sum(produccion_total.values()), 2),
            },
            "replicas": {},
            "transporte": _transporte_info(distancia),
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Datos para dashboard guardados en: {json_out}")

    model.writeLP(str(PARTE2 / "modelo_distribucion.lp"))
    return filas


TRUCK_CAPACITY_M3 = 30.0
TRUCK_COST_PER_KM = 1200.0
TRUCK_COST_PER_TRIP_FIXED = 50000.0
TRAIN_COST_PER_M3_KM = 30.0
TRAIN_TRANSFER_COST_M3 = 3500.0
TRAIN_STATIONS = {"Laja", "Concepcion", "Talcahuano", "Coronel"}


def _transporte_info(distancia):
    """Genera datos de transporte multimodal para el dashboard."""
    camiones = {}
    for dest in DESTINOS:
        viajes = {}
        for prod in PRODUCTOS:
            viajes[prod] = 0
        camiones[dest] = {
            "capacidad_m3": TRUCK_CAPACITY_M3,
            "costo_por_km": TRUCK_COST_PER_KM,
            "costo_fijo_por_viaje": TRUCK_COST_PER_TRIP_FIXED,
            "viajes": viajes,
        }

    tren = {
        "costo_m3_km": TRAIN_COST_PER_M3_KM,
        "costo_transferencia_m3": TRAIN_TRANSFER_COST_M3,
        "estaciones_cercanas": sorted(TRAIN_STATIONS),
        "aplicable_a": [
            "Puerto_Coronel",
            "Puerto_San_Vicente",
            "Puerto_Lirquen",
            "Reman_Coronel",
        ],
        "no_aplicable_a": [
            "Reman_Los_Angeles",
            "Plywood_Collipulli",
        ],
        "nota": "Requiere transbordo en Laja (~30 km desde Mulchen). "
               "Solo competitivo para volumenes altos a puertos/Coronel.",
        "costo_total_estimado_m3": {},
    }

    return {"camiones": camiones, "tren": tren}


def _actualizar_transporte(json_data):
    """Rellena los viajes de camiones y costos de tren con los despachos reales."""
    cam = json_data["transporte"]["camiones"]
    tren = json_data["transporte"]["tren"]
    import math
    for d in json_data["despachos"]:
        dest = d["destino"]
        prod = d["producto"]
        vol = d["volumen_m3"]
        if vol < 1e-6:
            continue
        viajes = int(math.ceil(vol / TRUCK_CAPACITY_M3))
        cam[dest]["viajes"][prod] = viajes
        d["camiones_viajes"] = viajes
        d["camiones_costo_total"] = round(
            viajes * (d["distancia_km"] * TRUCK_COST_PER_KM + TRUCK_COST_PER_TRIP_FIXED)
        )
        if dest in tren["aplicable_a"]:
            costo_tren = vol * (d["distancia_km"] * TRAIN_COST_PER_M3_KM + TRAIN_TRANSFER_COST_M3)
            tren["costo_total_estimado_m3"].setdefault(dest, {})[prod] = round(costo_tren)
        d["tren_costo_estimado"] = (
            round(vol * (d["distancia_km"] * TRAIN_COST_PER_M3_KM + TRAIN_TRANSFER_COST_M3))
            if dest in tren["aplicable_a"] else None
        )


def _exportar_json_final(distancia, rutas, resultados_replicas):
    """Escribe solucion_distribucion.json con datos de todas las replicas."""
    origen = {"nombre": "Planta Aserradero CMPC Mulchen", "lon": -72.2412, "lat": -37.7165}
    destinos_geo = {
        "Puerto_Coronel":       {"nombre": "Puerto Coronel",              "lon": -73.1432, "lat": -37.0298},
        "Puerto_San_Vicente":   {"nombre": "Puerto San Vicente",           "lon": -73.1311, "lat": -36.7214},
        "Puerto_Lirquen":       {"nombre": "Puerto Lirquen",              "lon": -72.9764, "lat": -36.7095},
        "Reman_Coronel":        {"nombre": "Planta Reman. CMPC Coronel",  "lon": -73.1345, "lat": -37.0253},
        "Reman_Los_Angeles":    {"nombre": "Planta Reman. CMPC Los Angeles","lon": -72.6975, "lat": -37.2618},
        "Plywood_Collipulli":   {"nombre": "Planta Plywood CMPC Collipulli","lon": -72.419,  "lat": -37.9547},
    }

    base = {
        "origen": origen,
        "destinos": destinos_geo,
        "distancias": distancia,
        "rutas": rutas,
        "costos_unitarios": {i: COSTO_KM * distancia[i] for i in DESTINOS},
        "productos": PRODUCTOS,
        "destinos_list": DESTINOS,
        "transporte": _transporte_info(distancia),
    }

    replicas_dict = {}
    for key, data in resultados_replicas.items():
        replicas_dict[key] = {
            "produccion": data["produccion"],
            "despachos": data["despachos"],
            "costo_total_clp": data["costo_total_clp"],
        }

    avg = resultados_replicas.get("avg", {})
    base["produccion"] = avg.get("produccion", {})
    base["despachos"] = avg.get("despachos", [])
    base["costo_total_clp"] = avg.get("costo_total_clp", 0)
    base["replicas"] = replicas_dict
    base["parte1"] = {
        "fuente": "product_outputs.csv (5 replicas)",
        "produccion_total_m3": round(sum(avg.get("produccion", {}).values()), 2),
    }
    _actualizar_transporte(base)
    for rkey in replicas_dict:
        temp = {
            "despachos": replicas_dict[rkey]["despachos"],
            "transporte": _transporte_info(distancia),
        }
        _actualizar_transporte(temp)
        replicas_dict[rkey]["despachos"] = temp["despachos"]
        replicas_dict[rkey]["transporte"] = temp["transporte"]

    json_out = PARTE2 / "solucion_distribucion.json"
    json_out.write_text(
        json.dumps(base, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Datos para dashboard guardados en: {json_out}")

    # CSV
    despachos_avg = base.get("despachos", [])
    if despachos_avg:
        csv_out = PARTE2 / "solucion_distribucion.csv"
        with open(csv_out, "w", newline="", encoding="utf-8-sig") as f:
            fields = ["destino", "producto", "distancia_km", "volumen_m3", "costo_clp",
                      "camiones_viajes", "camiones_costo_total", "tren_costo_estimado"]
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(despachos_avg)
        print(f"CSV guardado en: {csv_out}")

    # Exportar formulacion LP para una replica de ejemplo
    prod_avg = avg.get("produccion", {})
    if prod_avg:
        model, _ = construir_modelo(prod_avg, distancia)
        model.writeLP(str(PARTE2 / "modelo_distribucion.lp"))


def _run_modelo(produccion, distancia, label):
    """Ejecuta el modelo para una produccion dada. Retorna dict de resultados."""
    L, U = build_bounds()
    validar_factibilidad(produccion, L, U)
    model, x = construir_modelo(produccion, distancia)
    model.solve(pulp.PULP_CBC_CMD(msg=False))
    if model.status != pulp.LpStatusOptimal:
        print(f"  {label}: {pulp.LpStatus[model.status]} — saltando")
        return {}
    filas = []
    for j in PRODUCTOS:
        for i in DESTINOS:
            vol = pulp.value(x[i, j])
            if vol is None or vol < 1e-6:
                continue
            filas.append({
                "destino": i,
                "producto": j,
                "distancia_km": distancia[i],
                "volumen_m3": round(vol, 2),
                "costo_clp": round(COSTO_KM * distancia[i] * vol, 2),
            })
    obj = pulp.value(model.objective)
    prod_total = {}
    for j in PRODUCTOS:
        total = sum(d["volumen_m3"] for d in filas if d["producto"] == j)
        prod_total[j] = round(total, 2)
    return {"produccion": prod_total, "despachos": filas, "costo_total_clp": round(obj, 2)}


def main():
    try:
        from pathlib import Path
        distancia, rutas = load_distances()
        if distancia is None:
            sys.exit(1)

        prod_por_replica = load_produccion_por_replica()
        resultados = {}

        if prod_por_replica:
            for rep in sorted(prod_por_replica):
                prod = prod_por_replica[rep]
                print(f"Resolviendo replica {rep}: P1={prod['P1']:,.0f} P2={prod['P2']:,.0f} P3={prod['P3']:,.0f}")
                r = _run_modelo(prod, distancia, f"Replica {rep}")
                if r:
                    resultados[str(rep)] = r
                    print(f"  Costo: ${r['costo_total_clp']:,.0f}")

            prod_avg = {}
            for p in PRODUCTOS:
                vals = [prod_por_replica[rep][p] for rep in sorted(prod_por_replica)]
                prod_avg[p] = round(sum(vals) / len(vals), 2)
            print(f"Resolviendo promedio: P1={prod_avg['P1']:,.0f} P2={prod_avg['P2']:,.0f} P3={prod_avg['P3']:,.0f}")
            r = _run_modelo(prod_avg, distancia, "Promedio")
            if r:
                resultados["avg"] = r
        else:
            prod_avg = load_produccion()
            print(f"Resolviendo con produccion promedio: P1={prod_avg['P1']:,.0f} P2={prod_avg['P2']:,.0f} P3={prod_avg['P3']:,.0f}")
            r = _run_modelo(prod_avg, distancia, "Promedio")
            if r:
                resultados["avg"] = r

        if not resultados:
            print("No se obtuvo solucion para ninguna replica.")
            sys.exit(1)

        _exportar_json_final(distancia, rutas, resultados)

        print("\n" + "=" * 72)
        print("PLAN OPTIMO — PROMEDIO 5 REPLICAS")
        print("=" * 72)
        for d in resultados.get("avg", {}).get("despachos", []):
            print(f"  {d['producto']:3s} → {d['destino'].replace('_',' '):28s} {d['volumen_m3']:10,.0f} m³ | ${d['costo_clp']:>12,.0f}")
        print(f"  COSTO TOTAL: ${resultados.get('avg', {}).get('costo_total_clp', 0):,.0f}")

        print("\n" + "-" * 72)
        print("COMPARATIVO POR REPLICA")
        print("-" * 72)
        for k in sorted(resultados):
            if k == "avg":
                continue
            r = resultados[k]
            print(f"  Rep {k}: ${r['costo_total_clp']:>14,.0f}")
        if "avg" in resultados:
            avg = resultados["avg"]
            costs = [resultados[k]["costo_total_clp"] for k in resultados if k != "avg"]
            if costs:
                import numpy as np
                print(f"  Avg:   ${avg['costo_total_clp']:>14,.0f}")
                print(f"  Std:   ${np.std(costs):>14,.0f}")

    except ValueError as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nEjecucion cancelada por el usuario.")
        sys.exit(1)


if __name__ == "__main__":
    main()
