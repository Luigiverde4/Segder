from socket import *
from datetime import datetime
from threading import Thread, Event
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
from PIL import Image, ImageDraw, ImageFont
import hashlib

import json
import select
import os

def actualizarLicenciasJSON(diContenidos) -> None:
    """
    Actualiza el índice de licencias con el objeto diContenidos,
    asegurando que no haya archivos repetidos.

    diContenidos (objeto): Objeto de Python con los datos de nombre, encriptado y iv de los archivos
    """
    # Verificar y eliminar archivos repetidos, dejando solo el más reciente
    archivos_vistos = {}
    for archivo in diContenidos['archivos']:
        archivos_vistos[archivo['Nombre']] = archivo  # Sobrescribir con el último archivo encontrado

    # Reemplazar el listado con los archivos actualizados (sin duplicados)
    diContenidos['archivos'] = list(archivos_vistos.values())

    # Actualizar el índice
    actualizarIndex(diContenidos)

def actualizarIndex(diContenidos) -> dict:
    """
    Crea un índice del contenido del servidor a partir del diccionario diContenidos.
    Returns:
        dict: Diccionario con el nombre del archivo como clave y el estado de encriptación como valor.
    """
    global index_encriptacion
    try:
        res_dict = {}
        for archivo in diContenidos.get("archivos", []):
            nombre = archivo.get("Nombre", "") # "" es el valor predeterminado 
            encriptado = archivo.get("Encriptado", 'False') # 'False' es el valor predeterminado
            res_dict[nombre] = encriptado
        
        index_encriptacion = res_dict
    except Exception as e:
        print(f"Error al procesar el índice: {str(e)}")

# Funciones interfaz
def log(msj: str) -> None:
    """Guarda un log con el tiempo y el mensaje en un archivo de texto.
    Args:
        msj (str): Mensaje a guardar en el log
    Returns:
        None
    """
    try:
        with open("logs/log.txt", "a") as log_file:
            log_entry = f"{datetime.now().strftime('%H:%M:%S')} - {msj}"
            print(log_entry)
            log_file.write(f"{log_entry}\n")
    except FileNotFoundError:
        print("ERROR: El archivo log.txt no existe y no se puede acceder.")
        raise 

def iniciar_log() -> None:
    """Escribe un mensaje de inicio en el log al iniciar el servidor anadiendo una linea en blanco si ya existe el archivo.
    Args:
        None
    Returns:
        None
    """
    try:
        archivo_existe = os.path.exists("log_Licencias.txt")
        
        with open("logs/log_Licencias.txt", "a") as log_file:
            if archivo_existe:
                log_file.write("\n")  # Anade una linea en blanco solo si el archivo ya existe
            log_entry = f"{datetime.now().strftime('%H:%M:%S')} - El servidor ha sido iniciado\n"
            log_file.write(log_entry + '\n')
        log(log_entry)
    except FileNotFoundError as e:
        log(f"{str(e)}")  # Loguea el error si no se encuentra el archivo
        raise

def json_a_txt(ruta_json: str, ruta_txt: str) -> None:
    """
    Convierte el contenido de un archivo JSON a txt

    Args:
        ruta_json (str): Ruta del archivo JSON 
        ruta_txt (str): Ruta del archivo de texto donde se guarda el contenido
    """
    try:
        with open(ruta_json, 'r') as archivo_json:
            contenido = json.load(archivo_json)
        
        with open(ruta_txt, 'w') as archivo_txt:
            for archivo in contenido.get("archivos", []):
                archivo_txt.write(f"Nombre: {archivo['nombre']}, Encriptado: {archivo['encriptado']}, IV: {archivo['iv']}, K: {archivo['k']}\n")
        
        log(f"Contenido de {ruta_json} convertido a {ruta_txt}")
    except Exception as e:
        log(f"Error al convertir JSON a TXT: {str(e)}")
        raise


def encriptar_txt_cbc(ruta_txt: str, clave: bytes) -> None:
    """
    Encripta un archivo de texto utilizando AES en modo CBC y sobrescribe el txt og

    Args:
        ruta_txt (str): Ruta del archivo de texto original que sera sobrescrito
        clave (bytes): Clave de 16 bytes 
    """
    try:
        with open(ruta_txt, 'rb') as archivo_txt:
            datos = archivo_txt.read()
        
        padding = 16 - len(datos) % 16
        datos_padded = datos + bytes([padding] * padding)       
        iv = os.urandom(16)
        aesCipher_CBC = Cipher(algorithms.AES(clave), modes.CBC(iv))
        aesEncryptor = aesCipher_CBC.encryptor()       
        datos_encriptados = aesEncryptor.update(datos_padded) + aesEncryptor.finalize()        
        with open(ruta_txt, 'wb') as archivo_txt:
            archivo_txt.write(iv + datos_encriptados)
        
        log(f"Archivo {ruta_txt} encriptado")
    except Exception as e:
        log(f"Error al encriptar y sobrescribir TXT: {str(e)}")
        raise

def desencriptar_txt_a_diccionario(ruta_txt: str, clave: bytes) -> dict:
    """
    Desencripta un archivo encriptado con AES en modo CBC y convierte su contenido a un diccionario de Python.

    Args:
        ruta_txt (str): Ruta del archivo de texto encriptado.
        clave (bytes): Clave de 16 bytes utilizada para el cifrado y descifrado.

    Returns:
        dict: Diccionario con los datos desencriptados.
    """
    try:
        # Leer el archivo en modo binario
        with open(ruta_txt, 'rb') as archivo_txt:
            datos = archivo_txt.read()

        # Asegúrate de que el archivo tiene al menos 16 bytes (el tamaño del IV)
        if len(datos) < 16:
            raise ValueError("El archivo encriptado es demasiado pequeño para ser válido (debe contener al menos 16 bytes para el IV).")

        # Extraer el IV (primeros 16 bytes)
        iv = datos[:16]
        datos_encriptados = datos[16:]

        # Desencriptar los datos
        aesCipher_CBC = Cipher(algorithms.AES(clave), modes.CBC(iv))
        aesDecryptor = aesCipher_CBC.decryptor()
        datos_desencriptados_padded = aesDecryptor.update(datos_encriptados) + aesDecryptor.finalize()

        # Eliminar el padding (añadido durante la encriptación)
        padding = datos_desencriptados_padded[-1]
        datos_desencriptados = datos_desencriptados_padded[:-padding]
        # Convertir los datos desencriptados a texto, asumiendo que estaban en formato UTF-8
        contenido_desencriptado = datos_desencriptados.decode('utf-8')

        # Parsear el contenido al formato esperado (diccionario)
        archivos = []
        for linea in contenido_desencriptado.split("\r\n"):
            if linea.strip():
                partes = linea.split(", ")
                archivo = {}
                for parte in partes:
                    clave, valor = parte.split(": ")
                    archivo[clave.strip()] = valor.strip()
                archivos.append(archivo)

        datos_json = {"archivos": archivos}

        return datos_json

    except Exception as e:
        print(f"Se produjo un error al desencriptar el archivo: {e}")
        return {}

def getdiContenido() -> dict:
    clave=os.urandom(16)
    json_a_txt("licencias/licencias.json","licencias.txt")
    encriptar_txt_cbc("licencias.txt",clave)
    return desencriptar_txt_a_diccionario("licencias.txt",clave)

