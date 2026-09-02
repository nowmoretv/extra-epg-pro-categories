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

def aplicar_reemplazos(texto, diccionario_ordenado):
    if not texto:
        return texto

    texto_modificado = texto
    for origen, destino in diccionario_ordenado:
        # Reemplazo insensible a mayúsculas respetando límites de palabra si son alfanuméricos
        patron = re.compile(rf"\b{re.escape(origen)}\b", re.IGNORECASE)
        texto_modificado = patron.sub(destino, texto_modificado)

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
