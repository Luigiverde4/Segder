from socket import *
from datetime import datetime
from threading import Thread, Event
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from PIL import Image, ImageDraw, ImageFont
from funciones import *
import hashlib
import random
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

# PROCESADO 
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


# Marca de Agua
def generar_posicion_aleatoria(ancho: int, alto: int, margen: int = 25) -> tuple[int, int]:
    """
    Genera una posición aleatoria para la marca de agua dentro de los límites de la imagen.
    
    Args:
        ancho (int): Ancho de la imagen.
        alto (int): Alto de la imagen.
        margen (int): Margen mínimo desde los bordes de la imagen.
        
    Returns:
        tuple[int, int]: Coordenadas (x, y) de la posición aleatoria.
    """
    # la hora como generador de seed para que vaya cambiando
    ahora = datetime.now()
    random.seed(ahora.second + ahora.microsecond)
    
    # Calcular pos en el area valida
    x = random.randint(margen, ancho - margen)
    y = random.randint(margen, alto - margen)
    
    return x, y

def MdA(nombre_limpio: str, nombre_sucio: str,marca: str) -> None:
    """
    Añade una marca de agua a una imagen para luego encriptarla,
    sin modificar el archivo original.
    
    Args:
        nombre_limpio (str): Nombre del archivo sin encriptar al que agregar la marca de agua.
        nombre_sucio (str): Nombre del archivo que se va a encriptar.
        marca (str): String que se va a usar para marcar la imagen 
    """      
    archivo = Image.open(f"contenido/{nombre_limpio}")
    editada = ImageDraw.Draw(archivo)

    # Parámetros de la marca de agua
    fuente = ImageFont.truetype('arial.ttf', 25)
    ancho, alto = archivo.size

    marca = os.urandom(8)
    bbox = editada.textbbox((0,0), marca, font = fuente)
    texto_ancho, texto_alto = bbox[2] - bbox[0], bbox[3] - bbox[1]
    posicion = generar_posicion_aleatoria(ancho - texto_ancho, alto - texto_alto)

    editada.text(posicion, marca, font=fuente, fill=(0,0,0))
    
    # Guardar el fichero con la marca de agua
    archivo.save(f"contenido/MdA_{nombre_sucio}")

# Encriptacion Decriptacion
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
                MdA(archivo['Nombre'],nombre_sucio, "mirar_meter_socket")
            formato = os.path.splitext(archivo['Nombre'])[1]
            archivo_encontrado = archivo
            break

    # Si no se encuentra el archivo original, avisar
    if not archivo_encontrado:
        raise FileNotFoundError(f"El archivo {nombre_input} no se encuentra en diContenidos")

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
    
    # Si el archivo original ya está encriptado, no tiene sentido volver a encriptarlo
    if archivo_encontrado.get('Encriptado', 'False') == 'True':
        log(f"El archivo {archivo_encontrado['Nombre']} ya está encriptado.")

        return

    print("El archivo no esta encriptado")

    # Cifrar el contenido del archivo original
    aesCipher_CTR = Cipher(algorithms.AES(k), modes.CTR(iv))
    aesEncryptor_CTR = aesCipher_CTR.encryptor()

    # Abrir el contenido del archivo sin encriptar
    ruta_original = os.path.join("contenido",f"MdA_{nombre_sucio}")
    with open(ruta_original, 'rb') as archivo_limpio:
        contenido = archivo_limpio.read()

    # Borramos el archivo temporal con la marca de agua
    os.remove(ruta_original)

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

# LICENCIAS
def comprueba_firma(firma: str, publica: str, valor_hash: int) -> None:
    """Descifra la firma digital del mensaje, asegurando que este es correcto.
    Args:
        firma (str): La firma digital generada en la aplicación
        publica (str): La clave pública que usaremos para descifrar el hash
        valor_hash (int): El valor que calculamos del hash, nos servirá para comprobar la veracidad del mensaje
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
    """Itera sobre los archivos y manda su IV.
    
    Args:
        sock (socket): Socket del cliente que estamos tratando.
        mensaje_rx (str): Nombre del archivo a desencriptar.
        diContenidos (dict): Diccionario con la información de los contenidos.
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
    print("hemos llegao aqui")
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
                k = int(k)
                k_encrypt = aesEncryptorCTR.update(int_to_byts(k, 16))
                print("pasamos")
                mensaje_iv = f"Vector: {clave_c} Clave: {byts_to_int(k_encrypt)} K_RSA: {k_rsa_encrypt} IV_RSA: {byts_to_int(IV_rsa)}"
                sock.send(str(mensaje_iv).encode())

                log(f"El archivo solicitado {msj[0]} sí está cifrado")

# LOGS
def iniciar_log() -> None:
    """Escribe un mensaje de inicio en el log al iniciar el servidor anadiendo una linea en blanco si ya existe el archivo.
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

def log(msj: str) -> None:
    """Guarda un log con el tiempo y el mensaje en un archivo de texto.
    Args:
        msj (str): Mensaje a guardar en el log
    """
    try:
        with open("logs/log_licencias.txt", "a") as log_file:
            log_entry = f"{datetime.now().strftime('%H:%M:%S')} - {msj}"
            print(log_entry)
            log_file.write(f"{log_entry}\n")
    except FileNotFoundError:
        print("ERROR: El archivo log.txt no existe y no se puede acceder.")
        raise 


# Crea el diccionario de las licencias y contenidos
diContenidos=getdiContenido()

# Ruta a la carpeta 'contenido' donde están guardados los archivos
ruta_contenido = 'contenido'

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
                            sacarIV(sock,mensaje_rx,diContenidos)

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