"""
Servidor Contenidos
"""
from socket import *
from datetime import datetime
from threading import Thread, Event
import select
import os
from funciones import *
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

index_encriptacion = {}
from cryptography.hazmat.primitives import padding


diContenidos=getdiContenido()
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

def checkEncriptacion(nombre_input: str, diContenidos: dict):
    # Buscar el archivo original en el diccionario
    archivo_encontrado = None
    for archivo in diContenidos['archivos']:
        if archivo['Nombre'] == nombre_input:
            archivo_encontrado = archivo
            break

    # Si no se encuentra el archivo original, avisar
    if not archivo_encontrado:
        raise FileNotFoundError(f"El archivo {nombre_input} no se encuentra en el diccionario de contenidos")

    if archivo_encontrado["Encriptado"] == 'True':
        return "True".encode()
    else:
        return "False".encode()

    

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

# Comandos disponibles
comandos = ["VER", "DESCARGAR", "FIN","checkEncriptacion"]
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
            else:
                log("\nComando erroneo\n")
            
    except EOFError:
        log("Entrada cerrada.")
        exitear()

diContenidos=getdiContenido()

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

                    elif mensaje_rx.startswith("checkEncriptacion"):
                        archivo = mensaje_rx.split(" ")[1]
                        estaEncriptado = checkEncriptacion(archivo, diContenidos)
                        sock.send(estaEncriptado)
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


# INICIO SERVIDOR
# Esperamos a que ambos hilos terminen
try:
    iniciar_log()
    actualizarIndex(diContenidos)
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