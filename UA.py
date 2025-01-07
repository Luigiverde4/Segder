import os
from socket import AF_INET, SOCK_STREAM, socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# SOCKETS
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

# CDM
dir_IP_CDM = '127.0.0.1'    
puerto_CDM = 7000           
s_cdm = socket(AF_INET, SOCK_STREAM)
dir_socket_UA = (dir_IP_CDM, puerto_CDM)
s_cdm.bind(dir_socket_UA)
s_cdm.listen(5)

comandos = {
    "VER": "Lista los contenidos disponibles en el servidor de contenidos",
    "DESCARGAR {nombre del archivo}": "Solicita la descarga de un archivo al servidor de contenidos",
    "FIN": "Cierra la aplicación",
    "CLS": "Limpia la consola",
}

max_len = max(len(comando) for comando in comandos)

# CONTENIDO
def ver(mensaje_rx:(str))->None:
    """
    Muestra los contenidos disponibles en el servidor.

    mensaje_rx (str): Respuesta de la UA con los contenidos disponibles.
    """
    print("\nContenidos disponibles:")
    for contenido in mensaje_rx.split("\n"):
        print(contenido)

    # Descargar contenido

def descargar(mensaje_cdm: str):
    """
    Descarga el contenido solicitado del servidor de contenidos.

    Args:
        mensaje_cdm (str): Comando a mandar al servidor de contenidos
    """
    partes = mensaje_cdm.split()

    # Verificamos si se ha proporcionado el nombre del archivo
    if len(partes) < 2:
        print("ERROR: Falta el nombre del archivo.")
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
                print("DESCARGA COMPLETA")
            else:
                print("ERROR: Descarga incompleta.")

        # Desencriptamos el archivo ( si es necesario )
        decrypt(nombre_archivo)
    else:
        print("ERROR: Archivo no encontrado en el servidor.")

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
        
        print("El archivo esta encriptado")

        # Pedir al CDM una mensaje de licencia para desencriptarlo
        mensajeArchivoParaLicencia = f"LICENCIA {nombre_archivo}"
        scdm.send(mensajeArchivoParaLicencia.encode())
        # Recibir del CDM el mensaje de licencia
        mensajePedirLicencias = scdm.recv(2048)
        print("Mensaje Pedir Licencias recibido del CDM")
        sl.send(mensajePedirLicencias)
        print("Mensaje Pedir Licencias enviado al SL")
        licencia = sl.recv(2048)
        print("Licencia recibida del SL")
        scdm.send(licencia)

        status = scdm.recv(2048).decode()
        print(status)
    except Exception as e:
        print(f"Error al desencriptar el archivo {nombre_archivo}: {e}")

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

# INTERFAZ USUARIO
def gestionar_comandos()->None:
    """
    Gestiona la entrada del usuario y envía comandos a la UA.
    """
    print("\nIntroduce INFO para obtener información sobre los comandos disponibles.")

    try:
        if not mensaje_tx.strip():
            print("Comando vacío. Intenta nuevamente.")
            return

        # COMANDOS DE LA CONSOLA
        elif mensaje_tx.upper() == "INFO":
            print("\nComandos disponibles:")
            for instruccion in comandos:
                print(f"{instruccion.ljust(max_len)} - {comandos[instruccion]}")
            return

        # Limpiar la consola
        elif mensaje_tx.upper() == "CLS":
            os.system("cls" if os.name == "nt" else "clear")
            return 

        # Finalizar el programa
        elif mensaje_tx.upper() == "FIN":
            print("Cerrando conexión con la UA y finalizando el programa...")
            sc.close()
            sl.close()
            scdm.close
            return

        else:
            # COMANDOS DE LOS SERVIDORES
            # Contenidos
            if (mensaje_tx.startswith("VER")):
                # Mandamos el comando "VER"
                sc.send(mensaje_tx.encode())  
                respuesta = sc.recv(2048).decode()
                ver(respuesta)

            elif (mensaje_tx.startswith("DESCARGAR")):
                # Descargar contenidos del ServCont
                descargar(mensaje_tx)
            
            else:
                print("Comando no identificado por Interfaz ni Servidores")

    except KeyboardInterrupt:
        print("\nInterrupción manual detectada. Cerrando conexión...")
        sl.close()
        sc.close()
        scdm.close()
    except Exception as e:
        print(f"Error inesperado: {e}")



scdm, addr = s_cdm.accept()
print("Conexion con el CDM!") 
# Iniciar la gestion de comandos
if __name__ == "__main__":
    while True:
        mensaje_tx = input("\nIntroduce tu comando: ")
        gestionar_comandos()