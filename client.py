import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 7070
TAMANHO_MAX_PACOTE = 4
TIMEOUT = 2

base = 0
next_seq_num = 0
window_size = 0
lock = threading.Lock()
timer = None
pacotes_a_enviar = []
total_pacotes = 0
cliente_socket: socket.socket = None

def calcular_checksum(dados: str) -> int:
    return sum(ord(c) for c in dados)

def iniciar_timer():
    global timer
    if timer:
        timer.cancel()
    timer = threading.Timer(TIMEOUT, retransmitir)
    timer.start()

def retransmitir():
    global timer
    with lock:
        print("\n" + "*"*50)
        print(f"[TIMEOUT] Estourou o tempo! Retransmitindo a janela a partir do pacote {base}.")
        print("*"*50 + "\n")

        for i in range(base, next_seq_num):
            pacote = pacotes_a_enviar[i]
            cliente_socket.sendall(pacote)
            print(f"> Pacote Nº {i} RETRANSMITIDO.")

        iniciar_timer()

def receber_acks(socket: socket.socket):
    global base, timer
    
    buffer = "" 
    while base < total_pacotes:
        try:
            dados_recebidos = socket.recv(1024).decode('utf-8')
            if not dados_recebidos:
                break
            
            buffer += dados_recebidos

            while 'ACK_' in buffer:
                try:
                    start_index = buffer.find('ACK_')
                    end_index = buffer.find('ACK_', start_index + 1)

                    if end_index == -1:
                        ack_completo = buffer
                        buffer = ""
                    else:
                        ack_completo = buffer[start_index:end_index]
                        buffer = buffer[end_index:]

                    ack_num_str = ack_completo.split('_')[1]
                    ack_num = int(ack_num_str)

                    print(f"[ACK Recebido] Servidor confirmou o pacote Nº {ack_num}.")
                
                    with lock:
                        if ack_num + 1 > base:
                            base = ack_num + 1

                        if base == next_seq_num:
                            if timer:
                                timer.cancel()
                            print(f"  - Janela limpa. Base = {base}. Timer parado.")
                        else:
                            print(f"  - Janela deslizou. Nova base = {base}. Reiniciando timer.")
                            iniciar_timer()
                
                except (ValueError, IndexError):
                    break
        
        except ConnectionAbortedError:
            break

def enviar_mensagem_GBN(socket: socket.socket, mensagem: str):
    global next_seq_num, base, pacotes_a_enviar, total_pacotes
    
    cargas_uteis = []
    for i in range(0, len(mensagem), TAMANHO_MAX_PACOTE):
        cargas_uteis.append(mensagem[i:i+TAMANHO_MAX_PACOTE])
    
    total_pacotes = len(cargas_uteis)
    
    for num_pacote, carga_util in enumerate(cargas_uteis):
        flag_fim = '1' if (num_pacote == total_pacotes - 1) else '0'
        checksum = calcular_checksum(carga_util)
        pacote = f"{num_pacote}[.]{checksum}[.]{flag_fim}[.]{carga_util}".encode('utf-8')
        pacotes_a_enviar.append(pacote)
    
    print(f"\n> [CLIENT] Mensagem dividida em {total_pacotes} pacotes.")

    ack_thread = threading.Thread(target=receber_acks, args=(socket,))
    ack_thread.daemon = True
    ack_thread.start()

    while base < total_pacotes:
        with lock:
            while next_seq_num < base + window_size and next_seq_num < total_pacotes:
                pacote_a_enviar = pacotes_a_enviar[next_seq_num]
                
                socket.sendall(pacote_a_enviar)
                time.sleep(0.02)
                print(f"> Pacote Nº {next_seq_num} enviado.")
                
                if base == next_seq_num:
                    iniciar_timer()
                
                next_seq_num += 1
        
        time.sleep(0.05)
    
    print(f"\n[CLIENT] Transmissão concluída. Todos os pacotes foram confirmados.")
    ack_thread.join(timeout=1)

def iniciar_cliente():
    global window_size, cliente_socket
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente_socket.connect((HOST, PORT))
        print(f"[CLIENT] Conectado com sucesso ao servidor em {HOST}:{PORT}\n")

        while True:
            protocolo_operacao = input("[CLIENT] Digite o protocolo (GBN ou SR): ").upper()
            if protocolo_operacao in ["GBN", "SR"]:
                break

        while True:
            tamanho_maximo_mensagem = int(input("[CLIENT] Digite o tamanho máximo do texto (min. 30): "))
            if tamanho_maximo_mensagem >= 30:
                break

        handshake_message = f"{protocolo_operacao}[.]{TAMANHO_MAX_PACOTE}[.]{str(tamanho_maximo_mensagem)}".encode('utf-8')
        
        cliente_socket.sendall(handshake_message)
        print("\n[CLIENT] Dados do handshake enviados ao servidor")
        
        handshake_confirmacao = cliente_socket.recv(1024).decode('utf-8')
        window_size = int(handshake_confirmacao.split('=')[1])

        print(f"\n[SERVER] Resposta do Servidor: {handshake_confirmacao.split("[.]")[0]}")
        print(f"[CLIENT] Tamanho da janela definido pelo servidor: {window_size}\n")

        while True:
            mensagem_original = input(f"\n[CLIENT] Digite a mensagem a ser enviada (limite de {tamanho_maximo_mensagem} caracteres): ")
            if len(mensagem_original) <= tamanho_maximo_mensagem:
                break 

        if protocolo_operacao == "GBN":
            enviar_mensagem_GBN(cliente_socket, mensagem_original)
        #elif protocolo_operacao == "SR":
        #   enviar_mensagem_SR(conexao_cliente)

    except ConnectionRefusedError:
        print("[CLIENT] Não foi possível conectar")

    except Exception as e:
        print(f"\nErro: {e}")
        
    finally:
        cliente_socket.close()
        print("\n[CLIENT] Conexão fechada")

if __name__ == "__main__":
    iniciar_cliente()