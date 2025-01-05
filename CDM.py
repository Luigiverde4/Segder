from socket import socket, AF_INET, SOCK_STREAM
import os

# SOCKET CON LA UA
dir_IP_UA = '127.0.0.1'  # Dirección IP de la UA
puerto_UA = 7000         # Puerto de la UA

# Crear el socket
sua = socket(AF_INET, SOCK_STREAM)

# Conectar al servidor de la UA
dir_socket_UA = (dir_IP_UA, puerto_UA)
sua.connect(dir_socket_UA)

# Comandos disponibles
comandos = {
    "VER": "Lista los contenidos disponibles en el servidor de contenidos",
    "DESCARGAR {nombre del archivo}": "Solicita la descarga de un archivo al servidor de contenidos",
    "FIN": "Cierra la aplicación",
    "CLS": "Limpia la consola",
}

max_len = max(len(comando) for comando in comandos)

def interactuar_con_UA(mensaje_tx:str)->None:
    """
    Manda comandos a la UA y procesa las respuestas recibidas.

    mensaje_tx (str): Comando que se manda a la UA.
    """
    try:
        # Enviar el comando a la UA
        sua.send(mensaje_tx.encode())

        # Esperar y recibir respuesta de la UA
        mensaje_rx = sua.recv(4096).decode()

        if not mensaje_rx:
            print("Error: No se recibió respuesta de la UA.")
            return

        # Procesar respuestas específicas
        if mensaje_tx.startswith("VER"):
            ver(mensaje_rx)
        elif mensaje_tx.startswith("DESCARGAR"):
            procesar_descarga(mensaje_tx, mensaje_rx)
        else:
            print(mensaje_rx)

    except Exception as e:
        print(f"Error al interactuar con la UA: {e}")

def ver(mensaje_rx:(str))->None:
    """
    Muestra los contenidos disponibles en el servidor.

    mensaje_rx (str): Respuesta de la UA con los contenidos disponibles.
    """
    print("\nContenidos disponibles:")
    for contenido in mensaje_rx.split("\n"):
        print(contenido)

def procesar_descarga(mensaje_tx, mensaje_rx):
    """
    Procesa la descarga de un archivo solicitada a la UA.

    Args:
        mensaje_tx (str): Comando enviado a la UA para descargar un archivo.
        mensaje_rx (str): Respuesta de la UA sobre el estado de la descarga.
    Returns:
        None
    """
    if mensaje_rx.startswith("200"):
        print("Descarga completada y archivo procesado correctamente.")
    elif mensaje_rx.startswith("400"):
        print("Error: El archivo solicitado no existe en el servidor.")
    elif mensaje_rx.startswith("204"):
        print(mensaje_rx)
    else:
        print(f"Error desconocido: {mensaje_rx}")

def gestionar_comandos():
    """
    Gestiona la entrada del usuario y envía comandos a la UA.

    Returns:
        None
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
            sua.sendall("FIN".encode())
            sua.close()
            return

        else:
            # COMANDOS DE LOS SERVIDORES
            interactuar_con_UA(mensaje_tx)

    except KeyboardInterrupt:
        print("\nInterrupción manual detectada. Cerrando conexión...")
        sua.close()
    except Exception as e:
        print(f"Error inesperado: {e}")

# Iniciar la gestión de comandos
if __name__ == "__main__":
    while True:
        mensaje_tx = input("\nIntroduce tu comando: ")
        gestionar_comandos()
