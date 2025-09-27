import socket
import threading
import time
import base64
import random
from cryptography.fernet import Fernet

HOST = "127.0.0.1"
PORT = 7070
TAMANHO_MAX_PACOTE = 4
TIMEOUT = 1
KEY = b'wA3xQc1V1L-i6pGs_8zNYRz1lO_pfg2f8a4fP9lJj0s='

cipher_suite = Fernet(KEY)

base = 0
next_seq_num = 0
window_size = 0
lock = threading.RLock()
timer = None
pacotes_a_enviar = []
total_pacotes = 0
cliente_socket: socket.socket = None
status_pacotes = {}
tempos_envio = {}

def calcular_checksum(dados: str) -> int:
    MOD = 2**32
    soma = 0
    for i, c in enumerate(dados):
        soma = (soma + (i + 1) * ord(c)) % MOD
    return soma

def corromper_pacote(pacote_bytes: bytes) -> bytes:
    try:
        pacote_str = pacote_bytes.decode('utf-8')
        pacote_sem_delimitador = pacote_str.replace("|||", "")
        partes = pacote_sem_delimitador.split('[.]')
        
        checksum_original = int(partes[1])
        checksum_corrompido = checksum_original + 7070
        partes[1] = str(checksum_corrompido)
        
        novo_pacote_str = "[.]".join(partes) + "|||"
        return novo_pacote_str.encode('utf-8')
    except (UnicodeDecodeError, IndexError, ValueError):
        return pacote_bytes

def iniciar_timer_GBN():
    global timer
    if timer:
        timer.cancel()
    timer = threading.Timer(TIMEOUT, retransmitir_GBN)
    timer.start()

def retransmitir_GBN():
    global timer
    with lock:
        print(f"\n[TIMEOUT] Estourou o tempo! Retransmitindo a janela a partir do pacote {base}.")

        for i in range(base, next_seq_num):
            pacote = pacotes_a_enviar[i]
            cliente_socket.sendall(pacote)
            print(f"> Pacote Nº {i} RETRANSMITIDO.")

        iniciar_timer_GBN()

def receber_acks_GBN(socket: socket.socket):
    global base, timer
    
    while base < total_pacotes:
        dados_recebidos = socket.recv(1024).decode('utf-8')
        if not dados_recebidos: break

        acks_agrupados = dados_recebidos.split('ACK_')

        for ack_str in acks_agrupados:
            if not ack_str: continue
            
            ack_num = int(ack_str)
            print(f"\n[CLIENT] Servidor confirmou o pacote Nº {ack_num}.")
            
            with lock:
                if ack_num + 1 > base:
                    base = ack_num + 1

                if base == next_seq_num:
                    if timer:
                        timer.cancel()
                    print(f"[CLIENT] Janela limpa. Base = {base}. Timer parado.")
                else:
                    print(f"[CLIENT] Janela deslizou. Nova base = {base}. Reiniciando timer.")
                    iniciar_timer_GBN() 

