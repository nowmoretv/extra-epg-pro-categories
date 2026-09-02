import os
import json
import re
import xml.etree.ElementTree as ET

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

XML_ENTRADA = "epg_deportes.xml"
XML_SALIDA = "epg_deportes_es_manual.xml"
DICCIONARIO_FILE = "traductor_manual/palabras_traducciones.json"

CANALES_A_TRADUCIR = {
    "Setanta Sports EE",
    "beIN Sports 1 AU",
    "Arena Sport 1 HR",
    "Nova Sport 1 CZ"
    # Añade los canales que requieran este filtro
}

# ==============================================================================
# LÓGICA DE TRADUCCIÓN MANUAL
# ==============================================================================

def cargar_diccionario():
    if not os.path.exists(DICCIONARIO_FILE):
        print(f"⚠️ Aviso: No existe '{DICCIONARIO_FILE}'. Se creará uno vacío.")
        with open(DICCIONARIO_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
        return {}

    with open(DICCIONARIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def ajustar_capitalizacion(texto_original, texto_reemplazo):
    """
    Imita el patrón de mayúsculas/minúsculas del texto original:
    - TODO MAYÚSCULAS  -> TODO MAYÚSCULAS
    - Capitalizado     -> Capitalizado (primera letra mayúscula)
    - todo minúsculas  -> todo minúsculas
    """
    if texto_original.isupper():
        return texto_reemplazo.upper()
    elif texto_original.islower():
        return texto_reemplazo.lower()
    elif texto_original.istitle() or (texto_original and texto_original[0].isupper()):
        return texto_reemplazo.capitalize()
    return texto_reemplazo

def aplicar_reemplazos(texto, diccionario_ordenado):
    if not texto:
        return texto

    texto_modificado = texto
    for origen, destino in diccionario_ordenado:
        patron = re.compile(rf"\b{re.escape(origen)}\b", re.IGNORECASE)

        # Función que re.sub llama por cada coincidencia encontrada
        def reemplazar(match):
            coincidencia = match.group(0)
            return ajustar_capitalizacion(coincidencia, destino)

        texto_modificado = patron.sub(reemplazar, texto_modificado)

    return texto_modificado

def main():
    if not os.path.exists(XML_ENTRADA):
        print(f"❌ Error: No existe el archivo base '{XML_ENTRADA}'.")
        return

    diccionario = cargar_diccionario()
    if not diccionario:
        print("ℹ️ Diccionario vacío: no se aplicarán cambios a los textos.")

    # Ordenamos de mayor a menor longitud para evitar sustituciones parciales prematuras
    diccionario_ordenado = sorted(diccionario.items(), key=lambda x: len(x[0]), reverse=True)

    print(f"--> Leyendo '{XML_ENTRADA}'...")
    tree = ET.parse(XML_ENTRADA)
    root = tree.getroot()

    programas_modificados = 0

    for programme in root.findall("programme"):
        channel_id = programme.get("channel")

        if channel_id in CANALES_A_TRADUCIR:
            cambio_realizado = False

            # Procesar título
            title_node = programme.find("title")
            if title_node is not None and title_node.text:
                nuevo_titulo = aplicar_reemplazos(title_node.text, diccionario_ordenado)
                if nuevo_titulo != title_node.text:
                    title_node.text = nuevo_titulo
                    cambio_realizado = True

            if cambio_realizado:
                programas_modificados += 1

    print(f"--> Programas con sustituciones aplicadas: {programas_modificados}")

    ET.indent(tree, space="  ", level=0)
    tree.write(XML_SALIDA, encoding="utf-8", xml_declaration=True)
    print(f"✔ Archivo final generado con éxito: {XML_SALIDA}")

if __name__ == "__main__":
    main()
