import json
import os

# Ruta al archivo JSON que contiene la información
ruta_json = 'licencias.json'

# Ruta a la carpeta 'contenido' donde están guardados los archivos
ruta_contenido = 'contenido'

def leer_json(ruta)->dict:
    """Abre el archivo JSON, lo lee y lo carga en un diccionario
    
    Args:
        ruta (str): La ruta del archivo
    
    Returns:
        dict: El contenido del archivo JSON como un diccionario
    """
    with open(ruta, 'r') as file:
        return json.load(file)

def verificar_archivos(json_data, carpeta)->None:
    """Recorre el archivo JSON y comprueba que exista el archivo y te dice si es es encriptable
    #cuando tengamos mas cosas hechas podemos enlazarlo bien
    
    Args:
        json_data (dict): El diccionario que contiene la información de los archivos
        carpeta (str): La ruta de la carpeta donde se encuentran los archivos
    Returns:
        None
    """
    archivos_en_carpeta = os.listdir(carpeta)
    
    # Recorre cada archivo en el JSON y verifica si existe en la carpeta
    for archivo_info in json_data['archivos']:
        archivo_nombre = archivo_info['nombre']
        encriptable = archivo_info['encriptable']
        
        # Verifica si el archivo esta presente en la carpeta 'contenido'
        if archivo_nombre in archivos_en_carpeta:
            print(f"El archivo '{archivo_nombre}' esta en la carpeta. Encriptable: {encriptable}")
        else:
            print(f"El archivo '{archivo_nombre}'no se encuentra en la carpeta. Encriptable: {encriptable}")

datos_json = leer_json(ruta_json)
verificar_archivos(datos_json, ruta_contenido)
