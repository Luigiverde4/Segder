"""
Servidor Contenidos
"""
from socket import *
from datetime import datetime
import select
import os

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

# Llamamos a iniciar_log al arrancar el servidor para crearlo si o si
try:
    iniciar_log()
except Exception as e:
    print(f"Error al iniciar el log: {str(e)}")

def ver(cliente: socket) -> None:
    """Envía al cliente los contenidos disponibles en el servidor.
    Args:
        cliente (socket): Socket del cliente con el que estamos trabajando
    Returns:
        None
    """    
    archivos = os.listdir("contenido")
    archivos_str = "\n".join(archivos) if archivos else "No hay contenido\n"
    cliente.send(archivos_str.encode())

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
        contenido = archivo.read()
        longitud = os.stat(ruta).st_size
        msg = f"200 Longitud Contenido:{longitud}\n"
        cliente.send(msg.encode())
        cliente.sendall(contenido)
        log(f"Archivo enviado: {nombre} ({longitud} bytes)")

# Configuracion de conexion
dir_IP_server = "127.0.0.1"
puerto_server = 6000
dir_socket_server = (dir_IP_server, puerto_server)

# Crear y configurar el socket
s = socket(AF_INET, SOCK_STREAM)
s.bind(dir_socket_server)
s.listen()
inputs = [s]

# Comandos disponibles
comandos = ["VER", "DESCARGAR", "FIN"]

# Bucle principal del servidor

while True:
    try:
        # Nuevas conexiones o mensajes entrantes
        ready_to_read, _, _ = select.select(inputs, [], [])

        # Miramos cada socket listo para leer
        for sock in ready_to_read:
            if sock is s:
                # Si el socket es nuevo
                client_socket, addr = s.accept()
                inputs.append(client_socket) 
                log(f"Conexion aceptada desde {addr}")
            else:
                # Si el socket es de un cliente existente, recibimos el mensaje
                mensaje_rx = sock.recv(2048).decode()

                if mensaje_rx:
                    # Logueamos el mensaje recibido
                    log(f"Mensaje recibido de cliente: {mensaje_rx}")

                    # Verificamos si el comando recibido es válido
                    if mensaje_rx.split()[0] not in comandos:
                        # Comando no reconocido
                        sock.send("Comando no reconocido\n".encode())
                    
                    elif mensaje_rx.startswith("FIN"):
                        # Comando FIN: cerrar la conexion
                        sock.send("Cerrando conexion\n".encode())
                        sock.close()
                        inputs.remove(sock)  # Quitamos el socket cerrado de la lista de entradas
                        log("Conexion cerrada por el cliente")
                    
                    elif mensaje_rx.startswith("VER"):
                        # Comando VER: listar contenidos disponibles
                        ver(sock)
                    
                    elif mensaje_rx.startswith("DESCARGAR"):
                        # Comando DESCARGAR: enviar archivo solicitado
                        get(sock, mensaje_rx)
                else:
                    # Si no hay mensaje, el cliente cerró la conexión
                    sock.close()
                    inputs.remove(sock)  # Eliminamos el socket del cliente
                    log("Cliente desconectado")
                    
    except FileNotFoundError:
        # Error al intentar acceder a un archivo inexistente
        log("ERROR: Archivo no encontrado!")
        sock.send("ERROR archivo no encontrado")
    except Exception as e:
        # Cualquier otro error en el servidor se loguea
        log(f"Error en el servidor: {str(e)}")
        sock.send("ERROR en el servidor")
