from socket import *
import os

def gestionaInputs(mensaje_tx:str) -> bool:
    """Gestiona el input del usuario y valida los comandos.
    Args:
        mensaje_tx (str): Mensaje del usuario a manejar
    Returns:
        bool: Si esperamos respuesta del servidor
    """
    if not mensaje_tx.strip():
        print("No has ingresado ningun comando, intenta otra vez.")
        return False

    if mensaje_tx.startswith("INFO"):
        print("\nComandos disponibles:")
        for instruccion in comandos:
            print(f"{instruccion.ljust(max_len)} - {comandos[instruccion]}")
        return False

    elif mensaje_tx.split()[0] not in [comando.split()[0] for comando in comandos]: 
        print("Comando erróneo")
        return False

    elif mensaje_tx.startswith("DESCARGAR"):
        partes = mensaje_tx.split()
        if len(partes) < 2:
            print("Error: Debes especificar el nombre del archivo despues de 'DESCARGAR'.")
            return False
        else:
            s.send(mensaje_tx.encode())
            return True

    elif mensaje_tx.startswith("FIN"):
        s.send(mensaje_tx.encode())
        s.close() 
        exit()

    elif mensaje_tx.startswith("CLS"):
        os.system("cls" if os.name == "nt" else "clear")
        print("Introduce INFO para obtener informacion sobre los comandos que puedes enviar")
        return False

    else:
        s.send(mensaje_tx.encode())
        return True

def ver(mensaje_rx: bytes) -> None:
    """Muestra por pantalla los contenidos disponibles del servidor.
    Args:
        mensaje_rx (bytes): Contenido recibido del servidor en bytes
    Returns:
        None
    """
    lista_contenidos = mensaje_rx.decode().split("\n")
    for contenido in lista_contenidos:
        print(contenido)

def descarga(mensaje_tx: str, mensaje_rx: bytes) -> None:
    """Funcion para descargar el archivo pedido al servidor.
    Args:
        mensaje_tx (str): Contenido pedido al servidor
        mensaje_rx (bytes): Mensaje del servidor con el codigo de estado y longitud si procede
    Returns:
        None
    """
    try:
        mensaje_decodificado = mensaje_rx.decode()

        if mensaje_decodificado.startswith("400"):
            print("Error: El archivo solicitado no existe en el servidor.")
            return

        if not mensaje_decodificado.startswith("200"):
            print("Error: El servidor no respondió con un mensaje válido para descarga.")
            return

        longitud = int(mensaje_decodificado.split(":")[1].strip())
        print(f"Tamaño del archivo a descargar: {longitud} bytes")

        with open(f"contenido_descargado/{mensaje_tx.split()[1]}", "wb") as archivo:
            bytes_descargados = 0
            while bytes_descargados < longitud:
                data = s.recv(2048)
                if not data:
                    print("Error: No se recibieron más datos, la descarga puede estar incompleta.")
                    break
                archivo.write(data)
                bytes_descargados += len(data)

            if bytes_descargados >= longitud:
                print("Descarga completa")
            else:
                print("Error: La descarga se interrumpió o fue incompleta.")
    except ValueError as e:
        print(f"Error al interpretar la longitud del contenido en la respuesta del servidor: {e}")
    except FileNotFoundError as e:
        print(f"Error al guardar el archivo descargado: {e}")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado durante la descarga: {e}")

def recibirRespuestas() -> None:
    """Funcion para tratar la respuesta del servidor."""
    try:
        mensaje_rx = s.recv(2048)
        if not mensaje_rx:
            print("Error: No se recibió respuesta del servidor.")
            return

        if mensaje_tx.startswith("VER"):
            ver(mensaje_rx)

        elif mensaje_tx.startswith("DESCARGAR"):
            descarga(mensaje_tx, mensaje_rx)

    except Exception as e:
        print(f"Ha ocurrido un error al recibir la respuesta del servidor: {e}")

# Datos de conexion
dir_IP_servidor = '127.0.0.1'
puerto_servidor = 6000
dir_socket_servidor = (dir_IP_servidor, puerto_servidor)

# Socket
s = socket(AF_INET, SOCK_STREAM)
s.connect(dir_socket_servidor)

# Variables globales
comandos = {
    "VER": "Sirve para obtener los contenidos disponibles en el servidor",
    "DESCARGAR {nombre del archivo}": "Envia una solicitud de descarga del fichero especificado al servidor",
    "FIN": "Cierra la aplicacion",
    "CLS": "Limpiar la consola"
}

max_len = max(len(comando) for comando in comandos)

print("Introduzca INFO para obtener informacion sobre los comandos que puedes enviar")

try:
    while True:
        mensaje_tx = input("\nIntroduzca su comando : ")
        if gestionaInputs(mensaje_tx):  # Si esperamos algo del servidor
            recibirRespuestas()
except KeyboardInterrupt as e:
    s.close()
    exit()