
from Http import HttpManual


if __name__ == "__main__":
    client = HttpManual("127.0.0.1", 8080)

    while True:
        cmd = input("Enter method (GET/POST/exit,Custom): ").strip().upper()

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
        elif cmd== "CUSTOM":
            meth=input("Enter method (GET/POST/exit): ").strip().upper()
            path=input("Enter path: ").strip().lower()
            if meth == "GET":
                print(client.get(
                    host="127.0.0.1",
                    path=path,
                ))

            elif meth == "POST":
                print(client.post(
                    host="127.0.0.1",
                    path=path,
                    data={"username": "yousef", "password": "secret123"}
                ))

        elif cmd == "EXIT":
            break

        else:
            print("Invalid command")

    client.tcp.close()
