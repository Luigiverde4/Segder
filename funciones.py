from socket import *
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import json
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

def json_a_txt(ruta_json: str, ruta_txt: str) -> None:
    """
    Convierte el contenido de un archivo JSON a un archivo de texto plano (TXT).

    Args:
        ruta_json (str): Ruta del archivo JSON.
        ruta_txt (str): Ruta del archivo de texto donde se guarda el contenido.
    """
    if os.path.exists(ruta_txt):
        raise FileExistsError(f"El archivo {ruta_txt} ya existe. No se generara de nuevo.")   
    try:
        with open(ruta_json, 'r') as archivo_json:
            contenido = json.load(archivo_json)
        
        with open(ruta_txt, 'w') as archivo_txt:
            for archivo in contenido.get("archivos", []):
                archivo_txt.write(
                    f"Nombre: {archivo['nombre']}, "
                    f"Encriptado: {archivo['encriptado']}, "
                    f"IV: {archivo['iv']}, "
                    f"K: {archivo['k']}\n"
                )
        
        print(f"Contenido de {ruta_json} convertido a {ruta_txt}")
    except Exception as e:
        print(f"Error al convertir JSON a TXT: {e}")
        raise

def encriptar_txt_cbc(ruta_txt: str, clave: bytes) -> None:
    """
    Encripta un archivo de texto utilizando AES en modo CBC y sobrescribe el archivo TXT original

    Args:
        ruta_txt (str): Ruta del archivo de texto que sera encriptado
        clave (bytes): Clave de 16 bytes para la encriptacion
    """
    try:
        with open(ruta_txt, 'rb') as archivo_txt:
            datos = archivo_txt.read()
        if len(datos) > 16 and datos[:16].isalnum():
            raise ValueError(f"El archivo {ruta_txt} ya esta encriptado")
        
        padding = 16 - len(datos) % 16
        datos_padded = datos + bytes([padding] * padding)

        iv = os.urandom(16)
        aesCipher_CBC = Cipher(algorithms.AES(clave), modes.CBC(iv))
        aesEncryptor = aesCipher_CBC.encryptor()
        datos_encriptados = aesEncryptor.update(datos_padded) + aesEncryptor.finalize()

        with open(ruta_txt, 'wb') as archivo_txt:
            archivo_txt.write(iv + datos_encriptados)
        
        print(f"Archivo {ruta_txt} encriptado")
    except Exception as e:
        print(f"Error al encriptar: {e}")
        raise

def desencriptar_txt_a_diccionario(ruta_txt: str, clave: bytes) -> dict:
    """
    Desencripta un archivo encriptado con AES en modo CBC y convierte su contenido a un diccionario de Python

    Args:
        ruta_txt (str): Ruta del archivo de texto encriptado
        clave (bytes): Clave de 16 bytes utilizada para el cifrado y descifrado

    Returns:
        dict: Diccionario con los datos desencriptados
    """
    try:
        with open(ruta_txt, 'rb') as archivo_txt:
            datos = archivo_txt.read()
        iv = datos[:16]
        datos_encriptados = datos[16:]

        aesCipher_CBC = Cipher(algorithms.AES(clave), modes.CBC(iv))
        aesDecryptor = aesCipher_CBC.decryptor()
        datos_desencriptados_padded = aesDecryptor.update(datos_encriptados) + aesDecryptor.finalize()

        padding = datos_desencriptados_padded[-1]
        datos_desencriptados = datos_desencriptados_padded[:-padding]
        contenido_desencriptado = datos_desencriptados.decode('utf-8')

        archivos = []
        for linea in contenido_desencriptado.split("\n"):
            if linea.strip():
                partes = linea.split(", ")
                archivo = {}
                for parte in partes:
                    clave, valor = parte.split(": ")
                    archivo[clave.strip()] = valor.strip()
                archivos.append(archivo)

        return {"archivos": archivos}

    except Exception as e:
        print(f"Error al desencriptar el archivo: {e}")
        raise

def getdiContenido() -> dict:
    clave=b'(0xS\x8bs\xc9\xdc\x1a\xab\xd5n\x9c\xa3@\xb4'
    # solo se usan estas funciones cuando se cree un licencias.json
    #json_a_txt("licencias.json","licencias.txt")
    #encriptar_txt_cbc("licencias.txt",clave)
    return desencriptar_txt_a_diccionario("licencias.txt",clave)

