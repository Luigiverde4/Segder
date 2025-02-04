from socket import socket, AF_INET, SOCK_STREAM
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa

# SOCKET CON LA UA
dir_IP_UA = '127.0.0.1'  # Dirección IP de la UA
puerto_UA = 7000         # Puerto de la UA

# Crear el socket
sua = socket(AF_INET, SOCK_STREAM)

# Conectar al servidor de la UA
dir_socket_UA = (dir_IP_UA, puerto_UA)
sua.connect(dir_socket_UA)

# PROCESADO 

def int_to_byts(i: int, length: int) -> bytes:
    """
    Convierte un numero entero en una representación en bytes.

    Args:
        i (int): El nº entero a convertir.
        length (int): La longitud de la representación en bytes.

    Returns:
        bytes: El nº entero convertido a bytes en formato big-endian.
    """
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
        mensaje_rx = sua.recv(2048).decode()
        print("Recibido el mensaje con la licencia de la UA")

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

def pedirLicencias(mensaje_tx: str) -> tuple[bytes, bytes]:
    """
    Gestiona la solicitud y recepción de licencias del servidor de licencias.

    Envía un mensaje al servidor con el nombre del archivo y la clave pública, 
    recibe la clave de desencriptado y el vector de inicialización (IV) para 
    procesar la licencia correspondiente.

    Args:
        mensaje_tx (str): El mensaje a enviar al servidor, normalmente el nombre del archivo que se está solicitando.

    Returns:
        tuple[bytes, bytes]: Una tupla que contiene:
            - iv (bytes): El vector de inicialización (IV) necesario para desencriptar el contenido.
            - k (bytes): La clave para desencriptar el contenido.
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

    print("\n Mensaje Pedir Licecncias enviado a la UA")
    sua.send(mensaje_tx.encode())
    iv,k = recibirLicencias(kpr,k_pub[0])
    return iv,k

def firmado(d: int, kpub: tuple[int, int]) -> int:
    """
    Genera una firma digital para un mensaje utilizando una clave privada RSA.

    La función crea un hash del mensaje y lo firma utilizando la clave privada (d) 
    y la clave pública (kpub) para generar la firma digital, que se puede verificar 
    posteriormente con la clave pública del emisor.

    Args:
        d (int): La clave privada RSA utilizada para firmar el mensaje.
        kpub (tuple[int, int]): La clave pública RSA del receptor, 
                                 donde el primer elemento es el módulo (n) y el segundo es el exponente (e).

    Returns:
        int: La firma digital generada a partir del hash del mensaje.
    """
    #Generamos el hash con el mensaje de comprobación
    mensaje_bits = b"Firma digital del mensaje"
    hash_m = int.from_bytes(hashlib.sha256(mensaje_bits).digest(), byteorder = 'big')
    n= kpub[0]
    e=kpub[1]
    
    firma = pow(hash_m, d, n) #Usamos pow para sacar la firma
    return firma

def generar_claves() -> tuple[int, list[int]]:
    """
    Genera una clave pública y una clave privada utilizando el algoritmo RSA.

    La función genera una clave privada y su correspondiente clave pública, 
    y luego extrae los componentes clave necesarios, como el exponente público (e), 
    el módulo (n) y la clave privada (d), para su uso en procesos de encriptación y firma digital.

    Returns:
        tuple[int, list[int]]: 
            - La clave privada (d) como un entero.
            - Una lista que contiene el módulo (n) y el exponente público (e) de la clave pública.
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

# CONTENIDO
def desencriptarContenido(k: bytes, iv: bytes, nombre_archivo: str) -> None:
    """
    Desencripta un archivo encriptado utilizando AES en modo CTR.

    Esta función lee un archivo encriptado, lo descifra utilizando la clave (k) 
    y el vector de inicialización (iv) proporcionados, y luego guarda el archivo 
    desencriptado en el mismo directorio.

    Args:
        k (bytes): La clave de encriptación para AES.
        iv (bytes): El vector de inicialización (IV) utilizado para AES en modo CTR.
        nombre_archivo (str): El nombre del archivo encriptado que se va a desencriptar.
    """
    # Cargar el archivo encriptado
    with open(f"contenido_descargado/{nombre_archivo}", "rb") as archivo_encriptado:
        datos_encriptados = archivo_encriptado.read()

    print(f"Archivo {nombre_archivo} cargado")

    # Crear el cifrador AES en modo CTR con el IV
    aes_cipher = Cipher(algorithms.AES(k), modes.CTR(iv))
    decryptor = aes_cipher.decryptor()
    datos_descifrados = decryptor.update(datos_encriptados) + decryptor.finalize()

    with open(f"contenido_descargado/{nombre_archivo}", "wb") as archivo_descifrado:
        archivo_descifrado.write(datos_descifrados)

    status = f"{nombre_archivo} desencriptado exitosamente." 
    print(status)
    sua.send(status.encode())

# Iniciar la gestión de comandos
if __name__ == "__main__":
    print("CDM INICIADO")
    while True:
        try:
            mensaje_rx = sua.recv(2048).decode()
            if mensaje_rx:
                print(f"Mensaje recibido del CDM {mensaje_rx}")

                if mensaje_rx.startswith("LICENCIA"):
                    # El formato es "LICENCIA fulanito"
                    nombreArchivoParaLicencia = mensaje_rx.split(" ")[1]
                    print(f"Licencia pedida para: {nombreArchivoParaLicencia}")

                    # Sacar iv, k
                    iv, k = pedirLicencias(nombreArchivoParaLicencia)
                    iv = iv.decode()  # IV como int
                    k = k.decode()  # k como int
                    iv = int_to_byts(int(iv), 16) # IV como bytes
                    k = int_to_byts(int(k), 16) # K como bytes
                    
                    # Desencriptar el contenido
                    desencriptarContenido(k,iv,nombreArchivoParaLicencia)
        except KeyboardInterrupt:
            print("\nInterrupción manual detectada. Cerrando conexión...")
            sua.close()
            exit()
        except Exception as e:
            print(f"Error inesperado: {e}")
