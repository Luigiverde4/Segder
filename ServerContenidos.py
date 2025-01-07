"""
Servidor Contenidos
"""
from socket import *
from datetime import datetime
from threading import Thread, Event
import select
import os
import json
from PIL import Image, ImageDraw, ImageFont

index_encriptacion = {}

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


def MdA(nombre_limpio: str, id: str) -> None:
    """
    Añade una marca de agua a una imagen para luego encriptarla,
    sin modificar el archivo original.
    
    Args:
        nombre_limpio (str): Nombre del archivo sin encriptar al que agregar la marca de agua.
        id (str): ID del  que pide la imagen
    """      
    archivo = Image.open(f"contenido/{nombre_limpio}")
    editada = ImageDraw.Draw(archivo)

    # Parámetros de la marca de agua
    marca = id
    fuente = ImageFont.truetype('arial.ttf', 25)
    ancho, alto = archivo.size

    bbox = editada.textbbox((0,0), marca, font = fuente)
    texto_ancho, texto_alto = bbox[2] - bbox[0], bbox[3] - bbox[1]
    posicion = (ancho - texto_ancho - 50, alto - texto_alto - 50)

    editada.text(posicion, marca, font=fuente, fill=(0,0,0))
    
    # Guardar el fichero con la marca de agua
    archivo.save(f"contenido/MdA_{nombre_limpio}")


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
        mensaje_rx (str): Mensaje recibido del cliente
    Returns:
        None
    """
    nombre = mensaje_rx.split()[1]
    ruta = f"contenido/{nombre}"

    if not os.path.exists(ruta):
        log(f"Archivo no encontrado: {nombre}")
        cliente.send("400 Archivo no encontrado\n".encode())
        return

    try:
        # Verificar si el archivo está encriptado
        if index_encriptacion.get(nombre, False):
            log(f"El archivo {nombre} ya está encriptado. No se aplica marca de agua.")
            archivo_enviar = ruta  # Archivo original
        else:
            # Añadir marca de agua a una copia del archivo
            ruta_mda = f"contenido/MdA_{nombre}"
            MdA(nombre, str(clientes[cliente][1]))  # Usar el identificador asociado al cliente.
            archivo_enviar = ruta_mda  # Usar el archivo con marca de agua

        # Cargar el contenido del archivo a enviar
        with open(archivo_enviar, 'rb') as archivo:
            contenido = archivo.read()

        # Obtener la longitud del archivo
        longitud = os.stat(archivo_enviar).st_size

        # Enviar respuesta de longitud y el contenido del archivo
        cliente.send(f"200 Longitud Contenido:{longitud}\n".encode())
        cliente.sendall(contenido)

        # Si hay archivo con marca de agua, eliminarlo
        if archivo_enviar != ruta:
            os.remove(archivo_enviar)
            log(f"Archivo temporal con marca de agua eliminado: {archivo_enviar}")

        log(f"Archivo enviado: {nombre} ({longitud / 1000} KB) a {clientes[cliente]}")
    except Exception as e:
        log(f"Error al procesar la solicitud de {clientes[cliente]}: {str(e)}")
        cliente.send("500 Error interno del servidor\n".encode())

def exitear():
    """Cerrar el evento del servidor"""
    log("Servidor detenido por exitear()")
    stop_event.set()  # Señaliza que el servidor debe detenerse

def actualizarIndex()->dict:
    """
    Crea un indice del contenido del servidor a partir del JSON de licencias.
    Returns:
        dict: Diccionario con el nombre del archivo como clave y el estado de encriptación como valor.
    """
    global index_encriptacion
    try:
        with open("licencias.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        res_dict = {}
        for archivo in data.get("archivos", []):
            nombre = archivo.get("nombre", "") # "" es el valor predeterminado 
            encriptado = archivo.get("encriptado", False) # False es el valor predeterminado
            res_dict[nombre] = encriptado
        
        index_encriptacion = res_dict
    except Exception as e:
        print(f"Error al procesar el JSON licencias.json: {str(e)}")

def actualizarLicenciasJSON(listado) -> None:
    """
    Actualiza el archivo JSON de licencias con el objeto listado,
    asegurando que no haya archivos repetidos.

    listado (objeto): Objeto de Python con los datos de nombre, encriptado y iv de los archivos
    """
    # Verificar y eliminar archivos repetidos, dejando solo el más reciente
    archivos_vistos = {}
    for archivo in listado['archivos']:
        archivos_vistos[archivo['nombre']] = archivo  # Sobrescribir con el último archivo encontrado

    # Reemplazar el listado con los archivos actualizados (sin duplicados)
    listado['archivos'] = list(archivos_vistos.values())

    # Guardar el estado actualizado en el archivo JSON
    with open("licencias.json", 'w') as file:
        json.dump(listado, file, indent=4)

    actualizarIndex()

def checkEncriptacion(nombre_input:str):
    with open("licencias.json", 'r') as file:
        listado = json.load(file)

    # Buscar el archivo original en el JSON
    archivo_encontrado = None
    for archivo in listado['archivos']:
        if archivo['nombre'] == nombre_input:
            archivo_encontrado = archivo
            break

    # Si no se encuentra el archivo original, avisar
    if not archivo_encontrado:
        raise FileNotFoundError(f"El archivo {nombre_input} no se encuentra en licencias.json")

    if archivo_encontrado["encriptado"]:
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
                        estaEncriptado = checkEncriptacion(archivo)
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
    actualizarIndex()
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