import os
import json
import time
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
# LÓGICA DE TRADUCCIÓN CON CONTROL DE ERRORES
# ==============================================================================

def es_respuesta_valida(texto):
    if not texto:
        return False
    texto_l = texto.lower()
    if "error 500" in texto_l or "that’s an error" in texto_l or "server error" in texto_l:
        return False
    return True

def traducir_con_reintentos(translator, texto, max_intentos=3):
    intentos = 0
    espera = 2.0

    while intentos < max_intentos:
        try:
            resultado = translator.translate(texto)
            if es_respuesta_valida(resultado):
                return resultado
            else:
                print(f"    ⚠️ Respuesta inválida de Google (Error 500 detectado). Reintentando en {espera}s...")
        except Exception as e:
            print(f"    ⚠️ Fallo en la llamada: {e}. Reintentando en {espera}s...")

        intentos += 1
        time.sleep(espera)
        espera *= 2  # Espera más en cada fallo (2s, 4s, 8s)

    # Si tras los intentos sigue fallando, devolvemos el texto original
    return texto

def main():
    if not os.path.exists(XML_ENTRADA):
        print(f"❌ Error: El archivo fuente '{XML_ENTRADA}' no existe.")
        return

    print(f"--> Leyendo archivo fuente: {XML_ENTRADA}")
    tree = ET.parse(XML_ENTRADA)
    root = tree.getroot()

    cache = cargar_cache()

    # Limpiamos posibles respuestas erróneas que hayan quedado guardadas en la caché previa
    cache = {k: v for k, v in cache.items() if es_respuesta_valida(v)}

    translator = GoogleTranslator(source="auto", target=TARGET_LANG)

    total_programas = 0
    nuevas_traducciones = 0

    def procesar_texto(texto):
        nonlocal nuevas_traducciones
        texto_limpio = (texto or "").strip()
        if not texto_limpio:
            return texto

        if texto_limpio in cache:
            return cache[texto_limpio]

        # Pequeña pausa preventiva para respetar los límites de Google
        time.sleep(0.35)

        resultado = traducir_con_reintentos(translator, texto_limpio)
        if es_respuesta_valida(resultado) and resultado != texto_limpio:
            cache[texto_limpio] = resultado
            nuevas_traducciones += 1
            return resultado
        
        return texto_limpio

    print("--> Procesando parrilla de programas...")

    for programme in root.findall("programme"):
        channel_id = programme.get("channel")

        if channel_id in CANALES_A_TRADUCIR:
            total_programas += 1

            title_node = programme.find("title")
            if title_node is not None and title_node.text:
                title_node.text = procesar_texto(title_node.text)

            desc_node = programme.find("desc")
            if desc_node is not None and desc_node.text:
                desc_node.text = procesar_texto(desc_node.text)

    guardar_cache(cache)
    print(f"--> Canales traducidos: {len(CANALES_A_TRADUCIR)}")
    print(f"--> Programas evaluados: {total_programas}")
    print(f"--> Nuevos textos enviados a traducir: {nuevas_traducciones}")

    ET.indent(tree, space="  ", level=0)
    tree.write(XML_SALIDA, encoding="utf-8", xml_declaration=True)
    print(f"✔ Archivo final generado con éxito: {XML_SALIDA}")

if __name__ == "__main__":
    main()
