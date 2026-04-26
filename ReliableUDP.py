import socket
import json
import time
import random

class ReliableUDP:
    def __init__(self, ip, port, is_server=False):
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.sock.settimeout(2)

        self.seq = 0
        self.expected_seq = 0

        self.is_server = is_server

        if is_server:
            self.sock.bind(self.addr)

    # ---------------- Packet Layer ----------------
    def create_packet(self, seq, ack, flags, data):
        packet = {
            "seq": seq,
            "ack": ack,
            "flags": flags,
            "data": data,
        }

        checksum = self.compute_checksum(packet)
        packet["checksum"] = checksum
        if random.random() < 0.01:
          print("⚠️ Packet CORRUPTED (simulated)")
          packet["checksum"] = checksum + 1
        return json.dumps(packet).encode()

    def compute_checksum(self, packet):
     temp = dict(packet)
     temp["checksum"] = 0
     data = json.dumps(temp, sort_keys=True).encode()
     return sum(data) % 256

    def verify_checksum(self, packet):
     received_checksum = packet["checksum"]

     temp = dict(packet)
     temp["checksum"] = 0

     computed = sum(json.dumps(temp, sort_keys=True).encode()) % 256
     return received_checksum == computed
    # ---------------- UDP I/O ----------------
    def send_packet(self, packet, addr=None):
      if random.random() < 0.02:
        print("⚠️ Packet LOST (simulated)")
        return

      if addr is None:
        addr = self.addr

      self.sock.sendto(packet, addr)
    def receive_packet(self):
        try:
            data, addr = self.sock.recvfrom(4096)
        except socket.timeout:
             return None, None

        try:
             packet = json.loads(data.decode())
        except:
            return None, addr

        if not self.verify_checksum(packet):
          print("❌ Corrupted packet dropped")
          return None, addr

        return packet, addr

    # ---------------- Reliability Layer ----------------
    def send(self, data):
        while True:
            old_seq = self.seq

            packet = self.create_packet(
            old_seq,
            0,
            {"ACK": 0, "SYN": 0, "FIN": 0},
            data
        )

            print(f"➡️ Sending seq={old_seq}")
            self.send_packet(packet)

            ack_packet, _ = self.receive_packet()

            if ack_packet is None:
              print("⏱ Timeout → Retransmitting...")
              continue

            if ack_packet["flags"].get("ACK") == 1 and ack_packet["ack"] == old_seq:
             print(f"✅ ACK received for seq={old_seq}")
             self.seq = 1 - self.seq
             break

    def receive(self):
     while True:
        try:
            packet, addr = self.receive_packet()

            if packet is None:
                continue

            # ---------------- FIN Handling ----------------
            if packet["flags"].get("FIN") == 1:
                print("📥 FIN received")

                # 1. Send ACK for FIN
                ack = self.create_packet(
                    0, 0,
                    {"ACK": 1, "SYN": 0, "FIN": 0},
                    ""
                )
                self.sock.sendto(ack, addr)
                print("✅ Sent ACK for FIN")

                # 2. Send server FIN
                fin = self.create_packet(
                    0, 0,
                    {"FIN": 1, "ACK": 0, "SYN": 0},
                    ""
                )
                self.sock.sendto(fin, addr)
                print("🔴 Sent FIN (server side)")

                # 3. Wait for final ACK
                while True:
                    try:
                        final_ack, _ = self.receive_packet()

                        if final_ack and final_ack["flags"].get("ACK") == 1:
                            print("🔒 Connection fully closed")
                            return None

                    except socket.timeout:
                        print("⏱ Resending FIN (server)")
                        self.sock.sendto(fin, addr)

            # ---------------- Normal Data ----------------
            seq = packet["seq"]

            if seq == self.expected_seq:
                print(f"📥 Received seq={seq}")
                self.expected_seq = 1-self.expected_seq

                ack = self.create_packet(
                    0,
                    seq,
                    {"ACK": 1, "SYN": 0, "FIN": 0},
                    ""
                )
                self.sock.sendto(ack, addr)

                return packet["data"].encode()

            else:
                print("⚠️ Duplicate packet → Resend ACK")

                ack = self.create_packet(
                    0,
                    1 - self.expected_seq,
                    {"ACK": 1, "SYN": 0, "FIN": 0},
                    ""
                )
                self.sock.sendto(ack, addr)

        except socket.timeout:
             return None

    # ---------------- Handshake ----------------
    def handshake(self):
        if not self.is_server:
            # CLIENT
            print("🔵 Sending SYN")
            syn = self.create_packet(
                0, 0,
                {"SYN": 1, "ACK": 0, "FIN": 0},
                ""
            )
            

            while True:
                self.send_packet(syn)
                
                packet, _ = self.receive_packet()
                if packet is None:
                 print("⏱ Timeout → Resending SYN")
                 continue
                if packet and packet["flags"]["SYN"] == 1 and packet["flags"]["ACK"] == 1:
                    print("🟢 Received SYN-ACK")

                    ack = self.create_packet(
                         0, 0,
                         {"ACK": 1, "SYN": 0, "FIN": 0},
                         ""
                        )
                    self.send_packet(ack)
                    print("✅ Connection Established")
                    break

                

        else:
            # SERVER
            print("🟡 Waiting for SYN...")

            while True:
                
                packet, addr = self.receive_packet()
                if packet is None:
                    print("⏱ Waiting for SYN...")
                    continue

                if packet and packet["flags"]["SYN"] == 1:
                    print("🔵 Received SYN")

                    self.addr = addr

                    syn_ack = self.create_packet(
                        0, 0,
                        {"SYN": 1, "ACK": 1, "FIN": 0},
                        ""
                    )
                    self.sock.sendto(syn_ack, addr)

                    while True:
                       
                        packet, _ = self.receive_packet()
                        if packet and packet["flags"]["ACK"] == 1:
                            print("✅ Connection Established")
                            return
                        if packet is None:
                            print("⏱ Timeout → Resending SYN")
                            self.sock.sendto(syn_ack, addr)
                            continue

    # ---------------- Close ----------------
    def close(self):
        fin = self.create_packet(
        0, 0,
        {"FIN": 1, "ACK": 0, "SYN": 0},
        ""
    )

        self.send_packet(fin)
        print("🔴 Sent FIN")

        got_ack = False
        got_fin = False  # ✔ ADD THIS FLAG

        while not (got_ack and got_fin):
            try:
                packet, _ = self.receive_packet()
                if not packet:
                     continue
                if packet["flags"].get("ACK") == 1:
                    print("✅ FIN acknowledged")
                    got_ack = True

                elif packet["flags"].get("FIN") == 1:
                    sender = "client" if self.is_server else "server"
                    print(f"📥 Received FIN from {sender}")     

                # send final ACK
                    ack = self.create_packet(
                         0, 0,
                         {"ACK": 1, "SYN": 0, "FIN": 0},
                         ""
                      )
                    self.sock.sendto(ack, self.addr)
                    got_fin = True

            except socket.timeout:
             print("⏱ Resending FIN")
             self.send_packet(fin)

        self.sock.close() 
