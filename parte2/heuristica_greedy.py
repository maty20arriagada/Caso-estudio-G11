"""
heuristica_greedy.py
=========================================================================
Heuristica GREEDY para la red de distribucion (Parte 2).

Regla: "cumplir minimos -> llenar el destino mas cercano primero".
Para cada producto (independiente):
  1) asignar el minimo contractual L[i,j] a cada destino i,
  2) residual R = P_j - sum(L[i,j]),
  3) ordenar destinos por costo unitario c_i = 100 * d_i (ascendente),
  4) llenar el mas barato primero hasta U[i,j]-L[i,j], hasta agotar R.

Como el costo unitario depende solo del destino (origen unico) y el
problema es separable por producto con cotas tipo caja, esta regla es
la de la MOCHILA CONTINUA: es OPTIMA. Se verifica comparando contra el
optimo del modelo LP exacto (solucion_distribucion.json).

Ventaja: NO requiere solver (es autocontenida; O(n log n) por producto).

Salida: greedy_solucion.json  (consumido por build_dashboard.py)
=========================================================================
"""
import json
from pathlib import Path

import pandas as pd

PARTE2 = Path(__file__).resolve().parent
BASE = PARTE2.parent

DESTINOS = [
    "Puerto_Coronel", "Puerto_San_Vicente", "Puerto_Lirquen",
    "Reman_Coronel", "Reman_Los_Angeles", "Plywood_Collipulli",
]
PRODUCTOS = ["P1", "P2", "P3"]
COSTO_KM = 100.0


def build_bounds():
    L = {(i, j): 0.0 for i in DESTINOS for j in PRODUCTOS}
    U = {(i, j): 0.0 for i in DESTINOS for j in PRODUCTOS}
    L["Puerto_Coronel", "P1"], U["Puerto_Coronel", "P1"] = 1200.0, 12000.0
    L["Reman_Coronel", "P1"], U["Reman_Coronel", "P1"] = 1500.0, 8000.0
    L["Reman_Los_Angeles", "P1"], U["Reman_Los_Angeles", "P1"] = 1300.0, 6000.0
    L["Puerto_Lirquen", "P2"], U["Puerto_Lirquen", "P2"] = 1500.0, 8000.0
    L["Puerto_San_Vicente", "P2"], U["Puerto_San_Vicente", "P2"] = 1500.0, 8000.0
    L["Reman_Los_Angeles", "P2"], U["Reman_Los_Angeles", "P2"] = 1500.0, 5000.0
    L["Plywood_Collipulli", "P2"], U["Plywood_Collipulli", "P2"] = 1500.0, 5000.0
    L["Puerto_Coronel", "P3"], U["Puerto_Coronel", "P3"] = 1200.0, 10000.0
    L["Puerto_San_Vicente", "P3"], U["Puerto_San_Vicente", "P3"] = 800.0, 12000.0
    L["Plywood_Collipulli", "P3"], U["Plywood_Collipulli", "P3"] = 1000.0, 4000.0
    return L, U


def load_distances():
    data = json.loads((PARTE2 / "distancias.json").read_text(encoding="utf-8"))
    return data["distancias"]


def load_produccion_por_replica():
    df = pd.read_csv(BASE / "data" / "product_outputs.csv")
    prod = df.groupby(["replication", "product"])["volume_m3"].sum()
    reps = {}
    for (rep, p), v in prod.items():
        reps.setdefault(int(rep), {})[p] = round(float(v), 2)
    return reps


