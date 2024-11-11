from socket import *
dir_IP_servidor= '127.0.0.1'
puerto_servidor = 6000
dir_socket_servidor =(dir_IP_servidor, puerto_servidor)

s = socket(AF_INET, SOCK_STREAM)
s.connect(dir_socket_servidor)
print("Introduzca INFO para obtener información sobre los comandos que puedes enviar")
while True:
    mensaje_tx = input("Introduzca su mensaje : ")
    if(mensaje_tx == "INFO"):
        print("Comandos disponibles:")
        print("VER - Sirve para obtener los contenidos disponibles en el servidor")
        print("DESCARGAR {nombre del archivo} - Envia una solicitud de descarga del fichero especificado al servidor")
        print("VER - Sirve para obtener los contenidos disponibles en el servidor")
        print("FIN - Cierra la aplicación")
    elif(mensaje_tx == "FIN"):
        s.send(mensaje_tx.encode())
        s.close()
        break
    else:
        s.send(mensaje_tx.encode())
        mensaje_rx = s.recv(2048)
        print(mensaje_rx.decode())



