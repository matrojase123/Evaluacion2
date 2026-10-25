

import requests
import urllib.parse
import os

# ==========================================
# CONFIGURACIÓN DE GRAPHHOPPER
# ==========================================

route_url = "https://graphhopper.com/api/1/route"
key = os.getenv("GRAPHHOPPER_API_KEY","f8a43e8c-3015-47ed-a5af-dd8cfa88b04b")


# ==========================================
# FUNCIÓN DE GEOCODIFICACIÓN
# ==========================================

def geocoding(location, key):

    while location.strip() == "":
        location = input("Ingrese nuevamente la ubicación: ")

    geocode_url = "https://graphhopper.com/api/1/geocode?"

    url = geocode_url + urllib.parse.urlencode({
        "q": location,
        "limit": "1",
        "key": key
    })

    try:
        replydata = requests.get(url, timeout=15)
        json_data = replydata.json()
        json_status = replydata.status_code

        if json_status == 200 and json_data.get("hits"):

            hit = json_data["hits"][0]

            lat = hit["point"]["lat"]
            lng = hit["point"]["lng"]
            name = hit["name"]
            value = hit.get("osm_value", "desconocido")

            country = hit.get("country", "")
            state = hit.get("state", "")

            if state and country:
                new_loc = f"{name}, {state}, {country}"
            elif state:
                new_loc = f"{name}, {state}"
            elif country:
                new_loc = f"{name}, {country}"
            else:
                new_loc = name

            # Ocultar API Key al imprimir
            print(
                f"URL de geocodificación para {new_loc} "
                f"(Tipo de ubicación: {value})"
            )

            print(
                geocode_url + urllib.parse.urlencode({
                    "q": location,
                    "limit": "1",
                    "key": "OCULTO"
                })
            )

        else:
            lat = None
            lng = None
            new_loc = location

            print(
                "Estado de la API de geocodificación:",
                json_status
            )

            print(
                "Error:",
                json_data.get(
                    "message",
                    "No se encontró la ubicación"
                )
            )

    except (requests.RequestException, ValueError) as error:

        print("Error de geocodificación:", error)

        json_status = 0
        lat = None
        lng = None
        new_loc = location

    return json_status, lat, lng, new_loc


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

while True:

    print("\n+++++++++++++++++++++++++++++++++++++++++++++")
    print("Perfiles de transporte disponibles:")
    print("+++++++++++++++++++++++++++++++++++++++++++++")
    print("auto, bicicleta, a pie")
    print("Escriba 's' o 'salir' para terminar.")
    print("+++++++++++++++++++++++++++++++++++++++++++++")

    # Traducción entre lo que escribe el usuario
    # y lo que necesita GraphHopper.
    vehicle_translation = {
        "auto": "car",
        "bicicleta": "bike",
        "a pie": "foot"
    }

    vehicle_input = input(
        "Ingrese un perfil de transporte: "
    ).strip().lower()

    # ==========================================
    # OPCIÓN PARA SALIR
    # ==========================================

    if vehicle_input in ["s", "salir"]:
        print("Saliendo del programa...")
        break

    # ==========================================
    # VALIDAR PERFIL
    # ==========================================

    if vehicle_input not in vehicle_translation:

        print(
            "No se ingresó un perfil válido. "
            "Se utilizará el perfil automóvil."
        )

        vehicle_input = "auto"

    # Valor en inglés que utilizará GraphHopper
    vehicle = vehicle_translation[vehicle_input]


    # ======================================
    # UBICACIÓN DE ORIGEN
    # ======================================

    loc1 = input(
        "Ingrese la ubicación de origen "
        "(o 's'/'salir' para terminar): "
    ).strip()

    if loc1.lower() in ["s", "salir"]:
        print("Saliendo del programa...")
        break

    orig = geocoding(loc1, key)

    if orig[1] is None or orig[2] is None:
        print("La ubicación de origen no es válida.")
        continue


    # ======================================
    # UBICACIÓN DE DESTINO
    # ======================================

    loc2 = input(
        "Ingrese la ubicación de destino "
        "(o 's'/'salir' para terminar): "
    ).strip()

    if loc2.lower() in ["s", "salir"]:
        print("Saliendo del programa...")
        break

    dest = geocoding(loc2, key)

    if dest[1] is None or dest[2] is None:
        print("La ubicación de destino no es válida.")
        continue


    # ======================================
    # CONSTRUIR URL DE ROUTING API
    # ======================================

    parameters = {
        "key": key,

        # GraphHopper recibe car, bike o foot
        "profile": vehicle,

        "point": [
            f"{orig[1]},{orig[2]}",
            f"{dest[1]},{dest[2]}"
        ],

        "instructions": "true",

        # Solicitar instrucciones en español
        "locale": "es",

        "calc_points": "true"
    }

    try:

        response = requests.get(
            route_url,
            params=parameters,
            timeout=30
        )

        status = response.status_code
        json_data = response.json()

    except (requests.RequestException, ValueError) as error:

        print("Error de la API de rutas:", error)
        continue


    # ======================================
    # INFORMACIÓN DE LA API
    # ======================================

    print("=================================================")
    print("Estado de la API de rutas:", status)

    # Mostrar URL sin exponer la API Key
    safe_parameters = parameters.copy()
    safe_parameters["key"] = "OCULTO"

    safe_url = requests.Request(
        "GET",
        route_url,
        params=safe_parameters
    ).prepare().url

    print("URL de la API de rutas:")
    print(safe_url)

    print("=================================================")


    # Mostrar el nombre en español
    print(
        f"Ruta desde {orig[3]} hasta {dest[3]} "
        f"mediante {vehicle_input}"
    )

    print("=================================================")


    # ======================================
    # VALIDAR RESULTADO DE ROUTING API
    # ======================================

    if status == 200 and json_data.get("paths"):

        path = json_data["paths"][0]

        distance = path["distance"]
        time = path["time"]


        # ==================================
        # CONVERSIÓN DE DISTANCIA
        # ==================================

        km = distance / 1000
        miles = km / 1.609344


        # ==================================
        # CONVERSIÓN DE TIEMPO
        # ==================================

        seconds = int(time / 1000)

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60


        # ==================================
        # MOSTRAR RESULTADOS
        # ==================================

        print(
            f"Distancia recorrida: "
            f"{miles:.2f} millas / {km:.2f} km"
        )

        print(
            f"Duración del viaje: "
            f"{hours:02d}:{minutes:02d}:{secs:02d}"
        )

        print("=================================================")


        # ==================================
        # NARRATIVA DEL VIAJE
        # ==================================

        print("NARRATIVA DEL VIAJE")
        print("=================================================")

        instructions = path.get("instructions", [])

        for number, instruction in enumerate(
            instructions,
            start=1
        ):

            text = instruction.get("text", "")

            step_distance = instruction.get(
                "distance",
                0
            )

            step_km = step_distance / 1000
            step_miles = step_km / 1.609344

            print(
                f"{number}. {text} "
                f"({step_km:.2f} km / "
                f"{step_miles:.2f} millas)"
            )

        print("=================================================")


    # ======================================
    # ERROR DE ROUTING
    # ======================================

    else:

        print(
            "Mensaje de error:",
            json_data.get(
                "message",
                "No se encontró una conexión "
                "entre las ubicaciones"
            )
        )

        print("*************************************************")
