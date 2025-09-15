import socket
import json


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000


DEFAULT_WINDOW_SIZE = 5
DEFAULT_MAX_MESSAGE_SIZE = 30
DEFAULT_MODE = "GBN"  

def start_server():
   
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)

    print(f"[SERVER] Servidor escutando em {SERVER_HOST}:{SERVER_PORT}...")

   
    conn, addr = server_socket.accept()
    print(f"[SERVER] Cliente conectado: {addr}")

    
    handshake_data = conn.recv(1024)
    handshake = json.loads(handshake_data.decode())
    print(f"[SERVER] Handshake recebido: {handshake}")

    
    server_handshake = {
        "type": "handshake_ack",
        "mode": DEFAULT_MODE,
        "window_size": DEFAULT_WINDOW_SIZE,
        "max_message_size": DEFAULT_MAX_MESSAGE_SIZE
    }

    conn.sendall(json.dumps(server_handshake).encode())
    print("[SERVER] Handshake confirmado. Conexão estabelecida.")

    conn.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()
