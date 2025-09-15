import socket
import json


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000


DEFAULT_WINDOW_SIZE = 5
DEFAULT_MAX_MESSAGE_SIZE = 30
DEFAULT_MODE = "GBN"

def start_client():

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(f"[CLIENT] Conectado ao servidor {SERVER_HOST}:{SERVER_PORT}")

    handshake = {
        "type": "handshake",
        "mode": DEFAULT_MODE,
        "window_size": DEFAULT_WINDOW_SIZE,
        "max_message_size": DEFAULT_MAX_MESSAGE_SIZE
    }

    client_socket.sendall(json.dumps(handshake).encode())
    print(f"[CLIENT] Handshake enviado: {handshake}")


    response_data = client_socket.recv(1024)
    response = json.loads(response_data.decode())
    print(f"[CLIENT] Confirmação recebida: {response}")

    client_socket.close()

if __name__ == "__main__":
    start_client()
