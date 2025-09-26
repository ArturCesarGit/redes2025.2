import socket

HOST = "127.0.0.1"
PORT = 7070
TAMANHO_MAX_PACOTE = 4

def enviar_pacotes(socket: socket, mensagem: str):
    pacotes = []
    for i in range(0, len(mensagem), TAMANHO_MAX_PACOTE):
        pacotes.append(mensagem[i:i+TAMANHO_MAX_PACOTE])

    total_pacotes = len(pacotes)
    print(f"\n> [CLIENT] Preparando envio de {total_pacotes} pacotes...")

    for num_pacote, carga_util in enumerate(pacotes):
        flag_fim = '1' if (num_pacote == total_pacotes - 1) else '0'
        pacote_formatado = f"{num_pacote}[.]{flag_fim}[.]{carga_util}".encode('utf-8')

        socket.sendall(pacote_formatado)
        print(f"> Pacote Nº {num_pacote} enviado:")
        print(f"   - Flag de Fim: {flag_fim}")
        print(f"   - Carga Útil: '{carga_util}'")

        ack_recebido = socket.recv(1024)
        print(f"[SERVER] Mensagem: {ack_recebido.decode('utf-8')}\n")
    
    print(f"\n[CLIENT] Transmissão concluída. Todos os pacotes foram enviados e confirmados.\n")

def iniciar_cliente():
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente_socket.connect((HOST, PORT))
        print(f"[CLIENT] Conectado com sucesso ao servidor em {HOST}:{PORT}\n")

        while True:
            protocolo_operacao = input("[CLIENT] Digite o protocolo (GBN ou RS): ").upper()
            if protocolo_operacao in ["GBN", "RS"]:
                break

        while True:
            tamanho_maximo_mensagem = int(input("[CLIENT] Digite o tamanho máximo do texto (min. 30): "))
            if tamanho_maximo_mensagem >= 30:
                break

        handshake_message = f"{protocolo_operacao}[.]{TAMANHO_MAX_PACOTE}[.]{str(tamanho_maximo_mensagem)}".encode('utf-8')
        
        cliente_socket.sendall(handshake_message)
        print("\n[CLIENT] Dados do handshake enviados ao servidor")
        
        confirmacao = cliente_socket.recv(1024)
        print(f"[SERVER] Resposta do Servidor: {confirmacao.decode('utf-8')}")

        while True:
            mensagem_original = input(f"\n[CLIENT] Digite a mensagem a ser enviada (limite de {tamanho_maximo_mensagem} caracteres): ")
            if len(mensagem_original) <= tamanho_maximo_mensagem:
                break 

        enviar_pacotes(cliente_socket, mensagem_original)

    except ConnectionRefusedError:
        print("[CLIENT] Não foi possível conectar")

    except Exception as e:
        print(f"\nErro: {e}")
        
    finally:
        cliente_socket.close()
        print("\n[CLIENT] Conexão fechada")

if __name__ == "__main__":
    iniciar_cliente()