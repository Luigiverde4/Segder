"""
Servidor Contenidos
"""
from socket import *
import os
from datetime import datetime

def log(msj: str)-> None:
    """
    Printea y guarda un log con el tiempo y el mensaje a logear
    Args:
        msj (str): El mensaje a logear
    Returns:
        None
    """
    print(f"{datetime.now().strftime('%H:%M:%S')} - {msj}")

def ver()->None:
    """
    Mira y envia si hay contenidos
    Args:
        None
    Returns:
        None
    """
    archivos = os.listdir("contenido")
    if (len(archivos) != 0):
        # Si hay contenido
        archivos_str = "\n".join(archivos)
    else:
        archivos_str = "No hay contenido\n"
    s1.send(archivos_str.encode())

def get(mensaje_rx:str)->None:
    """
    Coge y manda un archivo
    Args:
        nombre (str): Nombre del archivo a mandar
    Returns:
        None
    """
    nombre = mensaje_rx.split()[1]
    print(f"Nombre : {nombre}")
    ruta = f"contenido/{nombre}" 

    with open(f"contenido/{nombre}", 'rb') as archivo:
        cont = archivo.read()
        long = os.stat(ruta).st_size  # Obtener solo el tamaño del archivo
        msg = "200 Longitud Contenido:" + str(long) + "\n"  # Convertir a cadena
        s1.send(msg.encode())
        s1.sendall(cont)


# Datos conexion
dir_IP_server = "127.0.0.1"
puerto_server = 6000
dir_socket_server = (dir_IP_server,puerto_server)

# Socket
s=socket(AF_INET,SOCK_STREAM)
s.bind(dir_socket_server)
s.listen()
s1, addr = s.accept()
log(f"Conexion aceptada a {addr[0]}")

# Variables
comandos = ["VER","DESCARGAR","FIN"] 

# Bucle infinito que corre el servidor
while True:
    try:
        # Recibir peticion
        mensaje_rx= s1.recv(2048).decode()
        log(f"Mensaje RX {mensaje_rx}")

        # Verificar comando
        if mensaje_rx.split()[0] not in [comando.split()[0] for comando in comandos]: # Si no se hace asi, descargar no va
            s1.send("Comando no reconocido".encode())
        
        # Manejar el comando
        else:
            # FIN del programa
            if mensaje_rx.startswith("FIN"):
                s.close()
                break

            # VER los contenidos disponibles
            elif mensaje_rx.startswith("VER"):
                ver()
            
            # DESCARGAR contenido pedido
            elif mensaje_rx.startswith("DESCARGAR"):
                get(mensaje_rx)
                #TODO Al encriptar, separar cabecera y cuerpo
                        
    except Exception as e:
        # Capturar errores especificos y enviar un mensaje de error
        log(f"Error en el servidor: {str(e)}")
        s1.send("ERROR EN EL SERVIDOR".encode())

    except FileNotFoundError:
        log(f"ERROR: Archivo no encontrado!")
        s1.send(b"ERROR: Archivo no encontrado") 
    # # Cerrar el socket
    # finally:
    #     if s1:
    #         s1.close()
    #     log(f"Servidor cerrado")