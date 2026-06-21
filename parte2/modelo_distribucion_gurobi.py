"""
Modelo de distribución de madera desde la planta CMPC Mulchén.

Requiere:
    pip install gurobipy

Al ejecutar, el programa solicita:
1. Producción disponible de P1, P2 y P3.
2. Distancia desde Mulchén hasta cada destino.

Resultados:
- Muestra el plan óptimo en pantalla.
- Guarda el modelo como modelo_distribucion.lp.
- Guarda los despachos como solucion_distribucion.csv.
"""

import csv
import sys

import gurobipy as gp
from gurobipy import GRB


# ============================================================
# 1. CONJUNTOS
# ============================================================

DESTINOS = [
    "Puerto_Coronel",
    "Puerto_San_Vicente",
    "Puerto_Lirquen",
    "Reman_Coronel",
    "Reman_Los_Angeles",
    "Plywood_Collipulli",
]

PRODUCTOS = ["P1", "P2", "P3"]


# ============================================================
# 2. PARÁMETROS FIJOS
# ============================================================

# Costo de transportar 1 m3 durante 1 km [CLP/(m3·km)]
COSTO_KM = 100.0

# Inicialización de límites en cero.
# Para una combinación destino-producto no permitida:
# L[i,j] = U[i,j] = 0.
L = {(i, j): 0.0 for i in DESTINOS for j in PRODUCTOS}
U = {(i, j): 0.0 for i in DESTINOS for j in PRODUCTOS}

# Producto P1: madera verde tratada
L["Puerto_Coronel", "P1"] = 1200.0
U["Puerto_Coronel", "P1"] = 12000.0

L["Reman_Coronel", "P1"] = 1500.0
U["Reman_Coronel", "P1"] = 8000.0

L["Reman_Los_Angeles", "P1"] = 1300.0
U["Reman_Los_Angeles", "P1"] = 6000.0

# Producto P2: madera seca clasificada
L["Puerto_Lirquen", "P2"] = 1500.0
U["Puerto_Lirquen", "P2"] = 8000.0

L["Puerto_San_Vicente", "P2"] = 1500.0
U["Puerto_San_Vicente", "P2"] = 8000.0

L["Reman_Los_Angeles", "P2"] = 1500.0
U["Reman_Los_Angeles", "P2"] = 5000.0

L["Plywood_Collipulli", "P2"] = 1500.0
U["Plywood_Collipulli", "P2"] = 5000.0

# Producto P3: madera impregnada
L["Puerto_Coronel", "P3"] = 1200.0
U["Puerto_Coronel", "P3"] = 10000.0

L["Puerto_San_Vicente", "P3"] = 800.0
U["Puerto_San_Vicente", "P3"] = 12000.0

L["Plywood_Collipulli", "P3"] = 1000.0
U["Plywood_Collipulli", "P3"] = 4000.0


# ============================================================
# 3. LECTURA Y VALIDACIÓN DE DATOS
# ============================================================

def leer_numero_no_negativo(mensaje: str) -> float:
    """Solicita un número real no negativo."""
    while True:
        entrada = input(mensaje).strip().replace(",", ".")
        try:
            valor = float(entrada)
            if valor < 0:
                print("El valor debe ser mayor o igual que cero.")
                continue
            return valor
        except ValueError:
            print("Entrada inválida. Ingrese un número, por ejemplo: 12500.5")


def leer_datos():
    """Lee producción y distancias desde teclado."""
    print("\n=== PRODUCCIÓN DISPONIBLE ===")
    produccion = {
        j: leer_numero_no_negativo(
            f"Producción disponible de {j} [m3]: "
        )
        for j in PRODUCTOS
    }

    print("\n=== DISTANCIAS DESDE MULCHÉN ===")
    distancia = {
        i: leer_numero_no_negativo(
            f"Distancia Mulchén -> {i.replace('_', ' ')} [km]: "
        )
        for i in DESTINOS
    }

    return produccion, distancia


def validar_factibilidad_previa(produccion):
    """
    Comprueba la condición necesaria de factibilidad:
        sum_i L[i,j] <= P[j] <= sum_i U[i,j]
    """
    errores = []

    for j in PRODUCTOS:
        minimo_total = sum(L[i, j] for i in DESTINOS)
        maximo_total = sum(U[i, j] for i in DESTINOS)
        disponible = produccion[j]

        if disponible < minimo_total or disponible > maximo_total:
            errores.append(
                f"{j}: producción={disponible:,.2f} m3; "
                f"rango admisible=[{minimo_total:,.2f}, "
                f"{maximo_total:,.2f}] m3."
            )

    if errores:
        detalle = "\n".join(f"- {error}" for error in errores)
        raise ValueError(
            "\nEl problema no es factible con los datos ingresados:\n"
            f"{detalle}\n"
        )


