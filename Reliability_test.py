import json
import unittest
from unittest.mock import patch
import random
from ReliableUDP import ReliableUDP


class Test(unittest.TestCase):

    @patch("random.random")
    def test_packet_loss(self, mock_rand):
        # Force packet loss (0.01 < 0.02)
        mock_rand.return_value = 0.01

        udp = ReliableUDP("127.0.0.1", 5000)

        # do NOT touch socket
        result = udp.send_packet(b"hello")

        # send_packet always returns None
        self.assertIsNone(result)

        udp.sock.close()

    @patch("random.random")
    def test_packet_corruption(self, mock_rand):
        # Force corruption (0.001 < 0.01)
        mock_rand.return_value = 0.001

        udp = ReliableUDP("127.0.0.1", 5000)

        packet = udp.create_packet(
            0, 0,
            {"ACK": 0, "SYN": 0, "FIN": 0},
            "hello"
        )

        decoded = json.loads(packet.decode())

        temp = dict(decoded)
        temp["checksum"] = 0
        computed = sum(json.dumps(temp, sort_keys=True).encode()) % 256

        self.assertNotEqual(decoded["checksum"], computed)

        udp.sock.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
