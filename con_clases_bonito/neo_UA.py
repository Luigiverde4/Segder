from socket import socket, AF_INET, SOCK_STREAM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
import hashlib
import os

# Clase para manejar conexiones a servidores
class Servidor:
    def __init__(self, ip, puerto):
        self.ip = ip
        self.puerto = puerto
        self.socket = socket(AF_INET, SOCK_STREAM)
    
    def conectar(self):
        # Realizar la conexion con la direccion y puerto del servidor proporcionado
        self.socket.connect((self.ip, self.puerto))
        print(f"Conectado a {self.ip}:{self.puerto}")
    
    # Enviar datos al servidor
    def enviar(self, mensaje):
        self.socket.send(mensaje.encode())
    
    # Recibir datos del servidor
    def recibir(self, buffer=2048):
        return self.socket.recv(buffer).decode()

# Clase para gestionar licencias
class GestorLicencias:
    def __init__(self, servidor_licencias):
        self.servidor_licencias = servidor_licencias
    
    @staticmethod
    def generar_claves():
        kpr = rsa.generate_private_key(65537, 2048)
        k_pub = kpr.public_key()
        private_number = kpr.private_numbers()
        public_numbers = k_pub.public_numbers()
        return private_number.d, [public_numbers.n, public_numbers.e]
    
    @staticmethod
    def firmado(mensaje, d, n):
        hash_m = int.from_bytes(hashlib.sha256(mensaje).digest(), byteorder="big")
        return pow(hash_m, d, n)
    
    def solicitar_licencia(self, archivo, clave_privada, clave_publica):
        firma = self.firmado(b"Firma digital del mensaje", clave_privada, clave_publica[0])
        mensaje_tx = f"{archivo}-{clave_publica}-{firma}"
        self.servidor_licencias.enviar(mensaje_tx)
        return self.recibir_licencia(clave_privada, clave_publica[0])
    
    def recibir_licencia(self, clave_privada, modulo_n):
        try:
            respuesta = self.servidor_licencias.recibir()
            if not respuesta:
                raise ValueError("No se recibió respuesta del servidor de licencias.")
            partes = respuesta.split()
            iv = partes[1].encode()
            k_cifrada = int(partes[3])
            iv_aes = int.to_bytes(int(partes[7]), 16, "big")
            k_rsa = int.to_bytes(pow(k_cifrada, clave_privada, modulo_n), 16, "big")
            aes_cipher = Cipher(algorithms.AES(k_rsa), modes.CTR(iv_aes))
            aes_decryptor = aes_cipher.decryptor()
            k_descifrada = aes_decryptor.update(int.to_bytes(k_cifrada, 16, "big"))
            return iv, k_descifrada
        except Exception as e:
            print(f"Error al recibir la licencia: {e}")
            return None, None

# Clase para gestionar contenidos
class GestorContenido:
    def __init__(self, servidor_contenido):
        self.servidor_contenido = servidor_contenido
    
    def descargar(self, archivo):
        self.servidor_contenido.enviar(f"DESCARGAR {archivo}")
        respuesta = self.servidor_contenido.recibir()
        if respuesta.startswith("200"):
            longitud = int(respuesta.split(":")[1].strip())
            with open(f"contenido_descargado/{archivo}", "wb") as f:
                bytes_descargados = 0
                while bytes_descargados < longitud:
                    datos = self.servidor_contenido.socket.recv(2048)
                    if not datos:
                        break
                    f.write(datos)
                    bytes_descargados += len(datos)
            print(f"{archivo} descargado.")
        else:
            print("Error: Archivo no encontrado.")

# Clase para interactuar con el usuario
class InterfazUsuario:
    def __init__(self, servidor_cdm):
        self.servidor_cdm = servidor_cdm
    
    def manejar_comandos(self):
        comandos = {
            "VER": "Lista contenidos disponibles",
            "DESCARGAR {archivo}": "Descarga un archivo",
            "FIN": "Finaliza la conexión",
        }
        while True:
            comando = input("Ingrese un comando: ").strip()
            if comando == "FIN":
                break
            elif comando.startswith("DESCARGAR"):
                archivo = comando.split(" ", 1)[1]
                self.servidor_cdm.enviar(comando)
                respuesta = self.servidor_cdm.recibir()
                print(respuesta)
            elif comando == "VER":
                self.servidor_cdm.enviar(comando)
                print(self.servidor_cdm.recibir())
            else:
                print("Comando no reconocido.")

# Punto de entrada principal
def main():
    # Crear objetos de servidor
    servidor_contenidos = Servidor("127.0.0.1", 6000)
    servidor_licencias = Servidor("127.0.0.1", 6001)    
    servidor_cdm = Servidor("127.0.0.1", 7000)

    # Conectar con Contenidos, Licencias y CDM
    servidor_contenidos.conectar()
    servidor_licencias.conectar()
    servidor_cdm.conectar()


    gestor_licencias = GestorLicencias(servidor_licencias)
    gestor_contenido = GestorContenido(servidor_contenidos)
    interfaz = InterfazUsuario(servidor_cdm)

    # interfaz.manejar_comandos()

if __name__ == "__main__":
    main()
