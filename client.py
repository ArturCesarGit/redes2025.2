import socket

HOST = "127.0.0.1"
PORT = 7070

def iniciar_cliente():
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente_socket.connect((HOST, PORT))
        print(f"Conectado com sucesso ao servidor em {HOST}:{PORT}")

        modo_operacao = input("Digite o modo de operação: ")
        tamanho_maximo = int(input("Digite o tamanho máximo do texto (min. 30): "))

        if tamanho_maximo < 30:
            print(f"\nerro: O valor mínimo deve ser 30.")
            return

        handshake_string = f"{modo_operacao}[.]{str(tamanho_maximo)}"
        
        cliente_socket.sendall(handshake_string.encode('utf-8'))
        print("\nDados do handshake enviados ao servidor.\n")
        
        confirmacao = cliente_socket.recv(1024)
        print(f"Resposta do Servidor: {confirmacao.decode('utf-8')}")

    except ConnectionRefusedError:
        print("Não foi possível conectar.")
    except Exception as e:
        print(f"erro: {e}")
        
    finally:
        cliente_socket.close()
        print("Conexão com o servidor fechada.")

if __name__ == "__main__":
    iniciar_cliente()