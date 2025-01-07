from socket import *
from datetime import datetime
from threading import Thread, Event
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
from PIL import Image, ImageDraw, ImageFont
from funciones import *
import hashlib

import select
import os

index_encriptacion = {}

#Ahora producimos el hash
mensaje_bits = b"Firma digital del mensaje"
valor_hash = int.from_bytes(hashlib.sha256(mensaje_bits).digest(), byteorder = 'big')

# Detenemos el server
def exitear():
    """Cerrar el evento del servidor"""
    log("Servidor detenido por exitear()")
    stop_event.set()  # Señaliza que el servidor debe detenerse

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

def MdA(foto):
    """
    Añade una marca de agua a una fotografia
    Args: foto, la ruta de acceso al archivo que se va a modificar
    """      

    archivo = Image.open(f"contenido/{foto}")
    editada = ImageDraw.Draw(archivo)

    #Parametros de la marca de agua
    marca = "sexoydrogas"
    fuente = ImageFont.truetype('arial.ttf', 25)
    ancho, alto = archivo.size

    bbox = editada.textbbox((0,0), marca, font = fuente)
    texto_ancho, texto_alto = bbox[2] - bbox[0], bbox[3] - bbox[1]
    posicion = (ancho - texto_ancho - 50, alto - texto_alto - 50)

    editada.text(posicion, marca, font=fuente, fill=(0,0,0))
    archivo.save(f"contenido/{foto}")

# Encriptacion Decriptacion y el Index
def encrypt(nombre_input: str, nombre_sucio: str, diContenidos: dict) -> None:
    """
    Encripta un fichero y lo guarda con un nuevo nombre.

    Args:
        nombre_input (str): Nombre del fichero a encriptar.
        nombre_sucio (str): Nombre del fichero encriptado.
        diContenidos (dict): Diccionario que contiene la lista de archivos y sus propiedades.
    """
    # Buscar el archivo original en el diccionario
    archivo_encontrado = None
    for archivo in diContenidos['archivos']:
        if archivo['Nombre'] == nombre_input:
            formato = os.path.splitext(archivo['Nombre'])[1]
            if formato in [".jpeg",".jpg",".png",".bmp"]:
                MdA(archivo['Nombre'])
            formato = os.path.splitext(archivo['Nombre'])[1]
            archivo_encontrado = archivo
            break

    # Si no se encuentra el archivo original, avisar
    if not archivo_encontrado:
        raise FileNotFoundError(f"El archivo {nombre_input} no se encuentra en diContenidos")

    print("PRE generar IV y K")
    # Obtener el IV o generarlo si no existe o es inválido
    iv = archivo_encontrado.get('IV', "")
    k = archivo_encontrado.get('K', "")
    if not iv or (type(iv) != int and len(iv) != 16):
        iv = os.urandom(16)
    else:
        iv = int_to_byts(iv, 16)  # Convertir a bytes si ya es válido
    
    if not k or (type(k) != int and len(k) != 16):
        k = os.urandom(16)
    else:
        k = int_to_byts(k, 16)  # Convertir a bytes si ya es válido
    
    print("POST generar IV y K")
    # Si el archivo original ya está encriptado, no tiene sentido volver a encriptarlo
    if archivo_encontrado.get('Encriptado', 'False') == 'True':
        log(f"El archivo {archivo_encontrado['Nombre']} ya está encriptado.")

        return

    print("El archivo no esta encriptado")

    # Cifrar el contenido del archivo original
    aesCipher_CTR = Cipher(algorithms.AES(k), modes.CTR(iv))
    aesEncryptor_CTR = aesCipher_CTR.encryptor()

    # Abrir el contenido del archivo sin encriptar
    ruta_original = os.path.join("contenido", nombre_input)
    with open(ruta_original, 'rb') as archivo_limpio:
        contenido = archivo_limpio.read()

    print("Encriptamos el archivo")
    # Encriptar
    contenido_encriptado = aesEncryptor_CTR.update(contenido) + aesEncryptor_CTR.finalize()

    print("Guardamos el archivo")
    # Guardar el contenido cifrado con el nuevo nombre
    ruta_encriptada = os.path.join("contenido", nombre_sucio)
    with open(ruta_encriptada, 'wb') as archivo_encriptado:
        archivo_encriptado.write(contenido_encriptado)

    # Agregar el nuevo archivo cifrado al diccionario
    nuevo_archivo = {
        "Nombre": nombre_sucio,
        "Encriptado": 'True',
        "IV": byts_to_int(iv),  # Guardar el IV como entero
        "K": byts_to_int(k)
    }
    diContenidos['archivos'].append(nuevo_archivo)

    # Actualizar el índice
    actualizarLicenciasJSON(diContenidos)

    log(f"Archivo {nombre_input} encriptado y guardado como {nombre_sucio}")


