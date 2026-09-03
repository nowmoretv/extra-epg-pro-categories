import urllib.request
import xml.etree.ElementTree as ET
import os
import gzip
import base64
import copy
from datetime import datetime, timedelta, timezone

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Función auxiliar para decodificar en memoria
def _dec(b64_str):
    return base64.b64decode(b64_str.encode('utf-8')).decode('utf-8')

FUENTES_XML = {
    "Principal": _dec("aHR0cHM6Ly93d3cub3Blbi1lcGcuY29tL2dlbmVyYXRlL0NtTVlQYWI0RVkueG1sLmd6"),
    "Pluto TV": _dec("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL21hdHRodWlzbWFuL2kubWpoLm56L3JlZnMvaGVhZHMvbWFzdGVyL1BsdXRvVFYvZXMueG1s"),
    "Spain": _dec("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2RhdmlkbXVtYS9FUEdfZG9ibGVNL3JlZnMvaGVhZHMvbWFzdGVyL2d1aWFpcHR2LnhtbA=="),
    "Siguiente lista": "https://"
}

# ==============================================================================
# LIMPIEZA DE ETIQUETAS POR CATEGORÍA
# Define qué etiquetas eliminar de <programme> para aligerar el XML.
# Si pones una lista vacía [], se conserva todo.
# ==============================================================================

ETIQUETAS_LIMPIEZA = {
    "deportes": ["episode-num", "icon", "series-id", "sub-title", "category", "rating", "star-rating"],
    "nacionales": ["desc", "episode-num", "icon", "series-id", "sub-title", "category", "rating", "star-rating"],
    "cine": ["episode-num", "icon", "series-id", "sub-title", "rating", "star-rating"],
    "norteamerica": ["desc", "icon", "episode-num", "series-id", "sub-title", "category", "rating", "star-rating"]
}

# Etiquetas a eliminar por defecto si una categoría no está en el diccionario anterior
LIMPIEZA_DEFECTO = ["desc", "icon", "episode-num", "series-id"]

# ==============================================================================
# CANALES POR CATEGORÍA
# Estructura: "nombre_archivo": { "ID_ORIGINAL_XML": "ID_NUEVO_DESEADO" }
# ==============================================================================

