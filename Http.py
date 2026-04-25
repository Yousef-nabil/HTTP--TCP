from ReliableUDP import ReliableUDP

class HttpManual:
    def __init__(self, ip="127.0.0.1", port=8080):
        self.tcp = ReliableUDP(ip, port, False)
        self.tcp.handshake()

    def get(self, host, path, params=None, headers=None):
        query = ""
        if params:
            query = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        
        # Default headers
        req_headers = {
            'Host': host,
            'User-Agent': 'HttpManual/1.0',
            'Accept': '*/*',
            'Connection': 'close'
        }
        if headers:
            req_headers.update(headers)
        
        # Build header lines
        header_lines = '\\r\\n'.join(f"{k}: {v}" for k, v in req_headers.items())
        
        request = (
            f"GET {path}{query} HTTP/1.0\\r\\n"
            f"{header_lines}\\r\\n"
            "\\r\\n"
        )
        self.tcp.send(request)
        response = self.tcp.receive()
        return response.decode() if response else None

    def post(self, host, path, data=None, headers=None):
        body = ""
        if data:
            body = "&".join(f"{k}={v}" for k, v in data.items())
        
        # Default headers
        req_headers = {
            'Host': host,
            'User-Agent': 'HttpManual/1.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(body)),
            'Connection': 'close'
        }
        if headers:
            req_headers.update(headers)
        
        # Build header lines
        header_lines = '\\r\\n'.join(f"{k}: {v}" for k, v in req_headers.items())
        
        request = (
            f"POST {path} HTTP/1.0\\r\\n"
            f"{header_lines}\\r\\n"
            "\\r\\n"
            f"{body}"
        )
        self.tcp.send(request)
        response = self.tcp.receive()
        return response.decode() if response else None
    
