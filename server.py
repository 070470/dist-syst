import socket
from flask import Flask, request, jsonify, send_file, abort
import os
import json
import threading
import time

# This code implements the server side functionality of the distributed file
# sharing system, assuming client communication by HTTP messages passed via sockets.
# Commenting still in progress!

HOST = "127.0.0.1"
PORT = 65423 
SOCK_PORT = 65411
NODES = ["insert tuples of IP addresses of other servers"]

# These numbers will need to be adjusted to include the IP addresses and
# ports being used on the servers

STORAGE = "/target_dir"
app = Flask(__name__)

def get_timestamp(filename):
    path = os.path.join(STORAGE, filename)
    if os.path.exists(path):
        timestamp = os.path.getmtime(path)
        return {"timestamp": timestamp, "node": (HOST, SOCK_PORT)}
    return None

def latest_timestamp(filename):
    latest = get_timestamp(filename)
    for host, port in NODES:
        try:
            with socket.create_connection((host, port), timeout=5) as sock:
                message = {"action": "query", "filename": filename}
                sock.sendall(json.dumps(message).encode())
                response = json.loads(sock.recv(1024).decode())
                if response.get("timestamp"):
                    if not latest or response["timestamp"] > latest["timestamp"]:
                        latest = response
        except Exception as e:
            print("Communication with node {host}:{port} failed: {e}")
    return latest

def send_file(host, port, filename):
    try:
        with socket.create_connection((host, port), timeout=2) as sock:
            filepath = os.path.join(STORAGE, filename)
            with open(filepath, "rb") as f:
                data = f.read()
            message = {"action": "sync", "filename": filename, "data": data.decode("latin1")}
            sock.sendall(json.dumps(message).encode())
    except Exception as e:
        print(f"Error sending file to node {host}:{port}: {e}")


@app.route("/file/<filename>", methods=["GET"])

def get_file(filename):

    latest = latest_timestamp(filename)

    if not latest and not os.path.exists(os.path.join(STORAGE, filename)):
        return "File not found", 404

    filepath = os.path.join(STORAGE, filename)
    if latest and ["node"] != (HOST, SOCK_PORT):

        latest_node_host, latest_node_port = latest["node"]
        try:
            with socket.create_connection((latest_node_host, latest_node_port), timeout=2) as sock:
                message = {"action": "download", "filename": filename}
                sock.sendall(json.dumps(message).encode())
                data = sock.recv(1024 * 1024)
                with open(filepath, "wb") as f:
                    f.write(data)
        except Exception as e:
            return f"Error downloading file: {e}", 500

    return send_file(filepath, as_attachment=True)


@app.route("/file/<filename>", methods=["POST"])

def save_file(filename):
    file = request.files["file"]
    path = os.path.join(STORAGE, filename)
    file.save(path)
    return "", 204

def sock_server():
    with socket.socket(socket.AF_inet, socket.SOCK_STREAM) as server_sock:
        server_sock.bind((HOST, SOCK_PORT))
        server_sock.listen()
        print(f"Listening on {HOST}:{SOCK_PORT}")
        while True:
            conn, addr = server_sock.accept()
            threading.Thread(target=socket_connection, args=(conn, addr)).start()

def socket_connection(conn, addr):
    with conn:
        try:
            message = json.loads(conn.recv(1024).decode())
            if message["action"] == "query":
                filename = message["filename"]
                timestamp = get_timestamp(filename)
                conn.sendall(json.dumps(timestamp).encode())
            elif message["action"] == "sync":
                filename = message["filename"]
                data = message["data"].encode("latin1")
                filepath = os.path.join(STORAGE, filename)
                with open(filepath, "wb") as f:
                    f.write(data)
        except Exception as e:
            print(f"Failed socket connection from {addr}: {e}")

if __name__ == "__main__":
    threading.Thread(target=sock_server, daemon=True).start()
    app.run(host=HOST, port=PORT)