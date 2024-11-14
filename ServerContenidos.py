"""
Servidor Contenidos
"""
from socket import *
import os
from datetime import datetime

def iniciar_log() -> None:
    """Escribe un mensaje de inicio en el log al iniciar el servidor anadiendo una linea en blanco si ya existe el archivo."""
    try:
        archivo_existe = os.path.exists("log.txt")
        
        with open("log.txt", "a") as log_file:
            if archivo_existe:
                log_file.write("\n")  # Anade una linea en blanco solo si el archivo ya existe
            log_file.write(f"{datetime.now().strftime('%H:%M:%S')} - El servidor ha sido iniciado\n")
    
    except FileNotFoundError:
        print("ERROR: El archivo log.txt no existe y no se puede acceder.")
        raise  

def log(msj: str) -> None:
    """Guarda un log con el tiempo y el mensaje en un archivo de texto."""
    try:
        with open("log.txt", "a") as log_file:
            log_entry = f"{datetime.now().strftime('%H:%M:%S')} - {msj}\n"
            log_file.write(log_entry)
    
    except FileNotFoundError:
        print("ERROR: El archivo log.txt no existe y no se puede acceder.")
        raise  

# Llamamos a iniciar_log al arrancar el servidor para crearlo si o si
try:
    iniciar_log()
except Exception as e:
    print(f"Error al iniciar el log: {str(e)}")


def ver() -> None:
    """Envía al cliente los contenidos disponibles en el servidor."""
    archivos = os.listdir("contenido")
    archivos_str = "\n".join(archivos) if archivos else "No hay contenido\n"
    s1.send(archivos_str.encode())

def get(mensaje_rx: str) -> None:
    """Procesa la solicitud de descarga de un archivo."""
    nombre = mensaje_rx.split()[1]  # Extrae el nombre del archivo
    ruta = f"contenido/{nombre}"

    # Verifica si el archivo existe
    if not os.path.exists(ruta):
        log(f"Archivo no encontrado: {nombre}")
        s1.send("400 Archivo no encontrado\n".encode())
        return

    # Envia el archivo al cliente
    with open(ruta, 'rb') as archivo:
        contenido = archivo.read()
        longitud = os.stat(ruta).st_size  # Obtiene tamaño del archivo
        msg = f"200 Longitud Contenido:{longitud}\n"
        s1.send(msg.encode())
        s1.sendall(contenido)
        log(f"Archivo enviado: {nombre} ({longitud} bytes)")

# Configuracion de conexion
dir_IP_server = "127.0.0.1"
puerto_server = 6000
dir_socket_server = (dir_IP_server, puerto_server)

# Crear y configurar el socket
s = socket(AF_INET, SOCK_STREAM)
s.bind(dir_socket_server)
s.listen()
s1, addr = s.accept()
log(f"Conexion aceptada desde {addr[0]}")

# Comandos disponibles
comandos = ["VER", "DESCARGAR", "FIN"]

# Bucle principal del servidor
while True:
    try:
        # Recibir peticion del cliente
        mensaje_rx = s1.recv(2048).decode()
        log(f"Mensaje recibido: {mensaje_rx}")

        # Verificar comando
        if mensaje_rx.split()[0] not in comandos:
            s1.send("Comando no reconocido".encode())

        else:
            # Comando FIN: cerrar la conexion
            if mensaje_rx.startswith("FIN"):
                s1.send("Cerrando conexion".encode())
                s1.close()
                log("Conexion cerrada por el cliente")
                break

            # Comando VER: listar contenidos disponibles
            elif mensaje_rx.startswith("VER"):
                ver()

            # Comando DESCARGAR: enviar archivo solicitado
            elif mensaje_rx.startswith("DESCARGAR"):
                get(mensaje_rx)

    except FileNotFoundError:
        log("ERROR: Archivo no encontrado!")
        s1.send(b"ERROR: Archivo no encontrado")
    except Exception as e:
        log(f"Error en el servidor: {str(e)}")
        s1.send("ERROR EN EL SERVIDOR".encode())
