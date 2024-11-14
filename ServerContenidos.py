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

# Bucle infinito que corre el servidor
while True:
    # Recibir peticion
    mensaje_rx= s1.recv(2048)
    log(f"Mensaje RX {mensaje_rx}")
    if (mensaje_rx.decode() == "FIN"):
        s.close()
        break
    #s1[0].send(mensaje_rx)

log(f"Servidor cerrado")