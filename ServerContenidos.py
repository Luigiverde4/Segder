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

try:
    # Bucle infinito que corre el servidor
    while True:
        # Recibir peticion
        mensaje_rx= s1.recv(2048)
        log(f"Mensaje RX {mensaje_rx.decode()}")

        # Verificar comando
        if mensaje_rx.split()[0] not in [comando.split()[0] for comando in comandos]: # Si no se hace asi, descargar no va
            s1.send("Comando no reconocido".encode())
        
        # Terminar el programa
        elif (mensaje_rx.decode() == "FIN"):# Fin de la comunicacion con el cliente
            s.close()
            break
        
        # Manejar el comando
        else:
            s1.send("Comando recibido".encode())

except Exception as e:
    # Capturar errores específicos y enviar un mensaje de error
    log(f"Error en el servidor: {str(e)}")
    s1.send("ERROR EN EL SERVIDOR".encode())

# Cerrar el socket
finally:
    if s1:
        s1.close()
    log(f"Servidor cerrado")