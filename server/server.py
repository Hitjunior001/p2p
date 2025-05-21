import socket
import threading
import ast

peers = {}  

def handle_peer(conn, addr):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            msg = data.decode()

            if msg.startswith("LIST|"):
                list_str = msg.split("|", 1)[1]
                files = ast.literal_eval(list_str)
                peers[addr] = files
                print(f"[+] Updated file list from {addr}: {list(files.keys())}")

            elif msg.startswith("REQUEST_FILE|"):
                _, filename = msg.split("|", 1)
                print(f"[!] File request '{filename}' from peer {addr}")

                owners = [peer_addr for peer_addr, files in peers.items() if filename in files]
                if owners:
                    response = f"FILES_FOUND|{filename}|{owners}"
                else:
                    response = f"ERROR|File {filename} not found"

                conn.send(response.encode())

        except Exception as e:
            print(f"[x] Error with {addr}: {e}")
            break

    conn.close()
    if addr in peers:
        del peers[addr]
        print(f"[-] Peer {addr} removed")

def main():
    host = "0.0.0.0"
    port = 9000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print(f"[+] Edge node listening on {host}:{port}")
    while True:
        conn, addr = server.accept()
        print(f"[+] Connection from {addr}")
        threading.Thread(target=handle_peer, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
