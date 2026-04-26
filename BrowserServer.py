import socket
from Http import HttpManual

# TCP server for browser
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 9000))
server.listen(5)

print("🌐 Browser server running on http://127.0.0.1:9000")

udp_client = HttpManual("127.0.0.1", 8080)

while True:
    conn, addr = server.accept()
    request = conn.recv(4096).decode()

    print("📥 Browser request received")
    print(request)

    try:
        first_line = request.split("\r\n")[0]
        method, path, _ = first_line.split()
    except:
        response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
        conn.send(response.encode())
        conn.close()
        continue

    # Forward to UDP HTTP system
    if method == "GET":
        response = udp_client.get("127.0.0.1", path)

    elif method == "POST":
        response = udp_client.post("127.0.0.1", path, {"a": "1"})

    else:
        response = "HTTP/1.0 200 OK\r\n\r\nHello"

    if not response:
        response = "HTTP/1.0 500 Internal Server Error\r\n\r\nError"

    conn.send(response.encode())
    conn.close()
