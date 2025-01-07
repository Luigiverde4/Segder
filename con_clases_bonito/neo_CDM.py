import socket

# Configuración de la conexión con la UA
HOST_UA = '127.0.0.1'  # Dirección de la UA
PUERTO_UA = 7000       # Puerto de la UA

class CDM:
    def __init__(self):
        self.socket_UA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.estado_usuarios = {}  # Diccionario para mantener estados de usuarios

    def conectar_UA(self):
        try:
            self.socket_UA.connect((HOST_UA, PUERTO_UA))
            print("Conectado a la UA.")
        except Exception as e:
            print(f"Error al conectar con la UA: {e}")
            return False
        return True

    def enviar_comando_a_UA(self, comando):
        """
        Envía un comando a la UA y espera una respuesta.
        """
        try:
            self.socket_UA.sendall(comando.encode())
            respuesta = self.socket_UA.recv(1024).decode()
            print(f"Respuesta de la UA: {respuesta}")
            return respuesta
        except Exception as e:
            print(f"Error al enviar comando a la UA: {e}")
            return None

    def procesar_solicitud_usuario(self, usuario, accion, parametros):
        """
        Procesa solicitudes de los usuarios y decide cómo interactuar con la UA.
        """
        if accion == "VER":
            comando = f"VER {usuario} {parametros['contenido']}"
            respuesta = self.enviar_comando_a_UA(comando)
            # Actualizar estado del usuario
            self.estado_usuarios[usuario] = f"Visualizando {parametros['contenido']}"
            return respuesta
        elif accion == "DESCARGAR":
            comando = f"DESCARGAR {usuario} {parametros['contenido']}"
            respuesta = self.enviar_comando_a_UA(comando)
            return respuesta
        else:
            print(f"Acción no reconocida: {accion}")
            return None

    def cerrar_conexion_UA(self):
        self.socket_UA.close()
        print("Conexión con la UA cerrada.")

# Ejemplo de uso
if __name__ == "__main__":
    cdm = CDM()
    if cdm.conectar_UA():
        usuario = "user123"
        accion = "VER"
        parametros = {"contenido": "pelicula.mp4"}
        respuesta = cdm.procesar_solicitud_usuario(usuario, accion, parametros)
        print(f"Resultado: {respuesta}")

        # Cerrar conexión al finalizar
        cdm.cerrar_conexion_UA()
