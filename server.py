import socket

HOST = "127.0.0.1" 
PORT = 7070

def iniciar_servidor():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conexao_cliente = None

    servidor_socket.bind((HOST, PORT))
    servidor_socket.listen()
    print(f"Servidor aguardando conexão em {HOST}:{PORT}")

    try:
        conexao_cliente, endereco_cliente = servidor_socket.accept()
        print(f"Cliente conectado pelo endereço: {endereco_cliente}")
        
        dados_recebidos = conexao_cliente.recv(1024)        
        handshake_string = dados_recebidos.decode('utf-8')
        partes = handshake_string.split('[.]')
        
        modo_operacao = partes[0]
        tamanho_maximo = int(partes[1])
        
        print("\nHandshake Recebido!")
        print(f"Modo de Operação: {modo_operacao}")
        print(f"Tamanho Máximo do texto: {tamanho_maximo}\n")
        
        conexao_cliente.sendall(b'Handshake ok!')

    except Exception as e:
        print(f"erro: {e}")
        
    finally:
        if conexao_cliente:
            conexao_cliente.close()
            print("Conexão com o cliente fechada.")
            
        servidor_socket.close()
        print("Socket do servidor fechado.")

if __name__ == "__main__":
    iniciar_servidor()