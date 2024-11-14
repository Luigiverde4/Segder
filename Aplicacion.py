from socket import *
import os

def descarga(mensaje_tx: str)->None:
    long = int(mensaje_rx[23:])
    if mensaje_rx.decode().startswith("200"):
        print("--------> Fichero recibido")
        with open(f"contenido_descargado/{mensaje_tx.split()[1]}", "wb") as archivo:
            cont_down = 0
            while cont_down < long:
                data = s.recv(2048)
                cont_down += len(data)
                archivo.write(data)
    else:
        print("Respuesta:", mensaje_rx)
        print("--------> Fichero no encontrado")

def ver():
    # Creamos una lista partiendo cada \n
    lista_contenidos = mensaje_rx.decode().split("\n")
    print(lista_contenidos)  

# Datos conexion
dir_IP_servidor= '127.0.0.1'
puerto_servidor = 6000
dir_socket_servidor =(dir_IP_servidor, puerto_servidor)

# Socket
s = socket(AF_INET, SOCK_STREAM)
s.connect(dir_socket_servidor)

# Variables globales
comandos = {
    "VER": "Sirve para obtener los contenidos disponibles en el servidor",
    "DESCARGAR {nombre del archivo}": "Envía una solicitud de descarga del fichero especificado al servidor",
    "VER": "Ver los contenidos disponibles",
    "FIN": "Cierra la aplicación",
    "CLS": "Limpiar la consola"
}

max_len = max(len(comando) for comando in comandos) # Esto es para el formateo mas tarde

print("Introduzca INFO para obtener información sobre los comandos que puedes enviar")

while True:
    mensaje_tx = input("\nIntroduzca su comando : ")

    # Lidiar con el envio
    # Mostrar los comandos disponibles alineados
    if mensaje_tx.startswith("INFO"):
        print("\nComandos disponibles:")
        for instruccion in comandos:
            print(f"{instruccion.ljust(max_len)} - {comandos[instruccion]}")

    # Verificar el comando
    elif mensaje_tx.split()[0] not in [comando.split()[0] for comando in comandos]: 
        # Si el comando no existe, se avisa
        print("Comando erroneo")
        continue

    # Terminar el programa
    elif mensaje_tx.startswith("FIN"):
        s.send(mensaje_tx.encode())  # Enviar mensaje de cierre al servidor
        s.close() 
        continue  

    # Limpiar la consola 
    elif mensaje_tx.startswith("CLS"):
        os.system("cls")
        print("Introduzca INFO para obtener información sobre los comandos que puedes enviar")
        continue

    # Enviar mensaje
    else:
        s.send(mensaje_tx.encode())  # Enviar
    

    # Lidiar con la respuesta
    mensaje_rx = s.recv(2048)  # Recibir
    if mensaje_tx.startswith("VER"):
        ver()

    elif mensaje_tx.startswith("DESCARGAR"):
        descarga(mensaje_tx)
