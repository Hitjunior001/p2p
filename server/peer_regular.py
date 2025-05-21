import socket
import os
import hashlib

PEER_IP = input("Your IP: ").strip()
FILES_DIR = f"files/{PEER_IP}"

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)
    print(f"[+] Folder '{FILES_DIR}' created.")

def calculate_checksum(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def list_files_with_checksum():
    files = {}
    for filename in os.listdir(FILES_DIR):
        path = os.path.join(FILES_DIR, filename)
        if os.path.isfile(path):
            files[filename] = calculate_checksum(path)
    return files

def main():
    EDGE_HOST = "127.0.0.1"
    EDGE_PORT = 9000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((EDGE_HOST, EDGE_PORT))
    print("Connected to edge node")

    files = list_files_with_checksum()
    sock.send(f"LIST|{files}".encode())

    while True:
        filename = input("Enter file name ('exit' to quit): ").strip()
        if filename == "exit":
            break
        if filename:
            sock.send(f"REQUEST_FILE|{filename}".encode())

    sock.close()

if __name__ == "__main__":
    main()
