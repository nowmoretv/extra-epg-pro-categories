import os
import json
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Archivo EPG original de entrada (ruta relativa desde la raíz del repo)
XML_ENTRADA = "epg_deportes.xml"

# Archivo EPG traducido resultante
XML_SALIDA = "epg_deportes_es.xml"

# Archivo local de caché de traducciones
CACHE_FILE = "traductor/cache_traducciones.json"

# Idioma destino (código ISO: 'es' para español)
TARGET_LANG = "es"

# Canales a los que SÍ se les traducirá el título y la descripción
# Añade aquí los channel IDs exactos que coincidan con el XML de origen
CANALES_A_TRADUCIR = {
    "Setanta Sports EE",
    "beIN Sports 1 AU",
    "Arena Sport 1 HR",
    "Nova Sport 1 CZ"
    # Añade los IDs que necesites traducir...
}

# ==============================================================================
# MANEJO DE CACHÉ
# ==============================================================================

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# ==============================================================================
# LÓGICA DE TRADUCCIÓN
# ==============================================================================

def main():
    if not os.path.exists(XML_ENTRADA):
        print(f"❌ Error: El archivo fuente '{XML_ENTRADA}' no existe.")
        return

    print(f"--> Leyendo archivo fuente: {XML_ENTRADA}")
    tree = ET.parse(XML_ENTRADA)
    root = tree.getroot()

    cache = cargar_cache()
    translator = GoogleTranslator(source="auto", target=TARGET_LANG)

    total_programas = 0
    nuevas_traducciones = 0

    def traducir_texto(texto):
        nonlocal nuevas_traducciones
        texto_limpio = (texto or "").strip()
        if not texto_limpio:
            return texto

        # Si ya lo tenemos en caché, no consumimos conexión
        if texto_limpio in cache:
            return cache[texto_limpio]

        try:
            # Petición al traductor
            resultado = translator.translate(texto_limpio)
            cache[texto_limpio] = resultado
            nuevas_traducciones += 1
            return resultado
        except Exception as e:
            print(f"    ⚠️ Error traduciendo texto: {e}")
            return texto_limpio

    print("--> Procesando parrilla de programas...")

    for programme in root.findall("programme"):
        channel_id = programme.get("channel")

        # Solo traducimos si el canal está en la lista seleccionada
        if channel_id in CANALES_A_TRADUCIR:
            total_programas += 1

            # 1. Traducir Título
            title_node = programme.find("title")
            if title_node is not None and title_node.text:
                title_node.text = traducir_texto(title_node.text)

            # 2. Traducir Descripción (si existe)
            desc_node = programme.find("desc")
            if desc_node is not None and desc_node.text:
                desc_node.text = traducir_texto(desc_node.text)

    # Guardamos la caché actualizada en el repositorio
    guardar_cache(cache)
    print(f"--> Canales traducidos: {len(CANALES_A_TRADUCIR)}")
    print(f"--> Programas evaluados: {total_programas}")
    print(f"--> Nuevos textos enviados a traducir (sin caché): {nuevas_traducciones}")

    # Escribimos el nuevo archivo XML resultante
    ET.indent(tree, space="  ", level=0)
    tree.write(XML_SALIDA, encoding="utf-8", xml_declaration=True)
    print(f"✔ Archivo final generado con éxito: {XML_SALIDA}")

if __name__ == "__main__":
    main()
