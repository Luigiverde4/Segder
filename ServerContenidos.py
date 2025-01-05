"""
Servidor Contenidos
"""
from socket import *
from datetime import datetime
from threading import Thread, Event
import select
import os
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

index_encriptacion = {}
k = b'\x0f\x02\xf8\xcc#\x99\xe9<7[3\xc9T\x0b\xd5I'

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
        archivo_existe = os.path.exists("log.txt")
        
        with open("logs/log.txt", "a") as log_file:
            if archivo_existe:
                log_file.write("\n")  # Anade una linea en blanco solo si el archivo ya existe
            log_entry = f"{datetime.now().strftime('%H:%M:%S')} - El servidor ha sido iniciado\n"
            log_file.write(log_entry)
            log(log_entry)
    except FileNotFoundError as e:
        log(f"{str(e)}")  # Loguea el error si no se encuentra el archivo
        raise

def mostrarIndex() -> str:
    """
    Crea un string con el nombre y si esta encriptado segun el JSON
    """
    final = "\nNombre : Encriptado?\n"
    for llave, valor in index_encriptacion.items():
        final += f"{llave} : {valor} \n"
    return final


# Funciones servidor
def ver(cliente: socket) -> None:
    """Envia al cliente los contenidos disponibles en el servidor.
    Args:
        cliente (socket): Socket del cliente con el que estamos trabajando
    Returns:
        None
    """    
    archivos = os.listdir("contenido")
    archivos_str = "\n".join(archivos) if archivos else "No hay contenido\n"
    cliente.send(archivos_str.encode())
    log(f"Ver enviado a {clientes[cliente]}")

def get(cliente: socket, mensaje_rx: str) -> None:
    """Procesa la solicitud de descarga de un archivo.
    Args:
        cliente (socket): Socket del cliente con el que estamos trabajando
        mensaje_rx (str): Mensaje rec
    Returns:
        None
    """
    nombre = mensaje_rx.split()[1]
    ruta = f"contenido/{nombre}"

    if not os.path.exists(ruta):
        log(f"Archivo no encontrado: {nombre}")
        cliente.send("400 Archivo no encontrado\n".encode())
        return

    with open(ruta, 'rb') as archivo:
        # Cargar el contenido y peso
        contenido = archivo.read()
        longitud = os.stat(ruta).st_size

        # Aviso de longitud
        codigo = "200"
        msg = f"{codigo} Longitud Contenido:{longitud}\n"
        
        # Mandar el archivo
        cliente.send(msg.encode())
        cliente.sendall(contenido)
        log(f"Archivo enviado: {nombre} ({longitud/1000} Kb) a {clientes[cliente]}")

def exitear():
    """Cerrar el evento del servidor"""
    log("Servidor detenido por exitear()")
    stop_event.set()  # Señaliza que el servidor debe detenerse

def crearIndex(lst)->dict:
    """
    Crea un indice del contenido del servidor

    Args:
        lst (lista): Lista de ficheros en /contenidos/
    Returns:
        res_dict (diccionario): objeto 
    """
    res_dict = {}
    for i in range(0, len(lst)):
        res_dict[lst[i]] = False # a futuro cambiar por detector de si esta encriptado o no
    return res_dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64

def byts_to_int(b):
    return int.from_bytes(b,byteorder="big")

def encrypt():
    with open("licencias.json", 'r') as file:
        listado = json.load(file)

    for archivo in listado['archivos']:
        nombre = archivo['nombre']
        vector = archivo['iv']
        encriptado = archivo['encriptado']

        ruta = os.path.join("contenido", nombre)

        if not encriptado:
            if not vector:
                # Genera un IV de 16 bytes si no existe
                iv = os.urandom(16)
                archivo['iv'] = byts_to_int(iv)  # Guardar el IV como int
            else:
                iv = bytes(archivo['iv'])  # Convertir de lista de enteros a bytes

            aesCipher_CTR = Cipher(algorithms.AES(k), modes.CTR(iv))
            aesEncryptor_CTR = aesCipher_CTR.encryptor()

            with open(ruta, 'rb') as docu:
                contenido = docu.read()

            contenido_encriptado = aesEncryptor_CTR.update(contenido) + aesEncryptor_CTR.finalize()

            with open(ruta, 'wb') as almacen:
                almacen.write(contenido_encriptado)

            archivo['encriptado'] = True

    with open("licencias.json", 'w') as file:
        json.dump(listado, file, indent=4)