def decrypt(nombre_input: str, nombre_limpio: str, diContenidos: dict) -> None:
    """
    Desencripta el archivo de imagen.

    nombre_input (str): Nombre del archivo a desencriptar.
    nombre_limpio (str): Nombre del archivo desencriptado a guardar.
    """
    try:
        # Cargar el archivo encriptado
        with open(f"contenido/{nombre_input}", "rb") as archivo_encriptado:
            x = archivo_encriptado.read()  # Lee el archivo en bytes

        # Buscar el archivo original en el diccionario
        archivo_encontrado = None
        for archivo in diContenidos['archivos']:
            if archivo['Nombre'] == nombre_input:
                archivo_encontrado = archivo
                break

        iv = archivo_encontrado["IV"]
        iv = int_to_byts(iv, 16)
        k = archivo_encontrado["K"]
        k = int_to_byts(k, 16)
        
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

        # Agregar el nuevo archivo desencriptado al diccionario
        nuevo_archivo = {
            "Nombre": nombre_limpio,
            "Encriptado": 'False',
            "IV": byts_to_int(iv),  # Guardar el IV como entero
            "K": byts_to_int(k)  # Guardar el K como entero
        }
        diContenidos['archivos'].append(nuevo_archivo)

        # Actualizar el índice
        actualizarLicenciasJSON(diContenidos)

        log(f"Archivo {nombre_input} desencriptado y guardado como {nombre_limpio}")

    except Exception as e:
        print(f"Ha ocurrido un error al desencriptar el archivo: {e}")

# Crea el diccionario de las licencias y contenidos
diContenidos=getdiContenido()

# Ruta a la carpeta 'contenido' donde están guardados los archivos
ruta_contenido = 'contenido'

# Richichi te he cambiado esta funcion nose si la utilizaras o klk pero creo que deberia estar adaptada
def verificar_archivos(diContenidos, carpeta) -> None:
    """Recorre el diccionario y comprueba que exista el archivo y te dice si es encriptable
    
    Args:
        diContenidos (dict): El diccionario que contiene la informacion de los archivos
        carpeta (str): La ruta de la carpeta donde se encuentran los archivos
    Returns:
        None
    """
    archivos_en_carpeta = os.listdir(carpeta)
    
    # Recorre cada archivo en el diccionario y verifica si existe en la carpeta
    for archivo_info in diContenidos['archivos']:
        archivo_nombre = archivo_info['Nombre']
        encriptable = archivo_info['Encriptado'] == 'True'  # Verificar si es encriptable (basado en si está encriptado)
        vector = archivo_info.get('IV', '')
        encriptado = archivo_info['Encriptado']
        k = archivo_info.get('K', '')
        
        # Verifica si el archivo está presente en la carpeta 'contenido'
        if archivo_nombre in archivos_en_carpeta:
            print(f"El archivo '{archivo_nombre}' está en la carpeta. Encriptable: {encriptable}. IV: {vector} Encriptado: {encriptado}. K: {k}")
        else:
            print(f"El archivo '{archivo_nombre}' no se encuentra en la carpeta.")




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