def enviar_mensagem_GBN(socket: socket.socket, mensagem: str, modo_erro: int, chance_erro: int):
    global next_seq_num, base, pacotes_a_enviar, total_pacotes
    
    cargas_uteis = []
    for i in range(0, len(mensagem), TAMANHO_MAX_PACOTE):
        cargas_uteis.append(mensagem[i:i+TAMANHO_MAX_PACOTE])
    
    total_pacotes = len(cargas_uteis)
    
    for num_pacote, carga_util in enumerate(cargas_uteis):
        flag_fim = '1' if (num_pacote == total_pacotes - 1) else '0'
        
        carga_util_encrypted = cipher_suite.encrypt(carga_util.encode('utf-8'))
        carga_util_b64 = base64.b64encode(carga_util_encrypted).decode('utf-8')
        checksum = calcular_checksum(carga_util_b64)

        pacote = f"{num_pacote}[.]{checksum}[.]{flag_fim}[.]{carga_util_b64}|||".encode('utf-8')
        pacotes_a_enviar.append(pacote)
    
    print(f"\n[CLIENT] Mensagem dividida em {total_pacotes} pacotes.")

    ack_thread = threading.Thread(target=receber_acks_GBN, args=(socket,), daemon=True)
    ack_thread.start()

    while base < total_pacotes:
        with lock:
            while next_seq_num < base + window_size and next_seq_num < total_pacotes:
                pacote_a_enviar = pacotes_a_enviar[next_seq_num]

                deve_falhar = (modo_erro > 0) and (random.randint(1, 100) <= chance_erro)
                if deve_falhar:
                    if modo_erro == 1: # Simular Perda
                        print(f"\n> Pacote Nº {next_seq_num} PERDIDO.")
                        if base == next_seq_num:
                            iniciar_timer_GBN()
                        next_seq_num += 1
                        continue
                    
                    elif modo_erro == 2: # Simular Corrupção
                        print(f"\n> Pacote Nº {next_seq_num} CORROMPIDO.")
                        pacote_a_enviar = corromper_pacote(pacote_a_enviar)
                
                socket.sendall(pacote_a_enviar)
                if not deve_falhar:
                    print(f"\n> Pacote Nº {next_seq_num} enviado.")
                
                if base == next_seq_num:
                    iniciar_timer_GBN()
                
                next_seq_num += 1
        time.sleep(0.05)
    
    print(f"\n[CLIENT] Transmissão concluída. Todos os pacotes foram confirmados.")
    ack_thread.join(timeout=1)

def retransmitir_SR(num_pacote):
    with lock:
        if status_pacotes.get(num_pacote) == 'enviado':
            print(f"\n[TIMEOUT] Estourou para o pacote {num_pacote}! Retransmitindo.")
            pacote = pacotes_a_enviar[num_pacote]
            cliente_socket.sendall(pacote)
            tempos_envio[num_pacote] = time.time()

def monitor_de_timeout_SR():
    while base < total_pacotes:
        with lock:
            agora = time.time()
            for i in range(base, next_seq_num):
                if status_pacotes.get(i) == 'enviado':
                    if agora - tempos_envio.get(i, agora) > TIMEOUT:
                        retransmitir_SR(i)
        time.sleep(0.1)

def receber_acks_SR(socket: socket.socket):
    global base, status_pacotes
    
    while base < total_pacotes:
        dados_recebidos = socket.recv(1024).decode('utf-8')
        if not dados_recebidos: break

        acks_agrupados = dados_recebidos.split('ACK_')

        for ack_str in acks_agrupados:
            if not ack_str: continue
            
            ack_num = int(ack_str.strip())
            print(f"\n[SERVER] Servidor confirmou o pacote Nº {ack_num}.")

            with lock:
                if base <= ack_num < next_seq_num and status_pacotes.get(ack_num) == 'enviado':
                    
                    status_pacotes[ack_num] = 'acked'
                    print(f"[CLIENT] Pacote {ack_num} marcado como confirmado.")

                    if ack_num == base:
                        while status_pacotes.get(base) == 'acked':
                            base += 1
                        print(f"[CLIENT] Janela deslizou. Nova base = {base}.\n")

