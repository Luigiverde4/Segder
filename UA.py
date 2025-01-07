from socket import socket, AF_INET, SOCK_STREAM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
import hashlib


# ServerContenidos 
dir_IP_servidor_contenido = '127.0.0.1'
puerto_servidor_contenidos = 6000
sc = socket(AF_INET, SOCK_STREAM)
sc.connect((dir_IP_servidor_contenido, puerto_servidor_contenidos))

# Server Licencias
dir_IP_servidor_licencias = '127.0.0.1'
puerto_servidor_licencias = 6001



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

def byts_to_int(b)->int:
    """
    Pasa bytes a int

    b (bytes): Clave VI a pasar de int a bytes
    """
    return int.from_bytes(b,byteorder="big")

# LICENCIAS

def recibirLicencias(kpr,n) -> None:
    """Funcion para recibir las claves de descifrado
    Arg: kpr: Clave privada para descifrar el mensaje recibido
         n: Modulo para descifrar el mensaje recibido
    """
    try:
        print("En recibir licencias")
        mensaje_rx = sl.recv(2048).decode()
        print("Recibido el mensaje")
        if not mensaje_rx:
            print("Error: No se recibió respuesta del servidor de licencias")
        else:
            respuesta = mensaje_rx.split() # Recibimos la respuesta en una lista: la posición 1 es la IV para desencriptar, la posición 3 es la clave para desencriptar encriptada con AES
                                           # la posición 5 es lañ clave con la que se ha encriptado en AES la clave k, encriptada con RSA y la posición 7 es la IV usada para encriptar con AES la clave k
            k_rsa_encrypt = int(respuesta[5]) # Pasamos a int la k_rsa encriptada
            IV_rsa = int_to_byts(int(respuesta[7]),16) # Obtenemos en bytes la IV_rsa
            k_rsa = int_to_byts((pow(k_rsa_encrypt,kpr,n)),16) # Descencritamos la k_rsa con la clave privada y el modulo n, y la pasamos a bytes

            aesCipherCTR = Cipher(algorithms.AES(k_rsa),modes.CTR(IV_rsa))
            aesDecryptorCTR = aesCipherCTR.decryptor()
            k = aesDecryptorCTR.update(int_to_byts(int(respuesta[3]),16)) # Desencriptamos la k para desencriptar contenido y la pasamos a bytes
            if len(respuesta) == 8:
                print("Clave recibida")
                iv = respuesta[1].encode() 
                k = str(byts_to_int(k)).encode() # Pasamos la clave a int y hacemos encode()
                # print(iv,k)
                return iv,k
            else:
                print("cuidadin")
                print(mensaje_rx)
    except Exception as e:
        print(f"Ha ocurrido un error al recibir la respuesta del servidor: {e}")

def pedirLicencias(mensaje_tx:str)->None:
    """
        Gestionar si se descarga y recibir licencias del servidor de licencias
    """
    # Coger el nombre del archivo que hemos pedido para pedir el IV
    archivo = mensaje_tx
    print(archivo)
    # Pedir el IV
    # Generamos las claves
    kpr,k_pub = generar_claves()
    firma=firmado(kpr,k_pub)
    print("Clave pública:",k_pub)
    mensaje_tx = f"{archivo}-{k_pub}-{firma}"
    sl.send(mensaje_tx.encode())
    iv,k = recibirLicencias(kpr,k_pub[0])
    return iv,k

def firmado(d,kpub):
    """
    Genera un hash a partir del mensaje que vamos a mandar al servidor de licencias con la firma digital
        Args:
    mensaje: El mensaje que mandamos, será solamente el niombre del archivo del que solicitamos licencia
    privada: La clave privada RSA, la cual se usa de base para encriptar el mensaje
    """
    #Generamos el hash con el mensaje de comprobación
    mensaje_bits = b"Firma digital del mensaje"
    hash_m = int.from_bytes(hashlib.sha256(mensaje_bits).digest(), byteorder = 'big')
    n= kpub[0]
    e=kpub[1]
    
    firma = pow(hash_m, d, n) #Usamos pow para sacar la firma
    return firma

def generar_claves():
    """
    Genera una clave pública y una clave privada
    """
    kpr = rsa.generate_private_key(65537,2048)
    k_pub = kpr.public_key()
    private_number = kpr.private_numbers()
    
    public_numbers = k_pub.public_numbers()
    n = public_numbers.n
    # print("n",n)
    e = public_numbers.e
    
    d = private_number.d
    
    return d,[n,e]
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
        iv,k = pedirLicencias(nombre_archivo)
        print("IV decodificado:", iv)
        print("k decodificado:", k)
        iv = iv.decode()  # IV como int
        k = k.decode()  # IV como int
        iv = int_to_byts(int(iv), 16)
        k = int_to_byts(int(k), 16)
        

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
