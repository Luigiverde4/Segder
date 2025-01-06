from socket import *
from datetime import datetime
from threading import Thread, Event
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import json
import select
import os

index_encriptacion = {}

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

# Encriptacion y Desencriptacion

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


# Encriptacion Decriptacion y el Index
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
    k = archivo_encontrado.get('k', "")
    if not iv or (type(iv) != int and len(iv) != 16):
        iv = os.urandom(16)
    else:
        iv = int_to_byts(iv, 16)  # Convertir a bytes si ya es válido
    
    if not k or (type(k) != int and len(k) != 16):
        k = os.urandom(16)
    else:
        k = int_to_byts(k, 16)  # Convertir a bytes si ya es válido
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
        "iv": byts_to_int(iv),  # Guardar el IV como entero
        "k": byts_to_int(k)
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
        k = archivo_encontrado["k"]
        k = int_to_byts(k,16)
        # Verificar el tamaño del IV
        if len(iv) == 16:
            print("IV es válido para el cifrado.")
        else:
            print(f"Error: IV no tiene 16 bytes, tiene {len(iv)} bytes.")
            return
        
        # Verificar el tamaño del k
        if len(k) == 16:
            print("k es válido para el cifrado.")
        else:
            print(f"Error: k no tiene 16 bytes, tiene {len(k)} bytes.")
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
            "iv": byts_to_int(iv),  # Guardar el IV como entero
            "k": byts_to_int(k)  # Guardar el IV como entero
        }
        listado['archivos'].append(nuevo_archivo)

        # Actualizar licencias.json y el indice
        actualizarLicenciasJSON(listado)

        log(f"Archivo {nombre_input} desencriptado y guardado como {nombre_limpio}")

    except Exception as e:
        print(f"Ha ocurrido un error al desencriptar el archivo: {e}")

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
        k = archivo_info.get('k', '')
        
        # Verifica si el archivo esta presente en la carpeta 'contenido'
        if archivo_nombre in archivos_en_carpeta:
            print(f"El archivo '{archivo_nombre}' esta en la carpeta. Encriptable: {encriptable}. iv: {vector} Encriptado: {encriptado}. k: {k}")
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
    k_rsa = os.urandom(16) # Generamos las claves que vamos a usar para encriptar en CTR las claves de los contenidos
    IV_rsa = os.urandom(16)

    msj = mensaje_rx.split("-")
    print(msj)
    k_pub = msj[2] # Recibimos la clave pública como string
    k_pub = [int(num) for num in k_pub.strip("[]").split(",")] # Pasamos de string a lista con los elementos [n,e]
    print("Número gigante:",byts_to_int(k_rsa))
    k_rsa_encrypt = pow(byts_to_int(k_rsa),k_pub[1],k_pub[0]) # Encriptado la clave k_rsa que vamos a enviar
    for archivo in datos_json.get('archivos', []):
        if archivo['nombre'] == msj[0]:
            k = archivo.get("k")
            clave_c = archivo.get("iv")
            print(clave_c)
            # clave_c es un string
            print("Clave_c: ", clave_c)
            if not k:
                sock.send("El archivo no está encriptado\n".encode())
                log(f"El archivo solicitado {msj[0]} no esta cifrado")
            else:
                aesCipherCTR = Cipher(algorithms.AES(k_rsa),modes.CTR(IV_rsa))
                aesEncryptorCTR = aesCipherCTR.encryptor()
                k_encrypt = aesEncryptorCTR.update(int_to_byts(k,16))
                print("pasamos")
                mensaje_iv = f"Vector: {clave_c} Clave: {byts_to_int(k_encrypt)} K_RSA: {k_rsa_encrypt} IV_RSA: {byts_to_int(IV_rsa)}"
                sock.send(str(mensaje_iv).encode())

                log(f"El archivo solicitado {msj[0]} si está cifrado")


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
                        mensaje_rx = sock.recv(2048).decode()
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



# Interfaz servidor
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

            elif consola.startswith("encrypt"):
                _, nombre_limpio, nombre_sucio = consola.split()
                encrypt(nombre_limpio, nombre_sucio)

            elif consola.startswith("decrypt"):
                _, nombre_limpio, nombre_sucio = consola.split()
                decrypt(nombre_limpio, nombre_sucio)
            else:
                log("\nComando erroneo\n")

    except EOFError:
        log("Entrada cerrada.")
        exitear()
                 
#Se crean los hilos
actualizarIndex()
hilo_server = Thread(target=server)
hilo_serverInterface = Thread(target=serverInterface)

hilo_server.start()
hilo_serverInterface.start()


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