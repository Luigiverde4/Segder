"""
Servidor Contenidos
"""
from socket import *

dir_IP_server = "127.0.0.1"
puerto_server = 6000
dir_socket_server = (dir_IP_server,puerto_server)

s=socket(AF_INET,SOCK_STREAM)

s.bind(dir_socket_server)
s.listen()
s1 = s.accept()
while True:
    mensaje_rx= s1[0].recv(2048)
    print(mensaje_rx)
    if (mensaje_rx.decode() == "FIN"):
        s.close()
        break
    #s1[0].send(mensaje_rx)

