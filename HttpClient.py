
from Http import HttpManual


if __name__ == "__main__":
    client = HttpManual("127.0.0.1", 8080)

    while True:
        cmd = input("Enter method (GET/POST/exit): ").strip().upper()

        if cmd == "GET":
            print(client.get(
                host="127.0.0.1",
                path="/hello",
                params={"name": "yousef", "id": 10}
            ))

        elif cmd == "POST":
            print(client.post(
                host="127.0.0.1",
                path="/submit",
                data={"username": "yousef", "password": "secret123"}
            ))

        elif cmd == "EXIT":
            break

        else:
            print("Invalid command")

    client.tcp.close()
