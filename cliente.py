import socket
import threading

# Configurações
UDP_PORTA = 5001
CHAVE_BROADCAST = "PROCURANDO_SERVIDOR_ENIGMA"

class ClienteRede:
    def __init__(self):
        self.socket_cliente = None
        self.conectado = False
        self.esperando_sala = False

    def descobrir_servidor(self):
        """Busca automática do servidor via UDP broadcast"""
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp.settimeout(5)

        print("[CLIENTE] Procurando servidor na rede...")
        try:
            udp.sendto(CHAVE_BROADCAST.encode(), ('255.255.255.255', UDP_PORTA))
            dados, endereco = udp.recvfrom(1024)

            msg = dados.decode()
            if msg.startswith("SERVER_FOUND"):
                porta_servidor = int(msg.split("|")[1])
                ip_servidor = endereco[0]
                print(f"[CLIENTE] Servidor encontrado em {ip_servidor}:{porta_servidor}")
                return ip_servidor, porta_servidor
        except socket.timeout:
            print("[CLIENTE] Nenhum servidor encontrado.")
            return None

        return None

    def conectar_e_autenticar(self, ip, porta, usuario, senha):
        """Conecta ao servidor TCP e autentica usuário"""
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_cliente.connect((ip, porta))

        # Pede autenticação
        msg = self.socket_cliente.recv(1024).decode()
        if msg == "AUTH_REQUIRED":
            self.socket_cliente.send(f"{usuario}:{senha}".encode())
            resultado = self.socket_cliente.recv(1024).decode()

            if resultado == "USER_NOT_FOUND":
                resposta = input(f"Usuário '{usuario}' não existe. Quer criar? (sim/não): ").strip().lower()
                self.socket_cliente.send(resposta.encode())
                resultado = self.socket_cliente.recv(1024).decode()

            if resultado == "AUTH_SUCCESS":
                print("[CLIENTE] Autenticação bem-sucedida!")
                self.conectado = True
                threading.Thread(target=self.loop_escuta, daemon=True).start()
                return True

        print("[CLIENTE] Falha na autenticação.")
        return False

    def loop_escuta(self):
        while self.conectado:
            try:
                msg = self.socket_cliente.recv(1024).decode().strip()

                if not msg:
                    continue

                if msg == "CHOOSE_ROOM":
                    sala = input("Digite o número da sala que quer entrar: ")
                    self.socket_cliente.send(sala.encode())

                elif msg == "READY":
                    print("[SERVIDOR] Pronto para jogar!")

                else:
                    print("[SERVIDOR]", msg)

            except:
                print("[CLIENTE] Conexão encerrada.")
                self.conectado = False
                break


def main():
    cliente = ClienteRede()

    # Pergunta se quer modo local ou remoto
    modo = input("Modo de conexão (local / remoto): ").strip().lower()

    if modo == "local":
        servidor_info = cliente.descobrir_servidor()
        if not servidor_info:
            print("[CLIENTE] Nenhum servidor local encontrado.")
            return
        ip, porta = servidor_info

    elif modo == "remoto":
        ip = input("Digite o host do servidor: ").strip()
        porta = int(input("Digite a porta do servidor: ").strip())

    else:
        print("Modo inválido.")
        return

    # Login
    usuario = input("Usuário: ")
    senha = input("Senha: ")

    if cliente.conectar_e_autenticar(ip, porta, usuario, senha):
        print("[CLIENTE] Pronto para jogar")

        # Mantém o cliente vivo
        try:
            while True:
                msg = input("> ")
                cliente.socket_cliente.send(msg.encode())
        except KeyboardInterrupt:
            print("\n[CLIENTE] Encerrando...")


if __name__ == "__main__":
    main()
