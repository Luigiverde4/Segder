from socket import *
import os
# Datos conexio
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
    mensaje_tx = input("\nIntroduzca su comando : ").upper()
    

    # Lidiar con el envio

    # Mostrar los comandos disponibles alineados
    if mensaje_tx == "INFO":
        print("\nComandos disponibles:")
        for instruccion in comandos:
            print(f"{instruccion.ljust(max_len)} - {comandos[instruccion]}")

    # Verificar el comando
    elif mensaje_tx.split()[0] not in [comando.split()[0] for comando in comandos]: 
        # Si el comando no existe, se avisa
        print("Comando erroneo")

    # Terminar el programa
    elif mensaje_tx == "FIN":
        s.send(mensaje_tx.encode())  # Enviar mensaje de cierre al servidor
        s.close() 
        break  

    # Limpiar la consola 
    elif mensaje_tx == "CLS":
        os.system("cls")
        print("Introduzca INFO para obtener información sobre los comandos que puedes enviar")

    # Enviar mensaje
    else:
        s.send(mensaje_tx.encode())  # Enviar
    

    # Lidiar con la respuesta
    mensaje_rx = s.recv(2048).decode()  # Recibir
    if mensaje_tx == "VER":
        # Creamos una lista partiendo cada \n y la printeamos
        lista_contenidos = mensaje_rx.split("\n")
        print(lista_contenidos)    
    elif mensaje_tx == "DESCARGAR":
        # TODO hacer que descargue y cree el archivo al descargarlo
        pass