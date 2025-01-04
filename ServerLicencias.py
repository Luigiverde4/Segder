from socket import *
from datetime import datetime
from threading import Thread, Event
import base64
import json
import select
import os

# Detenemos el server
def exitear():
    """Cerrar el evento del servidor"""
    log("Servidor detenido por exitear()")
    stop_event.set()  # Señaliza que el servidor debe detenerse

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
        vector = archivo_info.get('iv', '')
        encriptado = archivo_info['encriptado']
        
        # Verifica si el archivo esta presente en la carpeta 'contenido'
        if archivo_nombre in archivos_en_carpeta:
            print(f"El archivo '{archivo_nombre}' esta en la carpeta. Encriptable: {encriptable}. iv: {vector} Encriptado: {encriptado}")
        else:
            print(f"El archivo '{archivo_nombre}'no se encuentra en la carpeta.")

datos_json = leer_json(ruta_json)

#Configuracion de conexión
dir_IP_server = '127.0.0.1'
puerto_server = 6001
dir_socket_server = (dir_IP_server, puerto_server)

#Se crean y configuran los sockets
s = socket(AF_INET, SOCK_STREAM)
s.bind(dir_socket_server)
s.listen()
inputs = [s]
clientes = {}

stop_event = Event()


def sacarIV(sock: socket,mensaje_rx: str)->None:
    """
    Itera sobre los archivos y manda su VI

    sock (Socket): Socket del cliente que estamos tratando
    mensaje_rx (str): Nombre del archivo a desencriptar
    """
    for archivo in datos_json.get('archivos', []):
        if archivo['nombre'] == mensaje_rx:

            clave_c = archivo.get("iv")
            print(clave_c)
            # clave_c es un string
            print("Clave_c: ", clave_c)
            
            if not clave_c:
                sock.send("El archivo no está encriptado\n".encode())
                log(f"El archivo solicitado {mensaje_rx} no esta cifrado")
            else:
                mensaje_tx = f"Vector: {clave_c}"
                sock.send(mensaje_tx.encode())
                log(f"El archivo solicitado {mensaje_rx} si está cifrado")


#Hacemos la función principal del server
def server():
    try:
        while not stop_event.is_set():
            ready_to_read, _, _ = select.select(inputs, [], [], 1)
            for sock in ready_to_read:
                if sock is s:
                    client_socket, addr = s.accept()
                    inputs.append(client_socket)
                    clientes[client_socket] = addr
                    log(f"Conexión aceptada desde {addr}")
                else:
                    try:
                        mensaje_rx = sock.recv(2048).decode().strip()
                        if mensaje_rx:
                            log(f"Mensaje recibido del cliente {clientes[sock]}: {mensaje_rx}")
                            sacarIV(sock,mensaje_rx)

                        else:
                            log(f"Cliente {clientes[sock]} desconectado")
                            inputs.remove(sock)
                            del clientes[sock]
                            sock.close()
                    except Exception as e:
                        log(f"Ha ocurrido un error inesperado: {e}")
                        inputs.remove(sock)
                        del clientes[sock]
                        sock.close()
        s.close()
        log("Socket principal cerrado")
    except Exception as e:
        log(f"Error en el servidor: {e}")
        s.close()
    except KeyboardInterrupt as e:
        log(f"Interrupción de teclado")

        exitear()
                        
#Se crean los hilos
iniciar_log()
hilo_server = Thread(target=server)
hilo_server.start()
hilo_server.join()