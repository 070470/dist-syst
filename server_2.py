import socket
from flask import Flask, request, send_file
import os
import threading
import logging


# This code implements the server side functionality of the distributed file
# sharing system, assuming client-server and server-server 
# communication through HTTP messages passed via sockets.
# Commenting still in progress!

# SUGGESTION: Consider moving configuration to a config file 
# Example config structure:
# [server]
# host = 127.0.0.1
# http_port = 65423
# socket_port = 65411

# SUGGESTION: Current JSON messages should be replaced with plaintext protocol:
# Last-Modified-Check <filename>
# Last-Modified <filename> <timestamp> <node-ID>
# File-Provision-Request <filename>
# File-Provision <filename>\n <file data>

# Server 1: 128.214.11.91
# Server 2: 128.214.9.25
# Server 3: 128.214.9.26


HOST = "127.0.0.1"
PORT = 65422 
SOCK_PORT = 65411
NODES = [("128.214.11.91", 65411), ("128.214.9.26", 65411)]

# These numbers will need to be adjusted to include the IP addresses and
# ports being used on the servers
STORAGE = "./distfiles"

# SUGGESTION: Add error checking for storage directory
if not os.path.exists(STORAGE):
    os.makedirs(STORAGE, exist_ok=True)

app = Flask(__name__)
logger = logging.getLogger(__name__)

# SUGGESTION: Add filename validation to prevent directory traversal attacks and ensure safe filenames
def validate_filename(filename):
    return (filename and                 # Check not empty
            '/' not in filename and      # No Unix paths
            '\\' not in filename and     # No Windows paths
            '..' not in filename and     # No parent dir access
            len(filename) < 255)         # Reasonable length

def get_timestamp(filename):
    
    # SUGGESTION: Add filename validation
    if not validate_filename(filename):
        return None
    
    path = os.path.join(STORAGE, filename)
    if os.path.exists(path):
        timestamp = os.path.getmtime(path)
        return f"Last-Modified {filename} {timestamp} {HOST}:{SOCK_PORT}"
    return None

def latest_timestamp(filename):
    
    # SUGGESTION: Add logging
    # Know when timestamp checks happen and for which files, track how long operations take and file access and modifications
    logging.info(f"Checking timestamps for {filename}")
    
    latest = get_timestamp(filename)
    for host, port in NODES:
        try:
            with socket.create_connection((host, port), timeout=5) as sock:

                message = f"Last-Modified-Check {filename}\n"
                sock.sendall(message.encode('utf-8'))
                response = sock.recv(1024).decode('utf-8').strip()
                if response.startswith("Last-Modified"):
                    _, _, timestamp, _ = response.split()
                    if not latest or float(timestamp) > float(latest.split()[2]):
                        latest = response
        except Exception as e:
            logging.error("Communication with node {host}:{port} failed: {e}")
    return latest

def send_file(host, port, filename):
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            filepath = os.path.join(STORAGE, filename)
            with open(filepath, "rb") as f:
                data = f.read()
            message = {"action": "sync", "filename": filename, "data": data.decode("latin1")}
            sock.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"Error sending file to node {host}:{port}: {e}")


@app.route("/file/<filename>", methods=["GET"])

def get_file(filename):
    
    # SUGGESTION: Add filename validation
    if not validate_filename(filename):
        return "Invalid filename", 400
    
    latest = latest_timestamp(filename)

    if not latest and not os.path.exists(os.path.join(STORAGE, filename)):
        return "File not found", 404

    filepath = os.path.join(STORAGE, filename)
    if latest and ["node"] != (HOST, SOCK_PORT):

        latest_node_host, latest_node_port = latest["node"]
        try:
            with socket.create_connection((latest_node_host, latest_node_port), timeout=2) as sock:
            
                message = f"File-Provision-Request {filename}\n"
                sock.sendall(message.encode('utf-8'))
                data = sock.recv(1024 * 1024)
                with open(filepath, "wb") as f:
                    f.write(data)
        except Exception as e:
            return f"Error downloading file: {e}", 500

    return send_file(filepath, as_attachment=True)


@app.route("/file/<filename>", methods=["POST"])

def save_file(filename):

    # SUGGESTION: Add input validation
    if not validate_filename(filename):
        return "Invalid filename", 400
    if 'file' not in request.files:
        return "No file provided", 400
    
    file = request.files["file"]
    path = os.path.join(STORAGE, filename)
    file.save(path)
    return "", 204


def handle_modification_check(conn, filename):
    """Respond to a modification check."""
    response = get_timestamp(filename)
    conn.sendall((response or "File not found").encode('utf-8'))


def handle_file_provision(conn, filename):
    """Provide the requested file."""
    filepath = os.path.join(STORAGE, filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            data = f.read()
        conn.sendall(data)
    else:
        conn.sendall(b"File not found")

def sock_server():
    with socket.socket(socket.AF_inet, socket.SOCK_STREAM) as server_sock:
        server_sock.bind((HOST, SOCK_PORT))
        server_sock.listen()
        logging.info(f"Listening on {HOST}:{SOCK_PORT}")
        while True:
            # SUGGESTION: Use ThreadPoolExecutor for better thread management and performance:
            # - Reuses threads instead of creating new ones for each connection
            # - Prevents server overload by limiting concurrent connections
            # with concurrent.futures.ThreadPoolExecutor() as executor:
            #     executor.submit(socket_connection, conn, addr)
            conn, addr = server_sock.accept()
            threading.Thread(target=socket_connection, args=(conn, addr)).start()

def socket_connection(conn, addr):
    with conn:
        try:
            
            message = conn.recv(1024).decode('utf-8').strip()
            if message["action"] == "query":
                filename = message["filename"]
                timestamp = get_timestamp(filename)
                conn.sendall(timestamp.encode('utf-8'))
            elif message["action"] == "sync":
                filename = message["filename"]
                data = conn.recv(1024).decode('utf-8').strip()
                if data.startswith('Last-Modified-Check'):
                    handle_modification_check(conn, data)
                elif data.startswith('File-Provision-Request'):
                    handle_file_provision(conn, data)
                filepath = os.path.join(STORAGE, filename)
                with open(filepath, "wb") as f:
                    f.write(data)
        except Exception as e:
            print(f"Failed socket connection from {addr}: {e}")

# Add missing Index-Listing feature
def handle_index_request(conn):
    try:
        files = os.listdir(STORAGE)
        response = "Index-Listing\n" + "\n".join(files) + "\n\n"
        conn.sendall(response.encode('utf-8'))
    except Exception as e:
        logging.error(f"Error listing index: {e}")

if __name__ == "__main__":
    threading.Thread(target=sock_server, daemon=True).start()
    app.run(host=HOST, port=PORT)