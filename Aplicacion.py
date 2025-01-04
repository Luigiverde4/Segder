from socket import *
import os
import select
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def des_AES_CBC(x: str):
    """Desencripta unas cadena de bits con AES CBC.
    Args:
        x (str): String de bits del contenido digital encriptado
    Returns:
        textDecrypt (str) : String de bits con el contenido digital original
    """
    key = b'w\xdf\x82\x80Z\xc5\xcc\x14\xbd\x8d\x7f\xde\x15s\xad\xdf'
    IV = b'\xdd\x1c\xe2?3,\x8bS\x1a\xc1\xca\xc1$X4\xb6'
    aesCipher = Cipher(algorithms.AES(key),modes.CBC(IV))
    aesDecryptor = aesCipher.decryptor()
    
    N = algorithms.AES.block_size
    unpadded_data = aesDecryptor.update(x)

    unpadder = padding.PKCS7(N).unpadder()
    textDecrypt = unpadder.update(unpadded_data)+unpadder.finalize()

    return textDecrypt


def desencriptar_imagen_CBC(data:str):
    """Desencripta una imagen con AES CBC.
    Args:
        data (str): String de bits de imagen encriptada
    Returns:
        archivo (str) : Ruta del archivo de imagen desencriptada
    """
    cab = data[0:54] # Guardamos la cabecera para que solo se encripte la imagen

    data = data[54:] # Extraemos la cabecera de lo que vamos a encriptar

    dataDecrypt = des_AES_CBC(data)

    imgDecrypt = open('prueba.bmp','wb') # Creamos fichero nuevo para guardar los datos desencriptados

    dataDecrypt = cab + dataDecrypt
    imgDecrypt.write(dataDecrypt) # Escribimos los datos desencriptados en el fichero


def gestionaInputs(mensaje_tx:str) -> bool:
    """Gestiona el input del usuario y valida los comandos.
    Args:
        mensaje_tx (str): Mensaje del usuario a manejar
    Returns:
        bool: Si esperamos respuesta del servidor
    """
    if not mensaje_tx.strip():
        print("No has ingresado ningun comando, intenta otra vez.")
        return False

    if mensaje_tx.startswith("INFO"):
        print("\nComandos disponibles:")
        for instruccion in comandos:
            print(f"{instruccion.ljust(max_len)} - {comandos[instruccion]}")
        return False

    elif mensaje_tx.split()[0] not in [comando.split()[0] for comando in comandos]: 
        print("Comando erróneo")
        return False

    elif mensaje_tx.startswith("DESCARGAR"):
        partes = mensaje_tx.split()
        if len(partes) < 2:
            print("Error: Debes especificar el nombre del archivo despues de 'DESCARGAR'.")
            return False
        else:
            s.send(mensaje_tx.encode())
            return True

    elif mensaje_tx.startswith("FIN"):
        s.send(mensaje_tx.encode())
        s.close() 
        exit()

    elif mensaje_tx.startswith("CLS"):
        os.system("cls" if os.name == "nt" else "clear")
        print("Introduce INFO para obtener informacion sobre los comandos que puedes enviar")
        return False

    else:
        s.send(mensaje_tx.encode())
        return True

def ver(mensaje_rx: bytes) -> None:
    """Muestra por pantalla los contenidos disponibles del servidor.
    Args:
        mensaje_rx (bytes): Contenido recibido del servidor en bytes
    Returns:
        None
    """
    lista_contenidos = mensaje_rx.decode().split("\n")
    for contenido in lista_contenidos:
        print(contenido)

def descarga(mensaje_tx: str, mensaje_rx: bytes) -> None:
    """Funcion para descargar el archivo pedido al servidor.
    Args:
        mensaje_tx (str): Contenido pedido al servidor
        mensaje_rx (bytes): Mensaje del servidor con el codigo de estado y longitud si procede
    Returns:
        None
    """
    try:
        mensaje_decodificado = mensaje_rx.decode()

        if mensaje_decodificado.startswith("400"):
            print("Error: El archivo solicitado no existe en el servidor.")
            return

        if not mensaje_decodificado.startswith("200"):
            print("Error: El servidor no respondió con un mensaje válido para descarga.")
            return

        longitud = int(mensaje_decodificado.split(":")[1].strip())
        print(f"Tamaño del archivo a descargar: {longitud} bytes")


        with open(f"contenido_descargado/{mensaje_tx.split()[1]}", "wb") as archivo:
            bytes_descargados = 0
            while bytes_descargados < longitud:
                data = s.recv(2048)
                if not data:
                    print("Error: No se recibieron más datos, la descarga puede estar incompleta.")
                    break
                archivo.write(data)
                bytes_descargados += len(data)

            if bytes_descargados >= longitud:
                print("Descarga completa")
            else:
                print("Error: La descarga se interrumpió o fue incompleta.")
    except ValueError as e:
        print(f"Error al interpretar la longitud del contenido en la respuesta del servidor: {e}")
    except FileNotFoundError as e:
        print(f"Error al guardar el archivo descargado: {e}")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado durante la descarga: {e}")

def recibirRespuestas() -> None:
    """Funcion para tratar la respuesta del servidor."""
    try:
        mensaje_rx = s.recv(2048)
        if not mensaje_rx:
            print("Error: No se recibió respuesta del servidor.")
            return

        if mensaje_tx.startswith("VER"):
            ver(mensaje_rx)

        elif mensaje_tx.startswith("DESCARGAR"):
            descarga(mensaje_tx, mensaje_rx)

    except Exception as e:
        print(f"Ha ocurrido un error al recibir la respuesta del servidor: {e}")

def obtener_solicitud():
    """Funcion obtener la solicitud de licencia por parte del CMD."""



# Datos de conexion
dir_IP_servidor = '127.0.0.1'
puerto_servidor = 6000
dir_socket_servidor = (dir_IP_servidor, puerto_servidor)

# Socket
s = socket(AF_INET, SOCK_STREAM)
s.connect(dir_socket_servidor)

inputs = [s]
ready_to_read, ready_to_write, in_error = select.select(inputs,[], [], 5)
if len(ready_to_read) != 0: # Si hay sockets para LEER
    for soc in ready_to_read: # Para cada socket
        if soc is s: # Si el socket no está aceptado, aceptamos la conexión
            clientsock, clientaddr = soc.accept()
            inputs.append(clientsock)
            print("Conectado desde: ",clientaddr)
        else: # Si está aceptado
            data = soc.recv(1024)
            print("Enviando datos: ", data.decode())
            for client in inputs:
                if client is not s and client is not soc:
                    client.send(data)

# Variables globales
comandos = {
    "VER": "Sirve para obtener los contenidos disponibles en el servidor",
    "DESCARGAR {nombre del archivo}": "Envia una solicitud de descarga del fichero especificado al servidor",
    "FIN": "Cierra la aplicacion",
    "CLS": "Limpiar la consola"
}

max_len = max(len(comando) for comando in comandos)

print("Introduzca INFO para obtener informacion sobre los comandos que puedes enviar")

try:
    while True:
        mensaje_tx = input("\nIntroduzca su comando : ")
        if gestionaInputs(mensaje_tx):  # Si esperamos algo del servidor
            recibirRespuestas()
except KeyboardInterrupt as e:
    s.close()
    exit()