def greedy_allocate(prod, dist, L, U):
    """Heuristica greedy. Devuelve despachos, traza de decisiones y costo."""
    alloc = {i: {j: 0.0 for j in PRODUCTOS} for i in DESTINOS}
    steps = []
    for j in PRODUCTOS:
        dests = [i for i in DESTINOS if U[i, j] > 0]
        # 1) minimos obligatorios
        for i in dests:
            if L[i, j] > 0:
                alloc[i][j] = L[i, j]
                steps.append({"producto": j, "destino": i, "tipo": "minimo",
                              "vol": L[i, j], "cunit": COSTO_KM * dist[i]})
        # 2) residual; 3-4) llenar el mas barato primero
        residual = prod[j] - sum(L[i, j] for i in dests)
        for i in sorted(dests, key=lambda i: dist[i]):
            if residual <= 1e-9:
                break
            add = min(residual, U[i, j] - alloc[i][j])
            if add > 1e-9:
                alloc[i][j] += add
                residual -= add
                steps.append({"producto": j, "destino": i, "tipo": "llenado",
                              "vol": add, "cunit": COSTO_KM * dist[i]})
    cacum = 0.0
    for s in steps:
        s["cinc"] = s["vol"] * s["cunit"]
        cacum += s["cinc"]
        s["cacum"] = cacum
        s["vol"] = round(s["vol"], 2)
        s["cunit"] = round(s["cunit"], 2)
        s["cinc"] = round(s["cinc"], 2)
        s["cacum"] = round(s["cacum"], 2)
    cost = sum(alloc[i][j] * COSTO_KM * dist[i] for i in DESTINOS for j in PRODUCTOS)
    despachos = []
    for j in PRODUCTOS:
        for i in DESTINOS:
            if alloc[i][j] > 1e-6:
                despachos.append({"destino": i, "producto": j, "distancia_km": dist[i],
                                  "volumen_m3": round(alloc[i][j], 2),
                                  "costo_clp": round(alloc[i][j] * COSTO_KM * dist[i], 2)})
    return {"despachos": despachos, "steps": steps, "costo_total_clp": round(cost, 2)}


def main():
    dist = load_distances()
    L, U = build_bounds()
    prod_rep = load_produccion_por_replica()
    sol = json.loads((PARTE2 / "solucion_distribucion.json").read_text(encoding="utf-8"))
    lp = {k: sol["replicas"][k]["costo_total_clp"] for k in sol.get("replicas", {})}

    print("=" * 74)
    print("HEURISTICA GREEDY vs OPTIMO LP")
    print("=" * 74)
    print(f"{'Caso':10s}{'Greedy (CLP)':>20s}{'Optimo LP (CLP)':>20s}{'Brecha':>14s}")
    print("-" * 74)

    keys = sorted(prod_rep)
    greedy_out = {}
    maxgap = 0.0
    for rep in keys:
        g = greedy_allocate(prod_rep[rep], dist, L, U)
        lpc = lp.get(str(rep))
        gap = g["costo_total_clp"] - lpc if lpc is not None else None
        maxgap = max(maxgap, abs(gap)) if gap is not None else maxgap
        greedy_out[str(rep)] = {**g, "lp_costo_clp": lpc,
                                "gap_clp": round(gap, 2) if gap is not None else None,
                                "produccion": prod_rep[rep]}
        print(f"Rep {rep:<6d}{g['costo_total_clp']:>20,.0f}{lpc:>20,.0f}{gap:>14,.2f}")

    prod_avg = {j: round(sum(prod_rep[r][j] for r in keys) / len(keys), 2) for j in PRODUCTOS}
    g = greedy_allocate(prod_avg, dist, L, U)
    lpc = lp.get("avg")
    gap = g["costo_total_clp"] - lpc if lpc is not None else None
    greedy_out["avg"] = {**g, "lp_costo_clp": lpc,
                         "gap_clp": round(gap, 2) if gap is not None else None,
                         "produccion": prod_avg}
    print("-" * 74)
    print(f"{'Promedio':10s}{g['costo_total_clp']:>20,.0f}{lpc:>20,.0f}{gap:>14,.2f}")
    print("=" * 74)
    print(f"Brecha maxima Greedy-vs-LP entre replicas: {maxgap:,.4f} CLP")
    print("=> El Greedy alcanza el OPTIMO (brecha ~ 0; diferencias por redondeo)."
          if maxgap < 1.0 else "=> Revisar: brecha no nula.")

    out = {
        "costo_km": COSTO_KM,
        "destinos": DESTINOS,
        "productos": PRODUCTOS,
        "distancias": dist,
        "bounds": {
            "L": {f"{i}|{j}": L[i, j] for i in DESTINOS for j in PRODUCTOS if U[i, j] > 0},
            "U": {f"{i}|{j}": U[i, j] for i in DESTINOS for j in PRODUCTOS if U[i, j] > 0},
        },
        "greedy": greedy_out,
        "max_gap_clp": round(maxgap, 4),
    }
    (PARTE2 / "greedy_solucion.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n>> {PARTE2 / 'greedy_solucion.json'}")


if __name__ == "__main__":
    main()
