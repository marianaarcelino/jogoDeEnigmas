import socket
import threading
import random
import unicodedata


# Configurações
TCP_PORTA = 6000
UDP_PORTA = 5001
CHAVE_BROADCAST = "PROCURANDO_SERVIDOR_ENIGMA"

# Base de usuários simples
USUARIOS = { } 

charadas = {
    1: {
        "resposta": "laranja",
        "pistas": [
            "Sou uma fruta.",
            "Sou redonda.",
            "Minha cor é a mesma que o pôr do sol."
        ]
    },
    2: {
        "resposta": "pegadas",
        "pistas": [
            "Quanto mais você me cria, mais deixo para trás.",
            "Posso ser na areia, neve ou terra.",
            "Sigo você aonde você vai."
        ]
    },
    3: {
        "resposta": "mapa",
        "pistas": [
            "Tenho cidades, mas não tenho casas.",
            "Tenho rios, mas não tenho água.",
            "Posso mostrar florestas, mas não tenho árvores reais."
        ]
    },
    4: {
        "resposta": "selo",
        "pistas": [
            "Posso dar a volta ao mundo sem sair do lugar.",
            "Sou usado para enviar cartas.",
            "Geralmente sou pequeno e adesivo."
        ]
    },
    5: {
        "resposta": "buraco",
        "pistas": [
            "Quanto mais você tira de mim, maior eu fico.",
            "Posso estar no chão, na parede ou na terra.",
            "Geralmente não sou visível quando estou cheio."
        ]
    },
    6: {
        "resposta": "relogio de sol",
        "pistas": [
            "Não tenho bateria nem corda.",
            "Mostro as horas usando apenas a luz do Sol.",
            "Fui muito usado antes de existirem relógios modernos."
        ]
    },
    7: {
        "resposta": "eco",
        "pistas": [
            "Posso repetir o que você diz, mas não tenho boca.",
            "Apareço quando há paredes ou montanhas por perto.",
            "Posso ser ouvido depois de você falar, mas não sou você."
        ]
    }
}


class SalaDeJogo:
    def __init__(self, sala_id):
        self.sala_id = sala_id
        self.jogadores = [] # Lista de sockets
        self.pistas = {}   # Pistas distribuídas
        self.estado = "AGUARDANDO"
        self.resposta_correta = None
        self.acertos = set()

    def enviar_para_sala(self, mensagem):
        # Envia msg apenas para jogadores desta sala
        for p in self.jogadores:
            try:
                p.send(mensagem.encode())
            except:
                self.jogadores.remove(p)

 #==== Funções de utilidade ====
def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFKD', texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto

def verificar_palpite(sala, palpite):
    return normalizar(palpite) == normalizar(sala.resposta_correta)


def distribuir_pistas(sala):
    numero_charada = random.choice(list(charadas.keys()))
    charada_escolhida = charadas[numero_charada]
    pistas = charada_escolhida["pistas"].copy()
    random.shuffle(pistas)

    sala.acertos.clear()  # zera os acertos da rodada

    for i, jogador in enumerate(sala.jogadores):
        pista = pistas[i % len(pistas)]
        try:
            jogador.send(f"[PISTA] {pista}".encode())
        except:
            sala.jogadores.remove(jogador)

    sala.resposta_correta = charada_escolhida["resposta"]


salas = {} # id: SalaDeJogo

def escutar_broadcast_udp():
    """ Escuta chamadas na rede local e responde com o IP """
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('', UDP_PORTA))
    print(f"[UDP] Escutando broadcast na porta {UDP_PORTA}...")
    
    while True:
        dados, endereco = udp_sock.recvfrom(1024)
        mensagem = dados.decode()
        if mensagem == CHAVE_BROADCAST:
            # Responde diretamente para quem perguntou
            resposta = f"SERVER_FOUND|{TCP_PORTA}"
            udp_sock.sendto(resposta.encode(), endereco)

