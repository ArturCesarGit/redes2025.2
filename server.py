import socket

HOST = "127.0.0.1" 
PORT = 7070

def iniciar_servidor():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conexao_cliente = None

    servidor_socket.bind((HOST, PORT))
    servidor_socket.listen()
    print(f"[SERVER] Aguardando conexão em {HOST}:{PORT}")

    try:
        conexao_cliente, endereco_cliente = servidor_socket.accept()
        print(f"[SERVER] Cliente conectado pelo endereço: {endereco_cliente}")
        
        handshake_recebido = conexao_cliente.recv(1024)
        handshake_string = handshake_recebido.decode('utf-8')
        partes = handshake_string.split('[.]')
        
        modo_operacao = partes[0]
        tamanho_maximo = int(partes[1])
        
        print("\nHandshake Recebido!")
        print(f"Modo de Operação: {modo_operacao}")
        print(f"Tamanho Máximo do texto: {tamanho_maximo}")
        
        conexao_cliente.sendall(b'HANDSHAKE_OK')

        print("\n[SERVER] Aguardando recebimento de pacotes...")
        mensagem_completa = ""
        
        while True:
            pacote_recebido = conexao_cliente.recv(1024)
            pacote_string = pacote_recebido.decode('utf-8')
            
            num_pacote, flag_fim, carga_util = pacote_string.split('[.]', 2)

            print(f"\n[SERVER] Pacote recebido:")
            print(f"Número do Pacote: {num_pacote}")
            print(f"Flag Fim: {flag_fim}")
            print(f"Carga Útil: '{carga_util}'")
            
            mensagem_completa += carga_util
            
            ack_message = f"ACK_PACOTE_{num_pacote}".encode('utf-8')
            conexao_cliente.sendall(ack_message)
            
            if flag_fim == '1':
                break
        
        print(f"\n[SERVER] MENSAGEM COMPLETA RECEBIDA: {mensagem_completa}")

    except Exception as e:
        print(f"Erro: {e}")
        
    finally:
        if conexao_cliente:
            conexao_cliente.close()
            print("\n[SERVER] Conexão fechada")

if __name__ == "__main__":
    iniciar_servidor()