CATEGORIAS = {
    "deportes": {
        "LaLigaTVHypermotion.es": "Hypermotion",
        "LaLigaTVHypermotion2.es": "Hypermotion 2",
        "LaLigaTVHypermotion3.es": "Hypermotion 3",
        "DSports.uy": "DSPORTS UY",
        "DSportsArgentina.uy": "DSPORTS AR",
        "DSports2.uy": "DSPORTS 2 UY",
        "DSportsPlus.uy": "DSPORTS Plus UY",
        "Setanta Sports.ee": "Setanta Sports EE",
        "Setanta Sports.lv": "Setanta Sports LV",
        "Setanta Sports 2.lv": "Setanta Sports 2 LV",
        "beINSports1.au": "beIN Sports 1 AU",
        "beINSports2.au": "beIN Sports 2 AU",
        "beINSports3.au": "beIN Sports 3 AU",
        "PremierSports1.uk": "Premier Sports UK",
        "PremierSports2.uk": "Premier Sports 2 UK",
        "Espn.ar": "ESPN AR",
        "Espn2.ar": "ESPN 2 AR",
        "Espn3.ar": "ESPN 3 AR",
        "Espn4.ar": "ESPN 4 AR",
        "Espn6.ar": "ESPN 6 AR",
        "EspnPremium.ar": "ESPN Premium AR",
        "ESPN HD.cl": "ESPN CL",
        "ESPN 2.cl": "ESPN 2 CL",
        "ESPN 3.cl": "ESPN 3 CL",
        "ESPN 4.cl": "ESPN 4 CL",
        "ESPN 5.cl": "ESPN 5 CL",
        "ESPN 6.cl": "ESPN 6 CL",
        "ESPN 7.cl": "ESPN 7 CL",
        "ESPN Premium.cl": "ESPN Premium CL",
        "ESPN.co": "ESPN CO",
        "ESPN 2.co": "ESPN 2 CO",
        "ESPN 3.co": "ESPN 3 CO",
        "ESPN 4.co": "ESPN 4 CO",
        "ESPN 5.co": "ESPN 5 CO",
        "ESPN 6 HD.co": "ESPN 6 CO",
        "ESPN 7 HD.co": "ESPN 7 CO",
        "Arenasport1.hr": "Arena Sport 1 HR",
        "Arenasport2.hr": "Arena Sport 2 HR",
        "Arenasport3.hr": "Arena Sport 3 HR",
        "Arenasport4.hr": "Arena Sport 4 HR",
        "Arenasport5.hr": "Arena Sport 5 HR",
        "Arenasport6.hr": "Arena Sport 6 HR",
        "Arenasport7.hr": "Arena Sport 7 HR",
        "Arenasport8.hr": "Arena Sport 8 HR",
        "Arenasport9.hr": "Arena Sport 9 HR",
        "Arenasport10.hr": "Arena Sport 10 HR",
        "Nova Sport 1 HD.cz": "Nova Sport 1 CZ",
        "Nova Sport 2 HD.cz": "Nova Sport 2 CZ",
        "CBS Sports Network USA (643).us": "CBS Sports",
        "Go3 Sport Open.lv": "Go3 Sport Open",
        "Polsat Sport 1.pl": "Polsat Sport 1",
        "TSN1HD.ca": "TSN 1",
        "TSN2HD.ca": "TSN 2",
        "TSN3HD.ca": "TSN 3",
        "TSN4HD.ca": "TSN 4",
        "TSN5HD.ca": "TSN 5",
        "SportdigitalFUSSBALL.de": "SportDigital Fussball",
        "SportdigitalFUSSBALL.de": "SportDigital Fussball",
        "SporTV.br": "sportv BR",
        "SporTV2.br": "sportv 2 BR",
        "SporTV3.br": "sportv 3 BR",
        "Tipik.be": "RTBF Tipik",
        "Fox Deportes (655).us": "FOX Deportes",
        "Fox Sports 1 (652).us": "FS1",
        "Fox Sports 2 (651).us": "FS2",
        "Eurosport1.es": "Eurosport 1 ES",
        "Eurosport2.es": "Eurosport 2 ES",
        "Eurosport 1 HD.sk": "Eurosport 1 SK",
        "Eurosport 2 HD.sk": "Eurosport 2 SK",
        "Tennis Channel.us": "Tennis Channel",
        "Sport1 HD.sk": "Sport1 SK",
        "Sport2 HD.sk": "Sport2 SK",
        "beINSPORTS1.fr": "beIN Sports 1 FR",
        "beINSPORTS2.fr": "beIN Sports 2 FR",
        "beINSPORTS3.fr": "beIN Sports 3 FR",
        "beINSPORTSMAX4.fr": "beIN Sports 4 FR",
        "beINSPORTSMAX5.fr": "beIN Sports 5 FR",
        "beINSPORTSMAX6.fr": "beIN Sports 6 FR",
        "beINSPORTSMAX7.fr": "beIN Sports 7 FR",
        "beINSPORTSMAX8.fr": "beIN Sports 8 FR",
        "beINSPORTSMAX9.fr": "beIN Sports 9 FR",
        "beINSPORTSMAX10.fr": "beIN Sports 10 FR",
        "PAY TV FOX.mx": "FOX MX",
        "FOX SPORTS.mx": "Fox Sports MX",
        "FOX SPORTS 2.mx": "Fox Sports 2 MX",
        "FOX SPORTS 3.mx": "Fox Sports 3 MX",
        "FOX SPORTS PREMIUM.mx": "Fox Sports Premium MX"
    },
    "cine": {
        "5f1ac1f1b66c76000790ef27": "Pluto Cine Estelar"
    },
    "nacionales": {
        "LA1.es": "La 1 OpB",
        "La 1 HD": "La 1", #DMUMA
        "La2.es": "La 2 OpB",
        "Cuatro.es": "Cuatro",
        "Telecinco.es": "Telecinco",
        "LaSexta.es": "La Sexta"
    },
    "norteamerica": {
        "AztecaUno.mx": "Azteca Uno",
        "LasEstrellas.mx": "Las Estrellas",
        "Telefe.ar": "Telefe",
        "CaracolTV.co": "Caracol TV",
        "RCNTV.co": "RCN TV"
    }
    # Puedes añadir todas las categorías que quieras:
    # "deportes": { "id_original": "id_nuevo" },
    # "series": { "id_original": "id_nuevo" },
}

# ==============================================================================
# LÓGICA DE PROCESAMIENTO Y FILTRADO TEMPORAL
# ==============================================================================

