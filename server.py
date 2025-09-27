import socket

HOST = "127.0.0.1" 
PORT = 7070
WINDOW_SIZE = 5

def calcular_checksum(dados: str):
    return sum(ord(c) for c in dados)

def processar_mensagens_GBN(conexao_cliente: socket.socket):
    print("[SERVER] Iniciando processamento com protocolo GBN...\n")
    mensagem_completa = ""
    num_sequencia_esperado = 0
    
    while True:
        pacote_recebido = conexao_cliente.recv(1024)
        if not pacote_recebido:
            print("[SERVER] Cliente desconectado.")
            break

        partes = pacote_recebido.decode('utf-8').split('[.]')
        num_pacote = int(partes[0])
        checksum_recebido = int(partes[1])
        flag_fim = partes[2]
        carga_util = partes[3]

        print(f"> Pacote Nº {num_pacote} recebido:")
        print(f"  - Checksum Recebido: {checksum_recebido}")
        print(f"  - Flag de Fim: {flag_fim}")
        print(f"  - Carga Util: '{carga_util}'")

        checksum_calculado = calcular_checksum(carga_util)

        if (num_pacote == num_sequencia_esperado) and (checksum_calculado == checksum_recebido):
            print(f"\n[SERVER] Pacote {num_pacote} OK. Enviando ACK_{num_pacote}.\n")
            mensagem_completa += carga_util
            conexao_cliente.sendall(f"ACK_{num_pacote}".encode('utf-8'))
            num_sequencia_esperado += 1
            
            if flag_fim == '1':
                print("[SERVER] Flag de fim recebida. Transmissão concluída.")
                break
        
        else:
            if checksum_calculado != checksum_recebido:
                print(f"[SERVER] ERRO: Checksum inválido para o pacote {num_pacote}. Esperado: {checksum_calculado}, Recebido: {checksum_recebido}.")
            else:
                print(f"[SERVER] ERRO: Pacote fora de ordem. Esperado: {num_sequencia_esperado}, Recebido: {num_pacote}.")

            ack_anterior = num_sequencia_esperado - 1
            if ack_anterior >= 0:
                print(f"[SERVER] Descartando pacote {num_pacote} e reenviando ACK_{ack_anterior}.")
                conexao_cliente.sendall(f"ACK_{ack_anterior}".encode('utf-8'))
            else:
                print(f"[SERVER] Descartando pacote {num_pacote}.")
    
    print(f"\n[SERVER] MENSAGEM COMPLETA (GBN): {mensagem_completa}")

def iniciar_servidor():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conexao_cliente = None

    servidor_socket.bind((HOST, PORT))
    servidor_socket.listen()
    print(f"[SERVER] Aguardando conexão em {HOST}:{PORT}")

    conexao_cliente, endereco_cliente = servidor_socket.accept()
    print(f"[SERVER] Cliente conectado pelo endereço: {endereco_cliente}")

    try:
        handshake_recebido = conexao_cliente.recv(1024)

        handshake_string = handshake_recebido.decode('utf-8')
        partes = handshake_string.split('[.]')
        
        protocolo_operacao = partes[0]
        tamanho_pacotes = int(partes[1])
        tamanho_mensagem = int(partes[2])
        
        print("\n" + "="*50)
        print("HANDSHAKE RECEBIDO".center(50))
        print("="*50)
        print(f"  - Modo de Operacao: {protocolo_operacao}")
        print(f"  - Tamanho Maximo dos Pacotes: {tamanho_pacotes}")
        print(f"  - Tamanho Total da Mensagem: {tamanho_mensagem}")
        print("="*50 + "\n")

        handshake_response = f"HANDSHAKE_OK[.]WINDOW_SIZE={WINDOW_SIZE}".encode('utf-8')
        conexao_cliente.sendall(handshake_response)

        if protocolo_operacao == "GBN":
            processar_mensagens_GBN(conexao_cliente)
        #elif protocolo_operacao == "SR":
        #   processar_mensagens_SR(conexao_cliente)

    except Exception as e:
        print(f"Erro: {e}")
        
    finally:
        if conexao_cliente:
            conexao_cliente.close()
            print("\n[SERVER] Conexão fechada")

if __name__ == "__main__":
    iniciar_servidor()