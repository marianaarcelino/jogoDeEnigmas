# README.md – Jogo de Enigmas

Sistema de Resolução Colaborativa de Pistas 🕵️‍♂️🕵️‍♀️

## Descrição
Este projeto é um jogo colaborativo em rede, onde até 3 jogadores recebem pistas diferentes sobre uma charada e precisam colaborar para adivinhar a resposta correta.
O servidor coordena o jogo, valida palpites e envia atualizações em tempo real. O sistema suporta mais de uma sala de jogo simultânea.
O cliente utiliza UDP broadcast para descobrir automaticamente o servidor na rede local e, depois, conecta via TCP para comunicação confiável durante o jogo.

## Funcionalidades
- Descoberta automática do servidor via UDP broadcast
- Comunicação confiável do jogo via TCP
- Autenticação de usuários (login ou criação de novo usuário)
- Salas de jogo com até 3 jogadores
- Distribuição de pistas de forma aleatória e individual
- Sistema de palpites com validação e feedback em tempo real
- Chat interno entre jogadores

## Pré-requisitos
- Python 3.14.2
- Sistema operacional: Windows, Linux ou macOS
- Conexão na mesma rede local para testar UDP broadcast

## Como rodar
### 1. Servidor
Digite no seu terminal:
`python3 servidor.py`

- O servidor escuta UDP na porta 5001 para descoberta e TCP na porta 6000 para comunicação com clientes.
- Logs do terminal mostram conexões e andamento do jogo.

### 2. Cliente
Digite no seu terminal:
`python3 cliente.py`

- **local →** o cliente tenta descobrir automaticamente o servidor na **mesma rede** usando UDP broadcast.
- **remoto →** você precisa digitar manualmente o **host** e a **porta** do servidor, normalmente fornecidos pelo ngrok, para permitir que jogadores de **outras redes** se conectem.  
- O cliente envia um broadcast UDP para descobrir automaticamente o servidor.
- Após encontrar o servidor, solicita login ou criação de usuário.
- Escolha uma sala para entrar (número inteiro).
- Aguarde outros jogadores para começar o jogo.
- Use `/palpite` <resposta> para tentar resolver a charada.
- Mensagens sem `/palpite` são enviadas para o chat da sala.

### Observações
- Atualmente, o jogo suporta até 3 jogadores por sala, mas pode ser expandido facilmente.
- UDP é usado somente para descoberta, garantindo rapidez e simplicidade.
- TCP garante ordem e entrega confiável das mensagens do jogo.