def enviar_mensagem_SR(socket: socket.socket, mensagem: str, modo_erro: int, chance_erro: int):
    global next_seq_num, base, pacotes_a_enviar, total_pacotes, status_pacotes, tempos_envio
    
    cargas_uteis = []
    for i in range(0, len(mensagem), TAMANHO_MAX_PACOTE):
        cargas_uteis.append(mensagem[i:i+TAMANHO_MAX_PACOTE])
    
    total_pacotes = len(cargas_uteis)
    
    for num_pacote, carga_util in enumerate(cargas_uteis):
        flag_fim = '1' if (num_pacote == total_pacotes - 1) else '0'

        carga_util_encrypted = cipher_suite.encrypt(carga_util.encode('utf-8'))
        carga_util_b64 = base64.b64encode(carga_util_encrypted).decode('utf-8')
        checksum = calcular_checksum(carga_util_b64)

        pacote = f"{num_pacote}[.]{checksum}[.]{flag_fim}[.]{carga_util_b64}|||".encode('utf-8')
        pacotes_a_enviar.append(pacote)
    
    print(f"\n[CLIENT] Mensagem dividida em {total_pacotes} pacotes.\n")

    ack_thread = threading.Thread(target=receber_acks_SR, args=(socket,), daemon=True)
    ack_thread.start()
    
    timeout_thread = threading.Thread(target=monitor_de_timeout_SR, daemon=True)
    timeout_thread.start()

    while base < total_pacotes:
        with lock:
            while next_seq_num < base + window_size and next_seq_num < total_pacotes:
                pacote_a_enviar = pacotes_a_enviar[next_seq_num]

                deve_falhar = (modo_erro > 0) and (random.randint(1, 100) <= chance_erro)
                if deve_falhar: 
                    if modo_erro == 1: # Simular Perda
                        print(f"\n> Pacote Nº {next_seq_num} PERDIDO.")
                        status_pacotes[next_seq_num] = 'enviado'
                        tempos_envio[next_seq_num] = time.time()
                        next_seq_num += 1
                        continue
                    elif modo_erro == 2: # Simular Corrupção
                        print(f"\n> Pacote Nº {next_seq_num} CORROMPIDO.")
                        pacote_a_enviar = corromper_pacote(pacote_a_enviar)

                socket.sendall(pacote_a_enviar)
                if not deve_falhar:
                    print(f"\n> Pacote Nº {next_seq_num} enviado.")
                
                status_pacotes[next_seq_num] = 'enviado'
                tempos_envio[next_seq_num] = time.time()
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
            if protocolo_operacao in ["GBN", "SR"]: break

        while True:
            tamanho_maximo_mensagem = int(input("[CLIENT] Digite o tamanho máximo do texto (min. 30): "))
            if tamanho_maximo_mensagem >= 30: break

        print("[CLIENT] Escolha um modo de simulação de erro:")
        print("- 0: Sem erro")
        print("- 1: Perder pacotes aleatoriamente")
        print("- 2: Corromper checksums aleatoriamente")

        modo_erro = 0
        while True:
            modo_erro = int(input("Digite a opção (0, 1 ou 2): "))
            if modo_erro in [0, 1, 2]: break

        chance_erro = 0
        if modo_erro in [1, 2]:
            while True:
                chance_erro = int(input(f"[CLIENT] Digite a chance de erros acontecerem: "))
                if 1 <= chance_erro <= 100: break

        handshake_message = f"{protocolo_operacao}[.]{TAMANHO_MAX_PACOTE}[.]{str(tamanho_maximo_mensagem)}".encode('utf-8')
        
        cliente_socket.sendall(handshake_message)
        print("\n[CLIENT] Dados do handshake enviados ao servidor")
        
        handshake_confirmacao = cliente_socket.recv(1024).decode('utf-8')
        window_size = int(handshake_confirmacao.split('=')[1])

        print("\n" + "="*50)
        print("HANDSHAKE RECEBIDO".center(50))
        print("="*50)
        print(f"  - Resposta do Servidor: {handshake_confirmacao.split("[.]")[0]}")
        print(f"  - Tamanho da janela definido pelo servidor: {window_size}")
        print("="*50)

        while True:
            mensagem_original = input(f"\n[CLIENT] Digite a mensagem a ser enviada (limite de {tamanho_maximo_mensagem} caracteres): ")
            if len(mensagem_original) <= tamanho_maximo_mensagem:
                break 

        if protocolo_operacao == "GBN":
            enviar_mensagem_GBN(cliente_socket, mensagem_original, modo_erro, chance_erro)
        elif protocolo_operacao == "SR":
           enviar_mensagem_SR(cliente_socket, mensagem_original, modo_erro, chance_erro)

    except ConnectionRefusedError:
        print("[CLIENT] Não foi possível conectar")
        
    finally:
        cliente_socket.close()
        print("\n[CLIENT] Conexão fechada")

if __name__ == "__main__":
    iniciar_cliente()