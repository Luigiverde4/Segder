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

def byts_to_int(b)->int:
    """
    Pasa bytes a int

    b (bytes): Clave VI a pasar de int a bytes
    """
    return int.from_bytes(b,byteorder="big")

def int_to_byts(i, length)->bytes:
    """
    Pasa un int a bytes
    """
    return i.to_bytes(length, byteorder="big")


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

def encrypt(nombre_input: str, nombre_sucio: str) -> None:
    """
    Encripta un fichero y lo guarda con un nuevo nombre.

    Args:
        nombre_input (str): Nombre del fichero a encriptar.
        nombre_sucio (str): Nombre del fichero encriptado.
    """
    # Cargar el contenido de licencias.json
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

    # Obtener el IV o generarlo si no existe o es inválido
    iv = archivo_encontrado.get('iv', "")
    if not iv or (type(iv) != int and len(iv) != 16):
        iv = os.urandom(16)
        archivo_encontrado['iv'] = byts_to_int(iv)  # Actualizar el IV en el original como entero
    else:
        iv = int_to_byts(iv, 16)  # Convertir a bytes si ya es válido

    # Si el archivo original ya está encriptado, no tiene sentido volver a encriptarlo
    if archivo_encontrado.get('encriptado', False):
        log(f"El archivo {archivo_encontrado['nombre']} ya está encriptado.")
        return

    # Cifrar el contenido del archivo original
    aesCipher_CTR = Cipher(algorithms.AES(k), modes.CTR(iv))
    aesEncryptor_CTR = aesCipher_CTR.encryptor()

    # Abrir el contenido del archivo sin encriptar
    ruta_original = os.path.join("contenido", nombre_input)
    with open(ruta_original, 'rb') as archivo_limpio:
        contenido = archivo_limpio.read()

    # Encriptar
    contenido_encriptado = aesEncryptor_CTR.update(contenido) + aesEncryptor_CTR.finalize()

    # Guardar el contenido cifrado con el nuevo nombre
    ruta_encriptada = os.path.join("contenido", nombre_sucio)
    with open(ruta_encriptada, 'wb') as archivo_encriptado:
        archivo_encriptado.write(contenido_encriptado)

    # Agregar el nuevo archivo cifrado a licencias.json
    nuevo_archivo = {
        "nombre": nombre_sucio,
        "encriptado": True,
        "iv": byts_to_int(iv)  # Guardar el IV como entero
    }
    listado['archivos'].append(nuevo_archivo)

    # Actualizar licencias.json y el indice
    actualizarLicenciasJSON(listado)

    log(f"Archivo {nombre_input} encriptado y guardado como {nombre_sucio}")

def decrypt(nombre_input: str,nombre_limpio:str)->None:
    """
    Desencripta el archivo de imagen.

    nombre_input (str): Nombre del archivo a desencriptar.
    nombre_limpio (str): Nombre del archivo desencriptado a guardar.
    """
    try:
        # Cargar el archivo encriptado
        with open(f"contenido/{nombre_input}", "rb") as archivo_encriptado:
            x = archivo_encriptado.read()  # Lee el archivo en bytes

        # Obtener el IV de licencias.json
        with open("licencias.json", 'r') as file:
            listado = json.load(file)

        # Buscar el archivo original en el JSON
        archivo_encontrado = None
        for archivo in listado['archivos']:
            if archivo['nombre'] == nombre_input:
                archivo_encontrado = archivo
                break

        iv = archivo_encontrado["iv"]
        iv = int_to_byts(iv,16)
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
        with open(f"contenido/{nombre_limpio}", "wb") as archivo_descifrado_output:
            archivo_descifrado_output.write(archivo_descifrado)

        # Agregar el nuevo archivo cifrado a licencias.json
        nuevo_archivo = {
            "nombre": nombre_limpio,
            "encriptado": False,
            "iv": byts_to_int(iv)  # Guardar el IV como entero
        }
        listado['archivos'].append(nuevo_archivo)

        # Actualizar licencias.json y el indice
        actualizarLicenciasJSON(listado)

        log(f"Archivo {nombre_input} desencriptado y guardado como {nombre_limpio}")

    except Exception as e:
        print(f"Ha ocurrido un error al desencriptar el archivo: {e}")

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

def actualizarLicenciasJSON(listado)->None:
    """
    Actualiza el archivo JSON de licencias con el objeto listado

    listado (objeto): Objeto de Python con los datos de nombre, encriptado y iv de los archivos
    """
    # Guardar el estado actualizado en el archivo JSON
    with open("licencias.json", 'w') as file:
        json.dump(listado, file, indent=4)

    actualizarIndex()

# INICIO SERVIDOR
try:
# Llamamos a iniciar_log al arrancar el servidor para crearlo si o si
    iniciar_log()
    actualizarIndex()
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
            
            elif consola.startswith("encrypt"):
                _, nombre_limpio, nombre_sucio = consola.split()
                encrypt(nombre_limpio, nombre_sucio)

            elif consola.startswith("decrypt"):
                _, nombre_limpio, nombre_sucio = consola.split()
                decrypt(nombre_limpio, nombre_sucio)
                
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