# ============================================================
# 4. CONSTRUCCIÓN DEL MODELO
# ============================================================

def construir_modelo(produccion, distancia):
    modelo = gp.Model("distribucion_madera_mulchen")

    # x[i,j]: m3 del producto j enviados al destino i.
    x = modelo.addVars(
        DESTINOS,
        PRODUCTOS,
        lb=0.0,
        vtype=GRB.CONTINUOUS,
        name="x",
    )

    # Función objetivo:
    # min sum_i sum_j COSTO_KM * distancia[i] * x[i,j]
    modelo.setObjective(
        gp.quicksum(
            COSTO_KM * distancia[i] * x[i, j]
            for i in DESTINOS
            for j in PRODUCTOS
        ),
        GRB.MINIMIZE,
    )

    # Toda la producción de cada producto debe distribuirse.
    for j in PRODUCTOS:
        modelo.addConstr(
            gp.quicksum(x[i, j] for i in DESTINOS) == produccion[j],
            name=f"asignacion_total_{j}",
        )

    # Mínimo contractual y capacidad máxima por destino-producto.
    for i in DESTINOS:
        for j in PRODUCTOS:
            modelo.addConstr(
                x[i, j] >= L[i, j],
                name=f"minimo_{i}_{j}",
            )
            modelo.addConstr(
                x[i, j] <= U[i, j],
                name=f"maximo_{i}_{j}",
            )

    return modelo, x


# ============================================================
# 5. SOLUCIÓN Y EXPORTACIÓN
# ============================================================

def mostrar_y_exportar_solucion(modelo, x, distancia):
    print("\n" + "=" * 72)
    print("PLAN ÓPTIMO DE DISTRIBUCIÓN")
    print("=" * 72)

    filas = []

    for j in PRODUCTOS:
        print(f"\nProducto {j}:")
        total_producto = 0.0

        for i in DESTINOS:
            volumen = x[i, j].X

            # Solo se muestran despachos positivos.
            if volumen > 1e-6:
                costo = COSTO_KM * distancia[i] * volumen
                total_producto += volumen

                print(
                    f"  {i.replace('_', ' '):28s}"
                    f"{volumen:12,.2f} m3"
                    f" | costo: ${costo:,.0f} CLP"
                )

                filas.append(
                    {
                        "destino": i,
                        "producto": j,
                        "distancia_km": distancia[i],
                        "volumen_m3": volumen,
                        "costo_clp": costo,
                    }
                )

        print(f"  Total distribuido de {j}: {total_producto:,.2f} m3")

    print("\n" + "-" * 72)
    print(f"Costo total mínimo: ${modelo.ObjVal:,.0f} CLP")
    print("-" * 72)

    archivo_salida = "solucion_distribucion.csv"
    with open(archivo_salida, "w", newline="", encoding="utf-8-sig") as archivo:
        campos = [
            "destino",
            "producto",
            "distancia_km",
            "volumen_m3",
            "costo_clp",
        ]
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"\nResultados guardados en: {archivo_salida}")


def main():
    try:
        produccion, distancia = leer_datos()
        validar_factibilidad_previa(produccion)

        modelo, x = construir_modelo(produccion, distancia)

        # Guarda la formulación para poder revisarla.
        modelo.write("modelo_distribucion.lp")

        # Resuelve el modelo.
        modelo.optimize()

        if modelo.Status == GRB.OPTIMAL:
            mostrar_y_exportar_solucion(modelo, x, distancia)

        elif modelo.Status == GRB.INFEASIBLE:
            print("\nEl modelo es infactible.")
            modelo.computeIIS()
            modelo.write("modelo_infactible.ilp")
            print(
                "Se guardó modelo_infactible.ilp con las restricciones "
                "que generan el conflicto."
            )

        elif modelo.Status == GRB.UNBOUNDED:
            print("\nEl modelo es no acotado.")

        elif modelo.Status == GRB.INF_OR_UNBD:
            print("\nEl modelo es infactible o no acotado.")

        else:
            print(
                f"\nLa optimización terminó con el estado "
                f"{modelo.Status}."
            )

    except gp.GurobiError as error:
        print(f"\nError de Gurobi {error.errno}: {error}")
        sys.exit(1)

    except ValueError as error:
        print(error)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nEjecución cancelada por el usuario.")
        sys.exit(1)


if __name__ == "__main__":
    main()
