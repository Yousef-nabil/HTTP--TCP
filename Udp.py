import socket
import struct
import threading


class ReliableUDP:
    """
    Temporary simulation of ReliableUDP using normal TCP sockets.
    Keeps the same interface so later you can replace internals
    with your teammate's real UDP reliability implementation.
    """

    SYN = 0x01
    ACK = 0x02
    FIN = 0x04

    HEADER_FORMAT = "!IIHH"   # seq, ack, flags, length
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, ip, port, is_server=False):
        self.ip = ip
        self.port = port
        self.is_server = is_server

        self.seq = 0
        self.ack = 0

        self.server_socket = None
        self.sock = None
        self.conn = None

        if is_server:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((ip, port))
            self.server_socket.listen(1)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # --------------------------------------------------
    # Packet Helpers
    # --------------------------------------------------

    def create_packet(self, seq, ack, flags, data):
        if isinstance(data, str):
            data = data.encode()

        header = struct.pack(
            self.HEADER_FORMAT,
            seq,
            ack,
            flags,
            len(data)
        )

        checksum = self.compute_checksum(header + data)

        # append checksum (2 bytes)
        return header + struct.pack("!H", checksum) + data

    def compute_checksum(self, packet):
        return sum(packet) % 65535

    def verify_checksum(self, packet):
        if len(packet) < self.HEADER_SIZE + 2:
            return False

        header = packet[:self.HEADER_SIZE]
        recv_checksum = struct.unpack("!H", packet[self.HEADER_SIZE:self.HEADER_SIZE + 2])[0]
        body = header + packet[self.HEADER_SIZE + 2:]
        calc = self.compute_checksum(body)

        return recv_checksum == calc

    # --------------------------------------------------
    # Low-level socket wrappers
    # --------------------------------------------------

    def send_packet(self, packet):
        conn = self.conn if self.is_server else self.sock
        conn.sendall(packet)

    def receive_packet(self):
        conn = self.conn if self.is_server else self.sock

        # read header + checksum (HEADER_SIZE + 2 bytes)
        header = b""
        while len(header) < self.HEADER_SIZE + 2:
            chunk = conn.recv(self.HEADER_SIZE + 2 - len(header))
            if not chunk:
                return None
            header += chunk

        seq, ack, flags, length = struct.unpack(
            self.HEADER_FORMAT,
            header[:self.HEADER_SIZE]
        )

        data = b""
        while len(data) < length:
            chunk = conn.recv(length - len(data))
            if not chunk:
                break
            data += chunk

        packet = header + data

        if not self.verify_checksum(packet):
            raise Exception("Checksum failed")

        return packet

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def handshake(self):
        """
        Simulated 3-way handshake over TCP.
        """

        if self.is_server:
            self.conn, addr = self.server_socket.accept()

            syn = self.receive_packet()

            syn_ack = self.create_packet(1, 1, self.SYN | self.ACK, b"")
            self.send_packet(syn_ack)

            final_ack = self.receive_packet()

        else:
            self.sock.connect((self.ip, self.port))

            syn = self.create_packet(0, 0, self.SYN, b"")
            self.send_packet(syn)

            syn_ack = self.receive_packet()

            ack = self.create_packet(1, 1, self.ACK, b"")
            self.send_packet(ack)

    def send(self, data):
        packet = self.create_packet(self.seq, self.ack, self.ACK, data)
        self.send_packet(packet)
        self.seq += 1

    def receive(self):
        packet = self.receive_packet()
        if packet is None:
            return None

        header = packet[:self.HEADER_SIZE]
        seq, ack, flags, length = struct.unpack(self.HEADER_FORMAT, header)

        data = packet[self.HEADER_SIZE + 2:]
        self.ack = seq + 1

        return data

    def close(self):
        fin = self.create_packet(self.seq, self.ack, self.FIN, b"")
        try:
            self.send_packet(fin)
        except:
            pass

        if self.conn:
            self.conn.close()
        if self.sock:
            self.sock.close()
        if self.server_socket:
            self.server_socket.close()