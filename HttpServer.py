from Udp import ReliableUDP
from urllib.parse import urlparse, parse_qs


def parse_http_request(raw_request):
    """Parse an HTTP request into method, path, headers, and body."""
    lines = raw_request.split('\r\n')
    
    # Parse request line
    request_line = lines[0]
    parts = request_line.split(' ')
    if len(parts) < 2:
        return None
    
    method = parts[0]
    path = parts[1]
    
    # Parse headers
    headers = {}
    i = 1
    while i < len(lines) and lines[i] != '':
        if ': ' in lines[i]:
            key, value = lines[i].split(': ', 1)
            headers[key] = value
        i += 1
    
    # Body is everything after the empty line
    body = '\r\n'.join(lines[i+1:]) if i + 1 < len(lines) else ''
    
    # Parse query parameters from path for GET
    params = {}
    if method == 'GET':
        parsed = urlparse(path)
        params = parse_qs(parsed.query)
        # Convert single-item lists to single values
        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        path = parsed.path
    
    # Parse body data for POST
    post_data = {}
    if method == 'POST' and body:
        post_data = parse_qs(body)
        post_data = {k: v[0] if len(v) == 1 else v for k, v in post_data.items()}
    
    return {
        'method': method,
        'path': path,
        'headers': headers,
        'params': params,
        'body': body,
        'post_data': post_data,
        'raw': raw_request
    }


if __name__ == "__main__":
    server = ReliableUDP("127.0.0.1", 8080, is_server=True)
    server.handshake()

    while True:
        data = server.receive()
        if not data:
            # Client disconnected, do new handshake for next client
            print("Client disconnected, waiting for new connection...")
            if server.server_socket:
                server.server_socket.close()
            server = ReliableUDP("127.0.0.1", 8080, is_server=True)
            server.handshake()
            continue
        
        raw_request = data.decode()
        print("=" * 50)
        print("Received request:")
        print(raw_request)
        print("=" * 50)
        
        parsed = parse_http_request(raw_request)
        
        if parsed:
            method = parsed['method']
            path = parsed['path']
            headers = parsed['headers']
            params = parsed['params']
            post_data = parsed['post_data']
            
        print(f"\nMethod: {method}")
        print(f"Path: {path}")
        print(f"\nRequest Headers:")
        for key, value in headers.items():
            print(f"  {key}: {value}")
        
        if method == 'GET' and params:
            print(f"\nQuery Parameters:")
            for key, value in params.items():
                print(f"  {key}: {value}")
        
        if method == 'POST' and post_data:
            print(f"\nPOST Data:")
            for key, value in post_data.items():
                print(f"  {key}: {value}")
        
        print()
        
        # Build response body
        response_body = ""
        if method == 'GET':
            # Replay with path name and query parameters
            if params:
                param_str = '&'.join(f"{k}={v}" for k, v in params.items())
                response_body = f"{path}?{param_str}"
            else:
                response_body = path
        elif method == 'POST':
            # Replay with created + path name
            response_body = f"created {path}"
        else:
            response_body = "Hello from server"

        response_headers = {
            'Content-Type': 'text/plain',
            'Content-Length': str(len(response_body)),
            'Server': 'ReliableUDP/1.0',
            'Connection': 'close'
        }
        
        print("Response Headers:")
        for key, value in response_headers.items():
            print(f"  {key}: {value}")
        print()
        
        header_lines = '\r\n'.join(f"{key}: {value}" for key, value in response_headers.items())
        response = (
            "HTTP/1.0 200 OK\r\n"
            f"{header_lines}\r\n"
            "\r\n"
            f"{response_body}"
        )

        server.send(response)