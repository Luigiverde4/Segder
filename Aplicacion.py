from socket import *

# Datos conexio
dir_IP_servidor= '127.0.0.1'
puerto_servidor = 6000
dir_socket_servidor =(dir_IP_servidor, puerto_servidor)

# Socket
s = socket(AF_INET, SOCK_STREAM)
s.connect(dir_socket_servidor)

# Variables globales
instrucciones = {
    "VER": "Sirve para obtener los contenidos disponibles en el servidor",
    "DESCARGAR {nombre del archivo}": "Envía una solicitud de descarga del fichero especificado al servidor",
    "FIN": "Cierra la aplicación"
}
max_len = max(len(comando) for comando in instrucciones) # Esto es para el formateo mas tarde


print("Introduzca INFO para obtener información sobre los comandos que puedes enviar")

while True:
    mensaje_tx = input("\nIntroduzca su comando : ").upper()
    if(mensaje_tx == "INFO"):
        # Mostrar comandos con formato alineado
        print("\nComandos disponibles:")
        for instruccion in instrucciones:
            print(f"{instruccion.ljust(max_len)} - {instrucciones[instruccion]}")
    elif(mensaje_tx == "FIN"):
        # Cerrar socket
        s.send(mensaje_tx.encode())
        s.close()
        break # return si cambiamos a funcion a futuro
    elif (mensaje_tx not in instrucciones):
        print("Comando erroneo")
    else:
        # Enviar y Recibir mensajes
        s.send(mensaje_tx.encode())
        mensaje_rx = s.recv(2048)
        print(mensaje_rx.decode())