# INICIO SERVIDOR
try:
# Llamamos a iniciar_log al arrancar el servidor para crearlo si o si
    iniciar_log()
    contenido_inicial = os.listdir("contenido")
    index_encriptacion = crearIndex(contenido_inicial)
except Exception as e:
    print(f"Error al iniciar el log: {str(e)}")


# Configuracion de conexion
dir_IP_server = "127.0.0.1"
puerto_server = 6000
dir_socket_server = (dir_IP_server, puerto_server)

# Crear y configurar el socket
s = socket(AF_INET, SOCK_STREAM)
s.bind(dir_socket_server)
s.listen()
inputs = [s]
clientes = {}
encrypt()
# Comandos disponibles
comandos = ["VER", "DESCARGAR", "FIN"]

# Evento para detener el servidor
stop_event = Event()

# Interfaz del servidor
def serverInterface():
    """Función de consola para controlar el servidor."""
    try:
        while True:
            # Tomar input del usuario 
            consola = input()
            
            # Fin del programa
            if consola.startswith("exit"):
                exitear()
                break
            # Logear datos
            elif consola.startswith("log"):
                log(" ".join(consola.split()[1:]))

            elif consola.startswith("index"):
                log(mostrarIndex())
    except EOFError:
        log("Entrada cerrada.")
        exitear()


# Bucle principal del servidor
def server():
    while not stop_event.is_set(): # en vez de true, es un evento
        # Nuevas conexiones o mensajes entrantes
        ready_to_read, _, _ = select.select(inputs, [], [], 1)

        # Miramos cada socket listo para leer
        for sock in ready_to_read:
            if sock is s:
                # Si el socket es nuevo
                client_socket, addr = s.accept()
                inputs.append(client_socket) 
                clientes[client_socket] = addr 
                log(f"Conexion aceptada desde {addr}")
            else:
                # Si el socket es de un cliente existente, recibimos el mensaje
                mensaje_rx = sock.recv(2048).decode()

                if mensaje_rx:
                    # Logueamos el mensaje recibido
                    log(f"Mensaje recibido de cliente {clientes[sock]} : {mensaje_rx}")

                    # Verificamos si el comando recibido es valido
                    if mensaje_rx.split()[0] not in comandos:
                        # Comando no reconocido
                        sock.send(f"Comando no reconocido de {clientes[sock]}\n".encode())
                    
                    elif mensaje_rx.startswith("FIN"):
                        # FIN: cerrar la conexion
                        sock.send("Cerrando conexion\n".encode())
                        sock.close()
                        inputs.remove(sock)  # Quitamos el socket cerrado de la lista de entradas
                        log(f"Conexion cerrada por el cliente {clientes[sock]}")
                    
                    elif mensaje_rx.startswith("VER"):
                        # VER: listar contenidos disponibles
                        ver(sock)
                    
                    elif mensaje_rx.startswith("DESCARGAR"):
                        # DESCARGAR: enviar archivo solicitado
                        get(sock, mensaje_rx)
                else:
                    # Si no hay mensaje, el cliente cerro la conexion
                    log(f"Cliente {clientes[sock]} desconectado")  
                    sock.close()
                    inputs.remove(sock)  # Eliminamos el socket del cliente
                    del clientes[sock]  # Eliminamos la info del cliente
                    
    # Cierre del socket principal al detener el servidor
    s.close()
    log("Socket principal cerrado.")

# Hilos
hilo_server = Thread(target=server)
hilo_serverInterface = Thread(target=serverInterface)

hilo_server.start()
hilo_serverInterface.start()

# Esperamos a que ambos hilos terminen
try:
    hilo_server.join()
    hilo_serverInterface.join()
except KeyboardInterrupt as e:
    log(f"Interrupción de teclado")
    exitear()
except FileNotFoundError:
    # Error al intentar acceder a un archivo inexistente
    log("ERROR: Archivo no encontrado!")
except EOFError as e:
    log(f"Error EOF")
    exitear()
except Exception as e:
    # Cualquier otro error en el servidor se loguea
    log(f"Error en el servidor: {str(e)}")