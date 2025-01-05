from socket import *
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

k = b'\x0f\x02\xf8\xcc#\x99\xe9<7[3\xc9T\x0b\xd5I'

def int_to_byts(i, length):
    return i.to_bytes(length, byteorder="big")

# Licencias
def decrypt(nombre_archivo:str):
    """
    Desencripta el archivo de imagen.

    nombre_archivo (str): Nombre del archivo a desencriptar.
    """
    try:

        # Comprobar si esta encriptado
        if not comprobarEncriptado(nombre_archivo):
            print("El archivo no está encriptado.")
            return
    
        print("Esta encriptado")
        # Cargar el archivo encriptado
        with open(f"contenido_descargado/{nombre_archivo}", "rb") as archivo_encriptado:
            x = archivo_encriptado.read()  # Lee el archivo completo en bytes
 
        # Obtener el IV desde el servidor
        iv = pedirLicencias(mensaje_tx)
        iv = iv.decode()  # IV como int
        iv = int_to_byts(int(iv), 16)
        print("IV decodificado:", iv)

        # Verificar el tamaño del IV
        if len(iv) == 16:
            print("IV es válido para el cifrado.")
        else:
            print(f"Error: IV no tiene 16 bytes, tiene {len(iv)} bytes.")
            return

        # Crear el cifrador AES en modo CTR con el IV
        aesCipher_CTR = Cipher(algorithms.AES(k), modes.CTR(iv))
        aesDecryptor_CTR = aesCipher_CTR.decryptor()

        # Desencriptar los datos
        archivo_descifrado = aesDecryptor_CTR.update(x) + aesDecryptor_CTR.finalize()  # Lee y desencripta los datos

        # Guardar el archivo desencriptado
        with open(f"contenido_descargado/{nombre_archivo}", "wb") as archivo_descifrado_output:
            archivo_descifrado_output.write(archivo_descifrado)

        print(f"{nombre_archivo} escrito con éxito!")

    except Exception as e:
        print(f"Ha ocurrido un error al desencriptar el archivo: {e}")

def comprobarEncriptado(nombre_archivo):
    mensaje_rx = f"checkEncriptacion {nombre_archivo}".encode()
    sc.send(mensaje_rx)

    response = sc.recv(1024) 
    if response == b'True':
        return True
    elif response == b'False':
        return False
    else:
        return None

def pedirLicencias(mensaje_tx:str)->None:
    """
        Gestionar si se descarga y recibir licencias del servidor de licencias
    """
    # Coger el nombre del archivo que hemos pedido para pedir el IV
    partes = mensaje_tx.split()
    archivo = partes[1]
    mensaje_tx = f"{archivo}"

    # Pedir el IV
    sl.send(mensaje_tx.encode())
    iv = recibirLicencias()
    return iv

def recibirLicencias() -> None:
    """Funcion para recibir las claves de descifrado"""
    try:
        mensaje_rx = sl.recv(2048).decode()

        if not mensaje_rx:
            print("Error: No se recibió respuesta del servidor de licencias")

        else:
            mensaje = mensaje_rx
            respuesta = mensaje.split()
            if len(respuesta) == 2:
                print("Clave recibida")
                iv = respuesta[1].encode()
                return iv
            else:
                print(mensaje_rx)

    except Exception as e:
        print(f"Ha ocurrido un error al recibir la respuesta del servidor: {e}")

def interactuarServerContenidos(mensaje_tx:str)->None:
    """
    Gestionar inpts y recibir respuestas del servidor de contenidos

    mensaje_tx (str): Input del usuario sobre el comando que quiere usar
    """
    if gestionaInputs(mensaje_tx):  # Si esperamos algo del servidor
        recibirRespuestas()


