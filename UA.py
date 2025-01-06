from socket import socket, AF_INET, SOCK_STREAM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
import hashlib

# Clave de cifrado
k = b'\x0f\x02\xf8\xcc#\x99\xe9<7[3\xc9T\x0b\xd5I'

# ServerContenidos 
dir_IP_servidor_contenido = '127.0.0.1'
puerto_servidor_contenidos = 6000
sc = socket(AF_INET, SOCK_STREAM)
sc.connect((dir_IP_servidor_contenido, puerto_servidor_contenidos))

# Server Licencias
dir_IP_servidor_licencias = '127.0.0.1'
puerto_servidor_licencias = 6001

exponente = 65537
tam = 2048
privada = rsa.generate_private_key(exponente, tam)



sl = socket(AF_INET, SOCK_STREAM)
sl.connect((dir_IP_servidor_licencias, puerto_servidor_licencias))

# SOCKET CON EL CDM
dir_IP_CDM = '127.0.0.1'   # Dirección IP donde escuchará la UA para conexiones del CDM
puerto_CDM = 7000          # Puerto en el que la UA espera la conexión del CDM

# Crear el socket para la UA
s_cdm = socket(AF_INET, SOCK_STREAM)
dir_socket_UA = (dir_IP_CDM, puerto_CDM)
s_cdm.bind(dir_socket_UA)
s_cdm.listen(5)
print("Esperando conexión del CDM...")

def int_to_byts(i, length):
    return i.to_bytes(length, byteorder="big")

# LICENCIAS

def recibirLicencias() -> None:
    """Funcion para recibir las claves de descifrado"""
    try:
        mensaje_rx = sl.recv(2048).decode()

        if not mensaje_rx:
            print("Error: No se recibió respuesta del servidor de licencias")

        else:
            mensaje = mensaje_rx
            respuesta = mensaje.split()
            if len(respuesta) == 2:
                print("Clave recibida")
                iv = respuesta[1].encode()
                return iv
            else:
                print(mensaje_rx)

    except Exception as e:
        print(f"Ha ocurrido un error al recibir la respuesta del servidor: {e}")

def pedirLicencias(mensaje_tx:str)->None:
    """
        Gestionar si se descarga y recibir licencias del servidor de licencias
    """
    # Coger el nombre del archivo que hemos pedido para pedir el IV
    partes = mensaje_tx.split()
    archivo = partes[1]
    mensaje_tx = f"{archivo}"
    firma, valor_hash = firmado(privada)
    mensaje_tx = f"{archivo} f{firma}"
    
    sl.send(mensaje_tx.encode())
    iv = recibirLicencias()
    print("IV conseguido ", iv)
    return iv

def firmado(privada):
    """
    Genera un hash a partir del mensaje que vamos a mandar al servidor de licencias con la firma digital
        Args:
    mensaje: El mensaje que mandamos, será solamente el niombre del archivo del que solicitamos licencia
    privada: La clave privada RSA, la cual se usa de base para encriptar el mensaje
    """
    #Generamos el hash con el mensaje de comprobación
    mensaje_bits = b"Firma digital del mensaje"
    hash_m = int.from_bytes(hashlib.sha256(mensaje_bits).digest(), byteorder = 'big')
    
    #Ahora sacamos de la clave privada los numeros para la encriptacion con pow
    numeros_privados = privada.private_numbers()
    n = numeros_privados.n
    d = numeros_privados.d
    
    firma = pow(hash_m, d, n) #Usamos pow para sacar la firma
    return firma