def comprueba_firma(firma, publica, valor_hash):
    """
    Descifra la firma digital del mensaje, asegurando que este es correcto
        Args:
    firma: La firma digital generada en la aplicacion
    publica: La clave publica que usaremos para descifrar el hash
    valor_hash: El valor que calculamos del hash, nos servira para comprobar la veracidad del mensaje
    """
    #Genera los números públicos para el descifrado
    publica = [int(num) for num in publica.strip("[]").split(",")]
    n = publica[0]
    e= publica[1]
    
    firma_entero = int(firma)
    
    hash_d = pow(firma_entero, e, n)
    if hash_d == valor_hash:
        log('Firma digital válida')
    else:
        log('Firma invalida, mensaje corrupto')

def sacarIV(sock: socket, mensaje_rx: str, diContenidos: dict) -> None:
    """
    Itera sobre los archivos y manda su IV.

    sock (Socket): Socket del cliente que estamos tratando
    mensaje_rx (str): Nombre del archivo a desencriptar
    """
    # Generamos la clave RSA
    k_rsa = os.urandom(16)  # Generamos las claves que vamos a usar para encriptar en CTR las claves de los contenidos
    IV_rsa = os.urandom(16)

    msj = mensaje_rx.split("-")
    print(msj)

    # Encriptamos la clave RSA
    k_pub = msj[1]  # Recibimos la clave pública como string
    k_pub = [int(num) for num in k_pub.strip("[]").split(",")]  # Pasamos de string a lista con los elementos [n, e]
    k_rsa_encrypt = pow(byts_to_int(k_rsa), k_pub[1], k_pub[0])  # Encriptado la clave k_rsa que vamos a enviar
    
    for archivo in diContenidos.get('archivos', []):
        print(f"MSJ 0 {msj[0]}")
        print(f"Archivo[nombre] {archivo['Nombre']}")
        if archivo['Nombre'] == msj[0]:
            print(f"EN EL IF {archivo['Nombre']}")
            k = archivo.get("K")
            clave_c = archivo.get("IV")
            print(clave_c)
            # clave_c es un string
            print("Clave_c: ", clave_c)
            if not k:
                sock.send("El archivo no está encriptado\n".encode())
                log(f"El archivo solicitado {msj[0]} no está cifrado")
            else:
                aesCipherCTR = Cipher(algorithms.AES(k_rsa), modes.CTR(IV_rsa))
                aesEncryptorCTR = aesCipherCTR.encryptor()
                k_encrypt = aesEncryptorCTR.update(int_to_byts(k, 16))
                print("pasamos")
                mensaje_iv = f"Vector: {clave_c} Clave: {byts_to_int(k_encrypt)} K_RSA: {k_rsa_encrypt} IV_RSA: {byts_to_int(IV_rsa)}"
                sock.send(str(mensaje_iv).encode())

                log(f"El archivo solicitado {msj[0]} sí está cifrado")



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
                            mensaje, publica, firma = mensaje_rx.split("-")
                            log(f"Archivo pedido  {clientes[sock]}: {mensaje}")
                            comprueba_firma(firma, publica, valor_hash)
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
                encrypt(nombre_limpio, nombre_sucio,diContenidos)

            elif consola.startswith("decrypt"):
                _, nombre_limpio, nombre_sucio = consola.split()
                decrypt(nombre_limpio, nombre_sucio,diContenidos)
            else:
                log("\nComando erroneo\n")

    except EOFError:
        log("Entrada cerrada.")
        exitear()
                 
#Se crean los hilos
actualizarIndex(diContenidos)
hilo_server = Thread(target=server)
hilo_serverInterface = Thread(target=serverInterface)

hilo_server.start()
hilo_serverInterface.start()


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