def es_programa_valido(fecha_inicio_str, fecha_limite_inicio, fecha_limite_fin):
    """
    Verifica si el programa entra en la ventana desde hoy a las 00:00:00
    hasta pasado mañana a las 05:59:59.
    """
    try:
        fecha_clean = fecha_inicio_str.split()[0][:14]
        fecha_dt = datetime.strptime(fecha_clean, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return fecha_limite_inicio <= fecha_dt <= fecha_limite_fin
    except Exception:
        return True

def obtener_arbol_xml(url, archivo_temp):
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp, open(archivo_temp, 'wb') as out:
        out.write(resp.read())

    if url.endswith('.gz'):
        with gzip.open(archivo_temp, 'rb') as f_in:
            tree = ET.parse(f_in)
    else:
        tree = ET.parse(archivo_temp)
    return tree

def limpiar_programa(programme_elem, tags_a_borrar):
    """
    Elimina los nodos hijos especificados (como <desc>, <icon>, etc.)
    del elemento <programme> para dejarlo lo más ligero posible.
    """
    for tag in tags_a_borrar:
        for nodo in programme_elem.findall(tag):
            programme_elem.remove(nodo)

def generar_epgs_por_categoria():
    canal_a_cat = {}
    arboles_categorias = {}
    canales_agregados = {}

    for cat_nombre, canales in CATEGORIAS.items():
        arboles_categorias[cat_nombre] = ET.Element('tv', generator_info_name=f"EPG - {cat_nombre.capitalize()}")
        canales_agregados[cat_nombre] = set()
        for id_orig, id_nuevo in canales.items():
            if id_orig not in canal_a_cat:
                canal_a_cat[id_orig] = []
            # Guardamos todas las categorías a las que pertenece el canal
            canal_a_cat[id_orig].append((id_nuevo, cat_nombre))

    # --- VENTANA TEMPORAL: Hoy 00:00:00 hasta Pasado Mañana 05:59:59 ---
    ahora_utc = datetime.now(timezone.utc)
    fecha_limite_inicio = ahora_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_limite_fin = fecha_limite_inicio + timedelta(days=2, hours=5, minutes=59, seconds=59)

    print(f"--> Filtrando programación:")
    print(f"    Desde: {fecha_limite_inicio.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"    Hasta: {fecha_limite_fin.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    for pais, url in FUENTES_XML.items():
        ext = ".xml.gz" if url.endswith('.gz') else ".xml"
        archivo_temp = f"temp_{pais}{ext}"
        print(f"--> Descargando fuente de {pais}...")

        try:
            tree = obtener_arbol_xml(url, archivo_temp)
            root = tree.getroot()

            # A. Canales
            for channel in root.findall('channel'):
                id_orig = channel.get('id')
                if id_orig in canal_a_cat:
                    # Recorremos todas las categorías donde debe aparecer el canal
                    for id_nuevo, cat_nombre in canal_a_cat[id_orig]:
                        if id_nuevo not in canales_agregados[cat_nombre]:
                            ch_copy = copy.deepcopy(channel)
                            ch_copy.set('id', id_nuevo)
                            display_name = ch_copy.find('display-name')
                            if display_name is not None:
                                display_name.text = id_nuevo

                            arboles_categorias[cat_nombre].append(ch_copy)
                            canales_agregados[cat_nombre].add(id_nuevo)

            # B. Programas
            for programme in root.findall('programme'):
                canal_orig = programme.get('channel')
                start_time = programme.get('start')

                if canal_orig in canal_a_cat and start_time:
                    if es_programa_valido(start_time, fecha_limite_inicio, fecha_limite_fin):
                        # Insertamos el programa en cada una de las categorías correspondientes
                        for id_nuevo, cat_nombre in canal_a_cat[canal_orig]:
                            prog_copy = copy.deepcopy(programme)
                            prog_copy.set('channel', id_nuevo)

                            tags_a_borrar = ETIQUETAS_LIMPIEZA.get(cat_nombre, LIMPIEZA_DEFECTO)
                            if tags_a_borrar:
                                limpiar_programa(prog_copy, tags_a_borrar)

                            arboles_categorias[cat_nombre].append(prog_copy)

            print(f"    ✔ Procesado {pais} con éxito.")

        except Exception as e:
            print(f"    ❌ Error procesando {pais}: {e}")
        finally:
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)

    print("\n--> Guardando archivos EPG limpios por categoría:")
    for cat_nombre, root_cat in arboles_categorias.items():
        nombre_archivo = f"epg_{cat_nombre}.xml"
        tree_cat = ET.ElementTree(root_cat)
        ET.indent(tree_cat, space="  ", level=0)
        tree_cat.write(nombre_archivo, encoding="utf-8", xml_declaration=True)
        print(f"    ✔ Generado: {nombre_archivo}")

    print("\n¡Todas las guías optimizadas han sido creadas con éxito!")

if __name__ == "__main__":
    generar_epgs_por_categoria()