# CONTENIDO
def gestionaInputs(mensaje_tx:str) -> bool:
    """Gestiona el input del usuario y valida los comandosc.
    Args:
        mensaje_tx (str): Mensaje del usuario a manejar
    Returns:
        bool: Si esperamos respuesta del servidor
    """
    # Comando vacio
    if not mensaje_tx.strip():
        print("No has ingresado ningun comando, intenta otra vez.")
        return False

    # INFO
    if mensaje_tx.startswith("INFO"):
        print("\nComandos disponibles:")
        for instruccion in comandos:
            print(f"{instruccion.ljust(max_len)} - {comandos[instruccion]}")
        return False
    
    #  No esta en los comnados
    elif mensaje_tx.split()[0] not in [comando.split()[0] for comando in comandos]: 
        print("Comando erróneo")
        return False

    #  DESCARGAR
    elif mensaje_tx.startswith("DESCARGAR"):
        partes = mensaje_tx.split()
        if len(partes) < 2:
            print("Error: Debes especificar el nombre del archivo despues de 'DESCARGAR'.")
            return False
        else:
            sc.send(mensaje_tx.encode())
            return True

    #  FIN
    elif mensaje_tx.startswith("FIN"):
        sc.send(mensaje_tx.encode())
        sc.close() 
        exit()

    #  CLS
    elif mensaje_tx.startswith("CLS"):
        os.system("cls" if os.name == "nt" else "clear")
        print("Introduce INFO para obtener informacion sobre los comandos que puedes enviar")
        return False

    #  Else -> Mandar lo que sea
    else:
        sc.send(mensaje_tx.encode())
        return True

def ver(mensaje_rx: bytes) -> None:
    """Muestra por pantalla los contenidos disponibles del servidor.
    Args:
        mensaje_rx (bytes): Contenido recibido del servidor en bytes
    Returns:
        None
    """
    # Separamos el contenido que nos han enviado
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
        # Pasamos de binario a string
        mensaje_decodificado = mensaje_rx.decode()

        # Archivo no existe - 400
        if mensaje_decodificado.startswith("400"):
            print("Error: El archivo solicitado no existe en el servidor.")
            return

        # Archivo existe y puede estar codificado - 400
        if not mensaje_decodificado.startswith("200"):
            print("Error: El servidor no respondió con un mensaje válido para descarga.")
            return

        # Calcular la longitud del archivo
        longitud = int(mensaje_decodificado.split(":")[1].strip())
        print(f"Tamaño del archivo a descargar: {longitud/1000} Kb")

        # Escribir el archivo
        with open(f"contenido_descargado/{mensaje_tx.split()[1]}", "wb") as archivo:
            bytes_descargados = 0
            
            # Vamos descargando los bytes del fichero
            while bytes_descargados < longitud:
                data = sc.recv(2048)

                # Si no se recibe datos, paramos
                if not data:
                    print("Error: No se recibieron más datos, la descarga puede estar incompleta.")
                    break

                # Escribimos en el archivo
                archivo.write(data)
                bytes_descargados += len(data)

            # Comprobamos el estado de la descarga
            if bytes_descargados >= longitud:
                print("Descarga completa")
            else:
                print("Error: La descarga se interrumpió o fue incompleta.")

        decrypt(mensaje_tx.split()[1])
    except ValueError as e:
        print(f"Error al interpretar la longitud del contenido en la respuesta del servidor: {e}")
    except FileNotFoundError as e:
        print(f"Error al guardar el archivo descargado: {e}")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado durante la descarga: {e}")


def recibirRespuestas() -> None:
    """Funcion para tratar la respuesta del servidor."""
    try:
        # Recibimos el mensaje
        mensaje_rx = sc.recv(2048)

        # Caso de error
        if not mensaje_rx:
            print("Error: No se recibió respuesta del servidor.")
            return
        
        # VER
        if mensaje_tx.startswith("VER"):
            ver(mensaje_rx)

        # DESCARGAR
        elif mensaje_tx.startswith("DESCARGAR"):
            descarga(mensaje_tx, mensaje_rx)

    except Exception as e:
        print(f"Ha ocurrido un error al recibir la respuesta del servidor: {e}")

# JESUS

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

# ??????
"""
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
"""

# Datos de conexion Contenido
dir_IP_servidor_contenido = '127.0.0.1'
dir_IP_servidor_licencias = '127.0.0.1'
puerto_servidor_contenidos = 6000
puerto_servidor_licencias = 6001

# Datos de conexion Licencias
dir_socket_servidor_contenido = (dir_IP_servidor_contenido, puerto_servidor_contenidos)
dir_socket_servidor_liciencias = (dir_IP_servidor_licencias, puerto_servidor_licencias)

# Socket
sc = socket(AF_INET, SOCK_STREAM)
sc.connect(dir_socket_servidor_contenido)

sl = socket(AF_INET, SOCK_STREAM)
sl.connect(dir_socket_servidor_liciencias)


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
        interactuarServerContenidos(mensaje_tx) 
except KeyboardInterrupt as e:
    sc.close()
    exit()
