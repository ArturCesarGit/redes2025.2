import socket

HOST = "127.0.0.1"
PORT = 7070
TAMANHO_MAX_PACOTE = 4

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

        mensagem_original = input(f"\n[CLIENT] Digite a mensagem a ser enviada (limite de {tamanho_maximo_mensagem} caracteres): ")

        if len(mensagem_original) > tamanho_maximo_mensagem:
            print(f"\n[CLIENT] ERRO: A mensagem possui {len(mensagem_original)} caracteres, excedendo o limite de {tamanho_maximo_mensagem} caracteres definido.")
            return 

        pacotes_a_enviar = []
        for i in range(0, len(mensagem_original), TAMANHO_MAX_PACOTE):
            pacotes_a_enviar.append(mensagem_original[i:i+TAMANHO_MAX_PACOTE])

        total_pacotes = len(pacotes_a_enviar)
        print(f"\n[CLIENT] Mensagem será dividida em {total_pacotes} pacotes.")

        for i, pacote_payload in enumerate(pacotes_a_enviar):
            
            flag_fim = '1' if (i == total_pacotes - 1) else '0'
            pacote_formatado = f"{i}[.]{flag_fim}[.]{pacote_payload}".encode('utf-8')
            
            cliente_socket.sendall(pacote_formatado)
            print(f"\n[CLIENT] Pacote {i} enviado -> Payload: '{pacote_payload}'")

            ack_recebido = cliente_socket.recv(1024)
            print(f"[SERVER] Confirmação recebida: {ack_recebido.decode('utf-8')}")
            
        print("\n[CLIENT] Todos os pacotes foram enviados e confirmados.")

    except ConnectionRefusedError:
        print("[CLIENT] Não foi possível conectar")

    except Exception as e:
        print(f"\nErro: {e}")
        
    finally:
        cliente_socket.close()
        print("\n[CLIENT] Conexão fechada")

if __name__ == "__main__":
    iniciar_cliente()