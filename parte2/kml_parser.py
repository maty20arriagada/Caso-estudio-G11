"""
kml_parser.py
=========================================================================
Extrae las rutas (LineString) desde DSP_distancias.kml, calcula la
distancia Haversine acumulada de cada ruta desde Mulchen hasta cada
destino, y exporta los resultados a distancias.json.

Cada carpeta de ruta (posterior al Folder "DSP") contiene una LineString
con el trazado real de la carretera, ademas de un Point para Mulchen
(origen) y otro para el destino.
=========================================================================
"""

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

PARTE2 = Path(__file__).resolve().parent
KML_FILE = PARTE2 / "DSP_distancias.kml"
OUT_FILE = PARTE2 / "distancias.json"

NS = {"kml": "http://www.opengis.net/kml/2.2"}


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Distancia en kilometros entre dos puntos geograficos (formula Haversine).
    """
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def parse_coordinates(coord_text: str) -> list[tuple[float, float]]:
    """
    Convierte texto de coordenadas KML a lista de (lon, lat).
    Ej: '-72.24115,-37.71651,0 -72.24119,-37.71662,0 ...'
    """
    points = []
    for token in coord_text.strip().split():
        token = token.strip()
        if not token:
            continue
        parts = token.split(",")
        if len(parts) >= 2:
            points.append((float(parts[0]), float(parts[1])))
    return points


def line_distance(points: list[tuple[float, float]]) -> float:
    """Distancia total acumulada de una secuencia de puntos (km)."""
    total = 0.0
    for i in range(len(points) - 1):
        lon1, lat1 = points[i]
        lon2, lat2 = points[i + 1]
        total += haversine(lon1, lat1, lon2, lat2)
    return total


KML_TO_MODEL: dict[str, str] = {
    "Puerto Coronel": "Puerto_Coronel",
    "Puerto San Vicente": "Puerto_San_Vicente",
    "Puerto Lirquen": "Puerto_Lirquen",
    "Puerto Lirquén": "Puerto_Lirquen",
    "Planta Reman. CMPC Coronel": "Reman_Coronel",
    "Planta Reman. CMPC Los Ángeles": "Reman_Los_Angeles",
    "Planta Plywood CMPC Collipulli": "Plywood_Collipulli",
}


def extract_routes() -> tuple[dict[str, float], dict[str, list[list[float]]]]:
    """
    Extrae las distancias y coordenadas desde el KML.
    Retorna (distancias, coordenadas) donde:
      distancias   = {nombre_modelo: distancia_km}
      coordenadas  = {nombre_modelo: [[lon, lat], [lon, lat], ...]}
    """
    tree = ET.parse(KML_FILE)
    root = tree.getroot()

    distancias: dict[str, float] = {}
    coordenadas: dict[str, list[list[float]]] = {}
    seen = set()

    for folder in root.findall(".//kml:Folder", NS):
        folder_name_el = folder.find("kml:name", NS)
        folder_name = folder_name_el.text.strip() if folder_name_el is not None else ""

        if folder_name == "DSP":
            continue

        line_el = folder.find(".//kml:LineString/kml:coordinates", NS)
        if line_el is None or line_el.text is None:
            continue

        coords = parse_coordinates(line_el.text)
        if len(coords) < 2:
            continue

        distance_km = line_distance(coords)

        model_name = KML_TO_MODEL.get(folder_name)
        if model_name is None:
            dest_placemarks = folder.findall(".//kml:Placemark", NS)
            for pm in dest_placemarks:
                name_el = pm.find("kml:name", NS)
                if name_el is not None:
                    n = name_el.text.strip()
                    if n in KML_TO_MODEL:
                        model_name = KML_TO_MODEL[n]
                        break

        if model_name is None:
            continue

        if model_name in seen:
            continue
        seen.add(model_name)
        distancias[model_name] = round(distance_km, 2)
        coordenadas[model_name] = [[lon, lat] for lon, lat in coords]

    return distancias, coordenadas


def main():
    distancias, coordenadas = extract_routes()

    mulchen = (-72.2412, -37.7165)
    for dest_name, dist in distancias.items():
        dest_label = dest_name.replace("_", " ")
        npoints = len(coordenadas.get(dest_name, []))
        print(f"  {dest_label:<28s} {dist:10.2f} km  ({npoints} puntos)")

    OUT_FILE.write_text(
        json.dumps(
            {
                "origen": {
                    "nombre": "Planta Aserradero CMPC Mulchen",
                    "lon": mulchen[0],
                    "lat": mulchen[1],
                },
                "distancias": distancias,
                "rutas": coordenadas,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nDistancias y coordenadas guardadas en: {OUT_FILE}")


if __name__ == "__main__":
    main()
