import urllib.request
import xml.etree.ElementTree as ET
import os
import gzip
from datetime import datetime, timedelta, timezone

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

DIAS_FUTURO = 3

FUENTES_XML = {
    "Espana": "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/refs/heads/master/guiaiptv.xml",
    "Mexico": "https://www.open-epg.com/generate/CmMYPab4EY.xml.gz",
    "Argentina": "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/PlutoTV/es.xml",
    "Colombia": "https://iptv-org.github.io/epg/guides/co.xml"
}

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
# LÓGICA DE PROCESAMIENTO
# ==============================================================================

def es_programa_valido(fecha_inicio_str, fecha_limite_inicio, fecha_limite_fin):
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

def generar_epgs_por_categoria():
    # 1. Crear un diccionario inverso para saber rápidamente a qué categoría pertenece cada canal
    # canal_a_cat[id_original] = (id_nuevo, nombre_categoria)
    canal_a_cat = {}
    arboles_categorias = {}
    canales_agregados = {}

    for cat_nombre, canales in CATEGORIAS.items():
        arboles_categorias[cat_nombre] = ET.Element('tv', generator_info_name=f"EPG - {cat_nombre.capitalize()}")
        canales_agregados[cat_nombre] = set()
        for id_orig, id_nuevo in canales.items():
            canal_a_cat[id_orig] = (id_nuevo, cat_nombre)

    # 2. Fechas límite de filtrado
    ahora_utc = datetime.now(timezone.utc)
    fecha_limite_inicio = ahora_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_limite_fin = fecha_limite_inicio + timedelta(days=DIAS_FUTURO + 1)

    print(f"--> Filtrando programación desde {fecha_limite_inicio.strftime('%Y-%m-%d')} hasta {fecha_limite_fin.strftime('%Y-%m-%d')}...")

    # 3. Descargar y clasificar cada fuente
    for pais, url in FUENTES_XML.items():
        ext = ".xml.gz" if url.endswith('.gz') else ".xml"
        archivo_temp = f"temp_{pais}{ext}"
        print(f"--> Descargando fuente de {pais}...")

        try:
            tree = obtener_arbol_xml(url, archivo_temp)
            root = tree.getroot()

            # A. Procesar Canales
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

            # B. Procesar Programas
            for programme in root.findall('programme'):
                canal_orig = programme.get('channel')
                start_time = programme.get('start')

                if canal_orig in canal_a_cat and start_time:
                    if es_programa_valido(start_time, fecha_limite_inicio, fecha_limite_fin):
                        id_nuevo, cat_nombre = canal_a_cat[canal_orig]
                        programme.set('channel', id_nuevo)
                        arboles_categorias[cat_nombre].append(programme)

            print(f"    ✔ Procesado {pais} con éxito.")

        except Exception as e:
            print(f"    ❌ Error procesando {pais}: {e}")
        finally:
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)

    # 4. Guardar un archivo .xml para cada categoría
    print("\n--> Guardando archivos EPG por categoría:")
    for cat_nombre, root_cat in arboles_categorias.items():
        nombre_archivo = f"epg_{cat_nombre}.xml"
        tree_cat = ET.ElementTree(root_cat)
        ET.indent(tree_cat, space="  ", level=0)
        tree_cat.write(nombre_archivo, encoding="utf-8", xml_declaration=True)
        print(f"    ✔ Generado: {nombre_archivo}")

    print("\n¡Todas las guías por categoría han sido creadas con éxito!")

if __name__ == "__main__":
    generar_epgs_por_categoria()
