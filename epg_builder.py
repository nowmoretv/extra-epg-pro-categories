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
    "Principal scraper": _dec("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL25vd21vcmV0di9leHRyYS1lcGctc2NyYXBlci9yZWZzL2hlYWRzL21haW4vZXBnLnhtbA=="),
    "Pluto TV ES": _dec("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL21hdHRodWlzbWFuL2kubWpoLm56L3JlZnMvaGVhZHMvbWFzdGVyL1BsdXRvVFYvZXMueG1s"),
    "Samsung TV ES": _dec("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL21hdHRodWlzbWFuL2kubWpoLm56L3JlZnMvaGVhZHMvbWFzdGVyL1NhbXN1bmdUVlBsdXMvZXMueG1s"),
    "Plex MX": _dec("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL21hdHRodWlzbWFuL2kubWpoLm56L3JlZnMvaGVhZHMvbWFzdGVyL1BsZXgvbXgueG1s"),
    "Plex US": _dec("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL21hdHRodWlzbWFuL2kubWpoLm56L3JlZnMvaGVhZHMvbWFzdGVyL1BsZXgvdXMueG1s"),
    "Spain": _dec("aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2RhdmlkbXVtYS9FUEdfZG9ibGVNL3JlZnMvaGVhZHMvbWFzdGVyL2d1aWFpcHR2LnhtbA=="),
    "Siguiente lista": "https://"
}

# ==============================================================================
# LIMPIEZA DE ETIQUETAS POR CATEGORÍA
# Define qué etiquetas eliminar de <programme> para aligerar el XML.
# Si pones una lista vacía [], se conserva todo.
# ==============================================================================

ETIQUETAS_LIMPIEZA = {
    "deportes": ["category", "episode-num", "icon", "rating", "series-id", "star-rating", "sub-title"],
    "cine": ["category", "episode-num", "icon", "rating", "series-id", "star-rating", "sub-title"],
    "entretenimiento": ["desc", "category", "episode-num", "icon", "rating", "series-id", "star-rating", "sub-title"],
    "nacionales": ["desc", "category", "episode-num", "icon", "rating", "series-id", "star-rating", "sub-title"],
    "regionales": ["desc", "category", "episode-num", "icon", "rating", "series-id", "star-rating", "sub-title"],
    "norteamerica": ["desc", "category", "episode-num", "icon", "rating", "series-id", "star-rating", "sub-title"]
}

# Etiquetas a eliminar por defecto si una categoría no está en el diccionario anterior
LIMPIEZA_DEFECTO = ["desc", "icon", "episode-num", "series-id"]

# ==============================================================================
# CANALES POR CATEGORÍA
# Estructura: "nombre_archivo": { "ID_ORIGINAL_XML": "ID_NUEVO_DESEADO" }
# ==============================================================================

