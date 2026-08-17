import urllib.request
import xml.etree.ElementTree as ET
import os
import gzip
from datetime import datetime, timedelta, timezone

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

FUENTES_XML = {
    "Espana": "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/refs/heads/master/guiaiptv.xml",
    "Mexico": "https://www.open-epg.com/generate/CmMYPab4EY.xml.gz",
    "Argentina": "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/PlutoTV/es.xml",
    "Colombia": "https://iptv-org.github.io/epg/guides/co.xml"
}

# ==============================================================================
# LIMPIEZA DE ETIQUETAS POR CATEGORÍA
# Define qué etiquetas eliminar de <programme> para aligerar el XML.
# Si pones una lista vacía [], se conserva todo.
# ==============================================================================

ETIQUETAS_LIMPIEZA = {
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
    "cine": {
        "5f1ac1f1b66c76000790ef27": "Pluto TV Cine Estelar"
    },
    "nacionales": {
        "La 1 HD": "La 1",
        "LA 1.es": "La 1 Light",
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
            canal_a_cat[id_orig] = (id_nuevo, cat_nombre)

    # --- VENTANA TEMPORAL: Hoy 00:00:00 hasta Pasado Mañana 05:59:59 ---
    ahora_utc = datetime.now(timezone.utc)
    fecha_limite_inicio = ahora_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Sumamos 2 días + 5 horas + 59 minutos + 59 segundos
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
                    id_nuevo, cat_nombre = canal_a_cat[id_orig]
                    
                    if id_nuevo not in canales_agregados[cat_nombre]:
                        channel.set('id', id_nuevo)
                        display_name = channel.find('display-name')
                        if display_name is not None:
                            display_name.text = id_nuevo

                        arboles_categorias[cat_nombre].append(channel)
                        canales_agregados[cat_nombre].add(id_nuevo)

            # B. Programas (Filtrados por ventana horaria y limpiados de etiquetas)
            for programme in root.findall('programme'):
                canal_orig = programme.get('channel')
                start_time = programme.get('start')

                if canal_orig in canal_a_cat and start_time:
                    if es_programa_valido(start_time, fecha_limite_inicio, fecha_limite_fin):
                        id_nuevo, cat_nombre = canal_a_cat[canal_orig]
                        programme.set('channel', id_nuevo)
                        
                        tags_a_borrar = ETIQUETAS_LIMPIEZA.get(cat_nombre, LIMPIEZA_DEFECTO)
                        if tags_a_borrar:
                            limpiar_programa(programme, tags_a_borrar)

                        arboles_categorias[cat_nombre].append(programme)

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
