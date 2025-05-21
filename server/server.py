import socket
import threading
import ast
import time

peers = {} 
lock = threading.Lock()
server_running = True

def handle_peer(conn, addr):
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            msg = data.decode()

            if msg.startswith("LIST|"):
                list_str = msg.split("|", 1)[1]
                data = ast.literal_eval(list_str)
                files = data.get('files', {})
                port = data.get('file_server_port')

                with lock:
                    peers[addr] = {'conn': conn, 'files': files, 'file_server_port': port}

                print(f"Updated file list from {addr}: {list(files.keys())}")

            elif msg.startswith("REQUEST_FILE|"):
                _, filename = msg.split("|", 1)
                print(f"File request '{filename}' from peer {addr}")

                with lock:
                    owners = [str((ip, info['file_server_port'])) for (ip, _), info in peers.items() if filename in info['files']]
                if owners:
                    response = f"FILES_FOUND|{filename}|{owners}"
                else:
                    response = f"ERROR|File {filename} not found"

                conn.send(response.encode())
            elif data and data.decode('utf-8')[0].lower() == 'q':
                del(conn, addr)
                return

    except Exception as e:
        print(f"Fail with {addr}: {e}")

    finally:
        conn.close()
        with lock:
            if addr in peers:
                del peers[addr]
        print(f"Peer: {addr} disconnected")

def check_connections_loop():
    while True:
        time.sleep(5)
        with lock:
            print("\nSeending... \n")
            print("Peers conencted:  ")
            for addr, info in list(peers.items()):
                try:                    
                    info['conn'].send("CHECK_LIST".encode())
                except:
                    print(f"Failed to send to {addr}, removing.")
                    info['conn'].close()
                    del peers[addr]

def main():
    host = "0.0.0.0"
    port = 9000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"Edge node listening on {host}:{port}")

    threading.Thread(target=check_connections_loop, daemon=True).start()

    while True:
        conn, addr = server.accept()
        print(f"{addr} connected")
        threading.Thread(target=handle_peer, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
