import socket

HOST = "127.0.0.1" 
PORT = 7070

def exibir_handshake(msn: bytes):
    handshake_string = msn.decode('utf-8')
    partes = handshake_string.split('[.]')
    
    modo_operacao = partes[0]
    tamanho_pacotes = int(partes[1])
    tamanho_mensagem = int(partes[2])
    
    print("\n" + "="*50)
    print("HANDSHAKE RECEBIDO".center(50))
    print("="*50)
    print(f"  - Modo de Operacao: {modo_operacao}")
    print(f"  - Tamanho Maximo dos Pacotes: {tamanho_pacotes}")
    print(f"  - Tamanho Total da Mensagem: {tamanho_mensagem}")
    print("="*50 + "\n")

def exibir_metadados_pacote(pacote: bytes):
    pacote_string = pacote.decode('utf-8')
    partes = pacote_string.split('[.]')

    num_pacote = int(partes[0])
    flag_fim = int(partes[1])
    carga_util = partes[2]

    print(f"> Pacote Nº {num_pacote} recebido:")
    print(f"  - Flag de Fim: {flag_fim}")
    print(f"  - Carga Util: '{carga_util}'\n")

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
        exibir_handshake(handshake_recebido)
        conexao_cliente.sendall(b'HANDSHAKE_OK')

        print("[SERVER] Aguardando recebimento de pacotes...")
        mensagem_completa = ""
        
        while True:
            pacote_recebido = conexao_cliente.recv(1024)
            exibir_metadados_pacote(pacote_recebido)

            num_pacote, flag_fim, carga_util = pacote_recebido.decode('utf-8').split('[.]')

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