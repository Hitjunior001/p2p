import socket
import os
import hashlib
import threading
import json
import random

IP_ADDRESS = input("Your IP: ").strip()
FILES_DIR = f"files/{IP_ADDRESS}"
file_port_file = 0

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)
    print(f"[+] Folder '{FILES_DIR}' created.")

def calculate_checksum(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def list_files():
    files = {}
    for name in os.listdir(FILES_DIR):
        path = os.path.join(FILES_DIR, name)
        if os.path.isfile(path):
            files[name] = calculate_checksum(path)
    return files

def send_file_list(sock, file_server_port):
    files = list_files()
    data = {"files": files, "file_server_port": file_server_port}
    msg = "LIST|" + str(data)
    sock.send(msg.encode())

def file_server():
    global file_port_file
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("0.0.0.0", 0))
    port = srv.getsockname()[1]
    srv.listen()

    print(f"File server running on {IP_ADDRESS}:{port}")
    file_port_file = port

    while True:
        conn, addr = srv.accept()
        print(f"\nPeer {addr} is requesting a file")
        threading.Thread(target=send_file_to_peer, args=(conn,), daemon=True).start()

def send_file_to_peer(conn):
    try:
        file_request = conn.recv(1024).decode()
        file_path = os.path.join(FILES_DIR, file_request)

        if os.path.exists(file_path):
            filesize = os.path.getsize(file_path)
            conn.sendall(str(filesize).encode().ljust(16))

            ack = conn.recv(2).decode()
            if ack != "OK":
                print("Client did not acknowledge, aborting transfer")
                return

            with open(file_path, 'rb') as f:
                while chunk := f.read(4096):
                    conn.sendall(chunk)
            print(f"Sent '{file_request}'")
        else:
            print(f"File not found: {file_request}")

    except Exception as e:
        print(f"Error sending file: {e}")
    finally:
        conn.close()


def download_file_from_peer(peer_addr, filename):
    ip, port = eval(peer_addr)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        sock.send(filename.encode())

        filesize_data = b''
        while len(filesize_data) < 16:
            part = sock.recv(16 - len(filesize_data))
            if not part:
                raise Exception("Failed to receive file size")
            filesize_data += part
        filesize = int(filesize_data.decode().strip())

        sock.send(b"OK")

        save_path = os.path.join(FILES_DIR, filename)
        with open(save_path, 'wb') as f:
            bytes_received = 0
            while bytes_received < filesize:
                chunk = sock.recv(min(4096, filesize - bytes_received))
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)

        if bytes_received == filesize:
            print(f"Downloaded '{filename}' from {ip}")
        else:
            print(f"Download incomplete for '{filename}' from {ip}: {bytes_received}/{filesize} bytes")

    except Exception as e:
        print(f"Failed to download from {ip}: {e}")
    finally:
        sock.close()


def handle_server(sock):
    while True:
        try:
            data = sock.recv(4096).decode()
            if not data:
                break

            if data.startswith("FILES_FOUND|"):
                _, filename, seeders_str = data.split("|", 2)
                seeders = eval(seeders_str)
                print(f"\n\n- File '{filename}' is available on peers: {seeders}\n")

                for peer_addr in seeders:
                    print(f"\nTrying to download from {peer_addr}\n")
                    peer_addr = random.choice(seeders)
                    download_file_from_peer(peer_addr, filename)
                    break 
            elif data.startswith("ERROR|"):
                print("Fail:", data)

            elif data == "CHECK_LIST":
                # print("check received, sending file list currently.")
                send_file_list(sock, file_port_file)

        except Exception as e:
            print(f"Connection lost: {e}")
            break

def main():
    global file_port_file

    threading.Thread(target=file_server, daemon=True).start()


    EDGE_HOST = "127.0.0.1"
    EDGE_PORT = 9000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((EDGE_HOST, EDGE_PORT))
    print("Connected to edge node")

    send_file_list(sock, file_port_file)

    threading.Thread(target=handle_server, args=(sock,), daemon=True).start()


    while True:
        filename = input("Enter filename to request (or 'exit' to quit): ").strip()
        if filename.lower() == "exit":
            break
        sock.send(f"REQUEST_FILE|{filename}".encode())

if __name__ == "__main__":
    main()
