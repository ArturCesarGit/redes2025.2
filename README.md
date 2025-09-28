# Implementação dos Protocolos Go-Back-N e Selective Repeat em Python

Este projeto consiste em uma aplicação cliente-servidor desenvolvida em Python que simula a transferência de dados confiável sobre uma camada de transporte não confiável, utilizando os protocolos de janela deslizante **Go-Back-N (GBN)** e **Selective Repeat (SR)**.

A aplicação também implementa funcionalidades adicionais como **criptografia de ponta a ponta** para a carga útil dos pacotes e **verificação de integridade** através de checksum.

## 🚀 Funcionalidades

-   **Dois Protocolos de Transporte:** Implementação completa dos mecanismos de envio e recebimento para GBN e SR.
-   **Comunicação Cliente-Servidor:** Arquitetura baseada em Sockets TCP.
-   **Janela Deslizante:** Controle de fluxo e de congestionamento utilizando o conceito de janela deslizante tanto no cliente (emissor) quanto no servidor (receptor).
-   **Segurança:** Criptografia simétrica (usando `Fernet`) da carga útil de cada pacote para garantir a confidencialidade da mensagem.
-   **Detecção de Erros:** Cálculo e verificação de um `checksum` para cada pacote, permitindo ao receptor detectar corrupções nos dados.
-   **Simulação de Falhas:** O cliente pode ser configurado para simular a **perda de pacotes** ou a **corrupção de checksums** com uma probabilidade definida, permitindo observar e testar os mecanismos de recuperação de cada protocolo.
-   **Handshake Inicial:** Cliente e servidor negociam o protocolo a ser utilizado e o tamanho da mensagem antes de iniciar a transmissão.

## ⚙️ Como Funciona

O fluxo de comunicação se inicia com o cliente, que determina qual protocolo será usado e envia essa informação, juntamente com outros metadados, ao servidor através de um *handshake*.

Após a confirmação, o cliente fragmenta a mensagem a ser enviada, criptografa cada fragmento e os encapsula em pacotes.

### Estrutura do Pacote

Cada pacote enviado pelo cliente segue a seguinte estrutura:

`numero_sequencia[.]checksum[.]flag_fim[.]carga_util_criptografada|||`

## 📋 Lógica dos Protocolos

#### Go-Back-N (GBN)

-   **Emissor (Cliente)**: Envia uma janela de pacotes e mantém um único *timer*. Se o ACK para o pacote base da janela não chega dentro do tempo limite, toda a janela (a partir do pacote base) é retransmitida.
-   **Receptor (Servidor)**: Apenas aceita pacotes em ordem. Se um pacote chega fora de ordem, ele é descartado. O servidor envia ACKs cumulativos, confirmando o recebimento de todos os pacotes até um certo número de sequência.

#### Selective Repeat (SR)

-   **Emissor (Cliente)**: Mantém um *timer* para cada pacote enviado. Se o tempo estoura para um pacote específico, apenas aquele pacote é retransmitido.
-   **Receptor (Servidor)**: Aceita e armazena em buffer pacotes que chegam fora de ordem, desde que estejam dentro da sua janela de recepção. Envia ACKs individuais para cada pacote recebido corretamente. Os pacotes são entregues para a camada de aplicação em ordem assim que a sequência é completada.