def tratar_cliente(socket_cliente, endereco):
    """ Gerencia a conexão de um cliente específico """
    print(f"[TCP] Nova conexão: {endereco}")
    
    try:
        # 1. Autenticação
        socket_cliente.send("AUTH_REQUIRED".encode())
        credenciais = socket_cliente.recv(1024).decode().split(":") # usuario:senha
        usuario, senha = credenciais[0], credenciais[1]
        
        if usuario in USUARIOS:
            if USUARIOS.get(usuario) == senha:
                socket_cliente.send("AUTH_SUCCESS".encode())
            else:
                socket_cliente.send("AUTH_FAIL".encode())
                socket_cliente.close()
                return
            
        else:
            # Usuário não existe, perguntar se quer criar
            socket_cliente.send("USER_NOT_FOUND".encode())
            resposta = socket_cliente.recv(1024).decode().strip().lower()
            if resposta == "sim":
                USUARIOS[usuario] = senha
                socket_cliente.send("AUTH_SUCCESS".encode())
                print(f"[SERVIDOR] Novo usuário criado: {usuario}")
            else:
                socket_cliente.send("AUTH_FAIL".encode())
                socket_cliente.close()
                return


        # --- Após autenticação bem-sucedida ---
        socket_cliente.send("CHOOSE_ROOM".encode())
        sala_id = int(socket_cliente.recv(1024).decode().strip())

        # Se a sala não existir, cria
        if sala_id not in salas:
            salas[sala_id] = SalaDeJogo(sala_id)

        sala_atual = salas[sala_id]
        sala_atual.jogadores.append(socket_cliente)
        print(f"Usuário {usuario} entrou na Sala {sala_atual.sala_id}")

        faltam = 3 - len(sala_atual.jogadores)

        if faltam > 0:
            sala_atual.enviar_para_sala(
                f"[SALA] {len(sala_atual.jogadores)}/3 jogadores conectados. "
                f"Aguardando mais {faltam} jogador(es)..."
            )


          # --- 2 Distribuir pistas quando todos chegarem ---
        if len(sala_atual.jogadores) == 3:
            sala_atual.enviar_para_sala(
                "[SALA] Todos os jogadores conectados! Iniciando o jogo..."
            )
            distribuir_pistas(sala_atual)


        # --- 3. Loop do Jogo ---
        while True:
            try:
                msg = socket_cliente.recv(1024).decode()
                if not msg:
                    break

                msg = msg.strip()

                # garante que existe resposta ativa
                if sala_atual.resposta_correta is None:
                    socket_cliente.send("[JOGO] Aguarde, o jogo ainda não começou.".encode())
                    continue

                # ===== /palpite =====
                if msg.lower().startswith("/palpite"):
                    palpite = msg[len("/palpite"):].strip()
                    print(f"[PALPITE][{usuario}]: {palpite}")

                    acertou = verificar_palpite(sala_atual, palpite)

                    if acertou:
                        if usuario in sala_atual.acertos:
                            socket_cliente.send("[JOGO] Você já acertou essa rodada 😉".encode())
                            continue

                        sala_atual.acertos.add(usuario)
                        sala_atual.enviar_para_sala(f"[JOGO] {usuario} acertou! 🎉")

                        faltam = len(sala_atual.jogadores) - len(sala_atual.acertos)
                        if faltam > 0:
                            sala_atual.enviar_para_sala(f"[JOGO] Falta(m) {faltam} jogador(es) acertar(em)...")
                        else:
                            sala_atual.enviar_para_sala("[JOGO] Todos desvendaram o enigma! 🕵️‍♀️✨")
                            sala_atual.enviar_para_sala("[JOGO] Nova charada chegando...")
                            sala_atual.acertos.clear()
                            distribuir_pistas(sala_atual)

                    else:
                        # envia só pro jogador que errou
                        socket_cliente.send(f"[JOGO] {palpite} está errado. Tente novamente!".encode())

                # ===== Chat normal =====
                else:
                    print(f"[CHAT][{usuario}]: {msg}")
                    sala_atual.enviar_para_sala(f"[{usuario}]: {msg}")

            except Exception as e:
                print(f"Erro no loop do jogador {usuario}: {e}")
                break


    except Exception as e:
        print(f"Erro com cliente {endereco}: {e}")
    finally:
        socket_cliente.close()

def start_server():
    # Inicia thread UDP
    threading.Thread(target=escutar_broadcast_udp, daemon=True).start()

    # Inicia TCP
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind(('0.0.0.0', TCP_PORTA))
    tcp_sock.listen()
    print(f"[TCP] Servidor rodando na porta {TCP_PORTA}")

    while True:
        socket_cliente, endereco = tcp_sock.accept()
        threading.Thread(target=tratar_cliente, args=(socket_cliente, endereco)).start()

if __name__ == "__main__":
    start_server()


