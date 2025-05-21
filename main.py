import socket
import threading

class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = [] 
        self.running = True

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        print(f"[+] Peer escutando em {self.host}:{self.port}")

        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        while self.running:
            conn, addr = self.server.accept()
            print(f"[+] Conexão recebida de {addr}")
            self.peers.append((conn, addr))
            threading.Thread(target=self.handle_peer, args=(conn, addr), daemon=True).start()

    def handle_peer(self, conn, addr):
        try:
            while self.running:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode()
                print(f"[{addr}] {message}")
                self.broadcast(message, exclude=conn)
        finally:
            print(f"[-] Desconectado de {addr}")
            self.peers = [(c, a) for c, a in self.peers if c != conn]
            conn.close()

    def connect_to_peer(self, peer_host, peer_port):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((peer_host, peer_port))
            self.peers.append((conn, (peer_host, peer_port)))
            print(f"[+] Conectado ao peer {peer_host}:{peer_port}")
            threading.Thread(target=self.handle_peer, args=(conn, (peer_host, peer_port)), daemon=True).start()
        except Exception as e:
            print(f"[x] Falha ao conectar em {peer_host}:{peer_port} - {e}")

    def send_message_to_all(self, message):
        self.broadcast(message)

    def broadcast(self, message, exclude=None):
        for conn, addr in self.peers:
            if conn != exclude:
                try:
                    conn.send(message.encode())
                except:
                    print(f"[x] Erro ao enviar para {addr}")
        # Enviar ao servidor monitor
        if self.monitor_conn:
            try:
                self.monitor_conn.send(f"[BROADCAST] {message}".encode())
            except:
                pass

    def connect_to_monitor(self, monitor_host='127.0.0.1', monitor_port=9000):
        try:
            self.monitor_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.monitor_conn.connect((monitor_host, monitor_port))
            self.monitor_conn.send(f"[INFO] Peer iniciado em {self.host}:{self.port}".encode())
        except Exception as e:
            print(f"[x] Não foi possível conectar ao monitor: {e}")

    def run(self):
        try:
            while True:
                msg = input("Você: ")
                if msg.lower() == "sair":
                    self.running = False
                    break
                self.send_message_to_all(msg)
        finally:
            self.server.close()
            for conn, _ in self.peers:
                conn.close()
            print("[-] Peer encerrado.")

if __name__ == "__main__":
    host = input("Seu IP (127.0.0.1 para local): ").strip() or "127.0.0.1"
    port = int(input("Sua porta: "))

    peer = Peer(host, port)

    while True:
        action = input("Conectar a outro peer? (s/n): ").strip().lower()
        if action == 's':
            peer_host = input("IP do peer: ").strip()
            peer_port = int(input("Porta do peer: ").strip())
            peer.connect_to_peer(peer_host, peer_port)
        else:
            break

    peer.run()
    self.monitor_conn = None
    self.connect_to_monitor()