CATEGORIAS = {
    "deportes": {
        "Onetoro": "Onetoro",
        "LaLiga TV Hypermotion HD": "Hypermotion", #DMUMA
        "LaLigaTVHypermotion.es": "Hypermotion OpB",
        "LaLiga TV Hypermotion 2": "Hypermotion 2", #DMUMA
        "LaLigaTVHypermotion2.es": "Hypermotion 2 OpB",
        "LaLiga TV Hypermotion 3": "Hypermotion 3", #DMUMA
        "LaLigaTVHypermotion3.es": "Hypermotion 3 OpB",
        "DSports.uy": "DSPORTS UY",
        "DSPORTS": "DSPORTS AR DMUMA", #DMUMA
        "DSportsArgentina.uy": "DSPORTS AR",
        "DSports2.uy": "DSPORTS 2 UY",
        "DSPORTS 2": "DSPORTS 2 AR DMUMA", #DMUMA
        "DSportsPlus.uy": "DSPORTS Plus UY",
        "DSPORTS+": "DSPORTS Plus AR DMUMA", #DMUMA
        "SetantaSports1.lt": "Setanta Sports LT",
        "SetantaSports2.lt": "Setanta Sports 2 LT",
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
        "ArenaSport1.hr.scraper": "Arena Sport 1 HR",
        "Arenasport1.hr": "Arena Sport 1 HR OpB",
        "ArenaSport2.hr.scraper": "Arena Sport 2 HR",
        "Arenasport2.hr": "Arena Sport 2 HR OpB",
        "ArenaSport3.hr.scraper": "Arena Sport 3 HR",
        "Arenasport3.hr": "Arena Sport 3 HR OpB",
        "ArenaSport4.hr.scraper": "Arena Sport 4 HR",
        "Arenasport4.hr": "Arena Sport 4 HR OpB",
        "ArenaSport5.hr.scraper": "Arena Sport 5 HR",
        "Arenasport5.hr": "Arena Sport 5 HR OpB",
        "ArenaSport6.hr.scraper": "Arena Sport 6 HR",
        "Arenasport6.hr": "Arena Sport 6 HR OpB",
        "ArenaSport7.hr.scraper": "Arena Sport 7 HR",
        "Arenasport7.hr": "Arena Sport 7 HR OpB",
        "ArenaSport8.hr.scraper": "Arena Sport 8 HR",
        "Arenasport8.hr": "Arena Sport 8 HR OpB",
        "ArenaSport9.hr.scraper": "Arena Sport 9 HR",
        "Arenasport9.hr": "Arena Sport 9 HR OpB",
        "ArenaSport10.hr.scraper": "Arena Sport 10 HR",
        "Arenasport10.hr": "Arena Sport 10 HR OpB",
        "Nova Sport 1 HD.cz": "Nova Sport 1 CZ",
        "Nova Sport 2 HD.cz": "Nova Sport 2 CZ",
        "CBS Sports Network USA (643).us": "CBS Sports",
        "Go3SportOpen.lt": "Go3 Sport Open LT",
        "Go3 Sport Open.lv": "Go3 Sport Open LV",
        "Polsat Sport 1.pl": "Polsat Sport 1",
        "TSN1HD.ca": "TSN 1",
        "TSN2HD.ca": "TSN 2",
        "TSN3HD.ca": "TSN 3",
        "TSN4HD.ca": "TSN 4",
        "TSN5HD.ca": "TSN 5",
        "SportdigitalFUSSBALL.de": "SportDigital Fussball",
        "SporTV.br": "sportv BR",
        "SporTV2.br": "sportv 2 BR",
        "SporTV3.br": "sportv 3 BR",
        "Tipik.be": "RTBF Tipik",
        "Fox Deportes (655).us": "FOX Deportes",
        "Fox Sports 1 (652).us": "FS1",
        "Fox Sports 2 (651).us": "FS2",
        "Eurosport 1 HD": "Eurosport 1 ES", #DMUMA
        "Eurosport1.es": "Eurosport 1 ES OpB",
        "Eurosport 2": "Eurosport 2 ES", #DMUMA
        "Eurosport2.es": "Eurosport 2 ES OpB",
        "Eurosport 1 HD.sk": "Eurosport 1 SK",
        "Eurosport 2 HD.sk": "Eurosport 2 SK",
        "Tennis Channel.us": "Tennis Channel",
        "Sport1 HD.sk": "Sport1 SK",
        "Sport2 HD.sk": "Sport2 SK",
        "beIN SPORTS XTRA ñ": "beIN Sports Xtra en espanol", #DMUMA
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
        "Somos Cine": "Somos Cine",
        "Cine Español (Rakuten TV)": "Rakuten Cine Espanol",
        "8madrid TV": "8madrid TV",
        "AXN HD": "AXN", #DMUMA
        "AXN.es": "AXN OpB",
        "AXN Movies HD": "AXN Movies", #DMUMA
        "AXNMovies.es": "AXN Movies OpB",
        "Pelis Top (Rakuten TV)": "Rakuten Pelis Top", #DMUMA
        "5f1ac1f1b66c76000790ef27": "Pluto Cine Estelar",
        "Películas de Acción (Rakuten TV)": "Rakuten Accion", #DMUMA
        "5f1ac2591dd8880007bb7d6d": "Pluto Accion",
        "Sony One Hits Acción": "Sony One Accion", #DMUMA
        "68d566603d3a9580eb461251": "Paramount Network de Pluto",
        "676e7b4a4bd636000819c6a7": "Pluto Sensacine TV",
        "Multicine atresplayer": "Atresplayer Multicine", #DMUMA
        "Películas de Drama (Rakuten TV)": "Rakuten Drama", #DMUMA
        "5f1ac947dcd00d0007937c08": "Pluto Drama",
        "Thrillers (Rakuten TV)": "Rakuten Thrillers", #DMUMA
        "5f1ac8a87cd38d000745d7cf": "Pluto Thrillers",
        "60cc807324d60a0007708dc8": "Pluto Cine de autor",
        "61373bb45168fe000773eecd": "Pluto Clasico",
        "6385e82900ab2e000768a058": "Pluto Western",
        "6267d4d1fb694f0007a6af0e": "Pluto Horror",
        "66b0dfa1d512590008bfa7fd": "Pluto Gore and slasher",
        "65ce480a78df2200131c597b": "Pluto Psycho",
        "Comedia (Rakuten TV)": "Rakuten Comedia", #DMUMA
        "5f1ac8099c49f600076579b2": "Pluto Comedia",
        "5f1abce155a03d0007718834": "Pluto Comedia Made in Spain",
        "Sony One Hits Comedia": "Sony One Comedia", #DMUMA
        "655b5d865812e80008843bd1": "Pluto Comedias romanticas",
        "Películas Románticas (Rakuten TV)": "Rakuten Romantico", #DMUMA
        "5f1ac9a2d3611d0007a844bb": "Pluto Romantico",
        "En Familia (Rakuten TV)": "Rakuten En Familia" #DMUMA
    },
    "entretenimiento": {
        "5f1acdaa8ba90f0007d5e760": "Pluto Cocina",
        "608049aefa2b8ae93c2c3a63-65cd2cf397fb4731f54ecae7": "Tastemade en espanol",  #PlexMX
        "690dd10a37b131228d76d5b1": "El Mueble",
        "64db2e0835425100080f2f5a": "Pluto Diseno",
        "65786abdb3801200084c593a": "Pluto Homeful",
        "NestingTV.es": "Nesting TV",
        "6a1610bebdf296985fd95603-5f0641d3e8ffda004033b16e": "The Design Network", #PlexUS
        "622f42b831233300078658cc": "Ciudadanos por el mundo",
        "Dviaje": "DViaje", #DMUMA
        "ES26000025M": "Hola Play", #SamsungES
        "61922be835f3910007fc58f6": "En el punto de mira",
        "Equipo de investigación": "Equipo de investigacion",
        "604f8125c6669b00077f7699": "Wipeout"
    },
    "nacionales": {
        "La 1 HD": "La 1", #DMUMA
        "LA1.es": "La 1 OpB",
        "La 1 Cataluña": "La 1 Catalunya", #DMUMA
        "La 1 Canarias": "La 1 Canarias", #DMUMA
        "La 2": "La 2", #DMUMA
        "La2.es": "La 2 OpB",
        "La 2 Cataluña": "La 2 Cat", #DMUMA
        "La 2 Canarias": "La 2 Canarias", #DMUMA
        "Teledeporte": "Teledeporte", #DMUMA
        "24 Horas": "Canal 24 Horas", #DMUMA
        "24 horas Cataluña": "Canal 24 Horas Catalunya", #DMUMA
        "24 horas Canarias": "Canal 24 Horas Canarias", #DMUMA
        "Clan": "Clan", #DMUMA
        "TRECE": "TRECE", #DMUMA
        "El Toro TV": "El Toro TV", #DMUMA
        "Distrito TV": "Distrito TV", #DMUMA
        "CanalParlamento.es": "Canal Parlamento",
        "67517fae5534bb0008187997": "Actualidad 360",
        "ESBC39000033J": "El Pais TV", #SamsungES
        "ESBC1400001L8": "El Confidencial", #SamsungES
        "Negocios TV": "Negocios TV", #DMUMA
        "EuroNews": "Euronews en espanol", #DMUMA
        "France24.es": "France24 en espanol",
        "DW.es": "DW en espanol",
        "RussiaToday.ar": "RT en espanol",
        "CNN en Español": "CNN en espanol", #DMUMA
        "CnnenEspañol.ar": "CNN en espanol OpB",
        "CGTN Español": "CGTN Espanol", #DMUMA
        "CGTNEspanol.es": "CGTN Espanol OpB",
        "NHK WORLD": "NHK World Espanol"
    },
    "regionales": {
        "etb1": "ETB 1", #DMUMA
        "etb2": "ETB 2", #DMUMA
        "etb1ON": "ETB 1 On", #DMUMA
        "etb2ON": "ETB 2 On", #DMUMA
        "TV3": "TV3", #DMUMA
        "TV3CAT Catalunya": "TV3 CAT", #DMUMA
        "3CatInfo": "3cat Info", #DMUMA
        "El 33 Catalunya": "El 33", #DMUMA
        "SX3": "Super3", #DMUMA
        "Esport 3": "Esport3", #DMUMA
        "TVG": "TVG", #DMUMA
        "TVG Europa HD": "TVG Europa", #DMUMA
        "TVG2": "TVG 2", #DMUMA
        "Canal Sur HD": "Canal Sur", #DMUMA
        "Canal Sur Andalucía": "Canal Sur Andalucia", #DMUMA
        "Andalucía TV": "Andalucia TV", #DMUMA
        "Telemadrid": "Telemadrid", #DMUMA
        "La Otra": "LaOtra", #DMUMA
        "À Punt": "A Punt", #DMUMA
        "La Ocho Mediterráneo": "La 8 Mediterraneo", #DMUMA
        "TV Canaria": "TV Canaria", #DMUMA
        "CMM TV": "CMM TV", #DMUMA
        "IB3 TV Illes Balears": "IB3 Global", #DMUMA
        "Canal Extremadura": "Canal Extremadura", #DMUMA
        "Canal Extremadura SAT": "Canal Extremadura Sat", #DMUMA
        "Aragón TV": "Aragon TV", #DMUMA
        "Aragón TV Internacional": "Aragon TV Int", #DMUMA
        "TPA7 Asturias": "TPA 7", #DMUMA
        "TPA8 Asturias": "TPA 8", #DMUMA
        "Popular TV Cantabria": "Popular TV Cantabria", #DMUMA
        "La 7 Murcia": "7RM", #DMUMA
        "Popular TV Región de Murcia": "Popular TV Murcia", #DMUMA
        "La 7 CyL": "CyL 7", #DMUMA
        "La 8 Valladolid": "La 8 Valladolid", #DMUMA
        "Navarra TV": "Navarra Television", #DMUMA
        "Navarra TV 2": "Navarra Television 2", #DMUMA
        "TVR Rioja": "TVR Rioja", #DMUMA
        "TV Melilla": "TV Melilla", #DMUMA
        "Bon Dia TV": "Bon Dia TV", #DMUMA
        "ATV Andorra Televisión": "Andorra Televisio" #DMUMA
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