# CONTENIDOS
def decrypt(nombre_archivo: str):
    """
    Desencripta un archivo con el IV proporcionado.

    Args:
        nombre_archivo (str): Nombre del archivo a desencriptar.
        iv (bytes): Vector de inicialización (IV).
    """
    try:
        # Comprobar si esta encriptado
        if not comprobarEncriptado(nombre_archivo):
            print("El archivo no está encriptado.")
            return
        
        print("Esta encriptado")

        # Cargar el archivo encriptado
        with open(f"contenido_descargado/{nombre_archivo}", "rb") as archivo_encriptado:
            datos_encriptados = archivo_encriptado.read()

        print("Archivo cargado", nombre_archivo)

        # Obtener el IV desde el servidor
        iv = pedirLicencias(nombre_archivo)
        iv = iv.decode()  # IV como int
        iv = int_to_byts(int(iv), 16)
        print("IV decodificado:", iv)

        # Crear el cifrador AES en modo CTR con el IV
        aes_cipher = Cipher(algorithms.AES(k), modes.CTR(iv))
        decryptor = aes_cipher.decryptor()
        datos_descifrados = decryptor.update(datos_encriptados) + decryptor.finalize()

        with open(f"contenido_descargado/{nombre_archivo}", "wb") as archivo_descifrado:
            archivo_descifrado.write(datos_descifrados)

        print(f"{nombre_archivo} desencriptado exitosamente.")
    except Exception as e:
        print(f"Error al desencriptar el archivo {nombre_archivo}: {e}")

def descargar(mensaje_cdm: str):
    """
    Descarga el contenido solicitado del servidor de contenidos.

    Args:
        mensaje_cdm (str): Comando a mandar al servidor de contenidos
    """
    partes = mensaje_cdm.split()

    # Verificamos si se ha proporcionado el nombre del archivo
    if len(partes) < 2:
        scdm.send(b"ERROR: Falta el nombre del archivo.")
        return
    
    # Enviamos el mensaje de solicitud al servidor
    nombre_archivo = partes[1]
    sc.send(mensaje_cdm.encode())
    respuesta = sc.recv(2048)

    # Verificamos si la respuesta del servidor es correcta
    if respuesta.decode().startswith("200"):
        # Calcular la longitud del archivo
        longitud = int(respuesta.decode().split(":")[1].strip())
        print(f"Tamaño del archivo a descargar: {longitud/1000} KB")

        # Escribir el archivo
        with open(f"contenido_descargado/{nombre_archivo}", "wb") as archivo:
            bytes_descargados = 0

            # Vamos descargando los bytes del fichero
            while bytes_descargados < longitud:
                datos = sc.recv(2048)

                # Si no se recibe datos, paramos
                if not datos:
                    break

                # Escribimos en el archivo
                archivo.write(datos)
                bytes_descargados += len(datos)

            # Comprobamos el estado de la descarga
            if bytes_descargados >= longitud:
                scdm.send(b"204 - DESCARGA COMPLETA")
            else:
                scdm.send(b"ERROR: Descarga incompleta.")

        decrypt(nombre_archivo)
    else:
        scdm.send(b"ERROR: Archivo no encontrado en el servidor.")

def comprobarEncriptado(nombre_archivo):
    mensaje_rx = f"checkEncriptacion {nombre_archivo}".encode()
    sc.send(mensaje_rx)

    response = sc.recv(1024) 
    if response == b'True':
        return True
    elif response == b'False':
        return False
    else:
        return None

def manejar_cdm():
    """
    Maneja las solicitudes del CDM.

    Args:
        conn (socket): Conexión con el CDM.
        addr (tuple): Dirección del CDM.
    """
    while True:
        try:
            # Recibir mensaje del CDM
            mensaje_cdm = scdm.recv(1024).decode()

            if not mensaje_cdm:
                break  # Si no se recibe mensaje, cerramos la conexión
            
            if mensaje_cdm.startswith("VER"):
                print("La UA quiere VER -> Sevidor Contenidos")
                # Ver contenido del Servidor de Contenido
                sc.send("VER".encode())
                respuesta = sc.recv(2048)
                scdm.send(respuesta)

            elif mensaje_cdm.startswith("DESCARGAR"):
                descargar(mensaje_cdm)
            else:
                scdm.send(b"ERROR: Comando no reconocido.")

        except Exception as e:
            print(f"Error al manejar solicitud del CDM: {e}")
            exit()

    scdm.close()

scdm, addr = s_cdm.accept()
print("Conexion con el CDM!") 
if __name__ == "__main__":
    try:
        while True:
            manejar_cdm()
    except KeyboardInterrupt:
        print("Cerrando UA...")
        sc.close()
        sl.close()
        scdm.close()
