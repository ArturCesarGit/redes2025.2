import socket
import base64
from cryptography.fernet import Fernet

HOST = "127.0.0.1" 
PORT = 7070
WINDOW_SIZE = 5
KEY = b'wA3xQc1V1L-i6pGs_8zNYRz1lO_pfg2f8a4fP9lJj0s='

cipher_suite = Fernet(KEY)

def calcular_checksum(dados: str) -> int:
    MOD = 2**32
    soma = 0
    for i, c in enumerate(dados):
        soma = (soma + (i + 1) * ord(c)) % MOD
    return soma

def processar_mensagens_GBN(conexao_cliente: socket.socket):
    print("[SERVER] Iniciando processamento com protocolo GBN...\n")
    mensagem_completa = ""
    num_sequencia_esperado = 0

    buffer_recebimento = ""
    DELIMITADOR = "|||"
    transmissao_concluida = False

    while not transmissao_concluida:
        dados_recebidos = conexao_cliente.recv(1024)
        if not dados_recebidos: break
        
        buffer_recebimento += dados_recebidos.decode('utf-8')

        while DELIMITADOR in buffer_recebimento:
            pacote_completo, buffer_recebimento = buffer_recebimento.split(DELIMITADOR, 1)

            if not pacote_completo: continue
            
            partes = pacote_completo.split('[.]')
            if len(partes) != 4: continue

            num_pacote = int(partes[0])
            checksum_recebido = int(partes[1])
            flag_fim = partes[2]
            carga_util_b64 = partes[3]

            print(f"> Pacote Nº {num_pacote} recebido:")
            print(f"  - Checksum Recebido: {checksum_recebido}")
            print(f"  - Flag de Fim: {flag_fim}")
            print(f"  - Carga Util Criptografada (Base64): '{carga_util_b64[:25]}...'")

            checksum_calculado = calcular_checksum(carga_util_b64 )

            if (num_pacote == num_sequencia_esperado) and (checksum_calculado == checksum_recebido):
                carga_util_encrypted = base64.b64decode(carga_util_b64.encode('utf-8'))
                carga_util_decrypted_bytes = cipher_suite.decrypt(carga_util_encrypted)
                carga_util = carga_util_decrypted_bytes.decode('utf-8')

                mensagem_completa += carga_util
                print(f"\n[SERVER] Pacote {num_pacote} OK.")

                num_sequencia_esperado += 1

                ack_cumulativo = num_sequencia_esperado - 1
                print(f"[SERVER] Enviando ACK cumulativo -> ACK_{ack_cumulativo}\n")
                conexao_cliente.sendall(f"ACK_{ack_cumulativo}".encode('utf-8'))
                
                if flag_fim == '1':
                    print("[SERVER] Flag de fim recebida. Transmissão concluída.")
                    transmissao_concluida = True
                    break
            
            else:
                if checksum_calculado != checksum_recebido:
                    print(f"\n[SERVER] ERRO: Checksum inválido para o pacote {num_pacote}. Esperado: ({checksum_calculado}), Recebido: ({checksum_recebido})")
                else:
                    print(f"\n[SERVER] ERRO: Pacote fora de ordem. Esperado: ({num_sequencia_esperado}), Recebido: ({num_pacote})")

                ack_anterior = num_sequencia_esperado - 1
                if ack_anterior >= 0:
                    print(f"[SERVER] Descartando pacote {num_pacote} e reenviando ACK_{ack_anterior}.\n")
                    conexao_cliente.sendall(f"ACK_{ack_anterior}".encode('utf-8'))
                else:
                    print(f"[SERVER] Descartando pacote {num_pacote}.\n")
    
    print(f"\n[SERVER] MENSAGEM COMPLETA (GBN): {mensagem_completa}")

def processar_mensagens_SR(conexao_cliente: socket.socket):
    print("[SERVER] Iniciando processamento com protocolo SR...\n")
    mensagem_completa = ""
    WINDOW_SIZE_SR = 5
    rcv_base = 0
    pacotes_em_buffer = {}

    buffer_recebimento = ""
    DELIMITADOR = "|||"
    transmissao_concluida = False

    while not transmissao_concluida:
        dados_recebidos = conexao_cliente.recv(1024)
        if not dados_recebidos: break
        
        buffer_recebimento += dados_recebidos.decode('utf-8')

        while DELIMITADOR in buffer_recebimento:
            pacote_completo, buffer_recebimento = buffer_recebimento.split(DELIMITADOR, 1)

            if not pacote_completo: continue

            partes = pacote_completo.split('[.]')
            if len(partes) != 4: continue

            num_pacote = int(partes[0])
            checksum_recebido = int(partes[1])
            flag_fim = partes[2]
            carga_util_b64 = partes[3]

            print(f"> Pacote Nº {num_pacote} recebido:")
            print(f"  - Checksum Recebido: {checksum_recebido}")
            print(f"  - Flag de Fim: {flag_fim}")
            print(f"  - Carga Util Criptografada (Base64): '{carga_util_b64[:25]}...'")

            checksum_calculado = calcular_checksum(carga_util_b64)

            if checksum_calculado != checksum_recebido:
                print(f"\n[SERVER] ERRO: Checksum inválido para o pacote {num_pacote}. Pacote descartado.\n")
                continue

            carga_util_encrypted = base64.b64decode(carga_util_b64.encode('utf-8'))
            carga_util_decrypted_bytes = cipher_suite.decrypt(carga_util_encrypted)
            carga_util = carga_util_decrypted_bytes.decode('utf-8')
            
            if rcv_base - WINDOW_SIZE_SR <= num_pacote < rcv_base + WINDOW_SIZE_SR:
                print(f"\n[SERVER] Pacote {num_pacote} OK.")
                print(f"  > Carga Útil Descriptografada: '{carga_util}'")
                print(f"  > [SERVER] Enviando ACK_{num_pacote}.\n")
                conexao_cliente.sendall(f"ACK_{num_pacote}".encode('utf-8'))

            if rcv_base <= num_pacote < rcv_base + WINDOW_SIZE_SR:
                if num_pacote not in pacotes_em_buffer:
                    pacotes_em_buffer[num_pacote] = (carga_util, flag_fim == '1')
                    print(f"\n[SERVER] Pacote {num_pacote} armazenado no buffer.")

            while rcv_base in pacotes_em_buffer:
                dados, eh_ultimo = pacotes_em_buffer.pop(rcv_base)
                mensagem_completa += dados
                print(f"[SERVER] Pacote {rcv_base} entregue à aplicação. Janela avança.\n")
                rcv_base += 1
                
                if eh_ultimo:
                    print("[SERVER] Flag de fim recebida. Transmissão concluída.")
                    transmissao_concluida = True
                    break 
            
            if transmissao_concluida:
                break

    print(f"\n[SERVER] MENSAGEM COMPLETA (SR): {mensagem_completa}")

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
        elif protocolo_operacao == "SR":
            processar_mensagens_SR(conexao_cliente)
        
    finally:
        if conexao_cliente:
            conexao_cliente.close()
            print("\n[SERVER] Conexão fechada")

if __name__ == "__main__":
    iniciar_servidor()