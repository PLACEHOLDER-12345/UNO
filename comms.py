# This file has helpers for connection & joining rooms.

import random
import socket, threading, json

room_list = { # this is local reference

}

server_socket = None
client_socket = None

PORT = 13108 
BUFFER_SIZE = 4_096

class Room:
    def __init__ (self, host_socket):
        self.code = generate_room_code()
        self.host = host_socket # PLAYER 0 (1)
        self.clients: list = [host_socket]

        self.game_state: dict = None # AUTHORITATIVE

def generate_room_code() -> str:
    while True:
        ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        code: str = ""
        for _ in range(4): code += ABC[random.randint(1, 26) - 1]

        if code not in room_list: return code

def send(sock: socket.socket, data):
    payload = json.dumps(data).encode("utf-8")
    header = len(payload).to_bytes(4, "big")

    sock.sendall(header + payload)

def recv_exact_bytes(sock: socket.socket, size: int) -> bytes | str:
    data = b""

    while len(data) < size:
        packet = sock.recv(size - len(data))

        if not packet: raise ConnectionError("Connection closed. BYE!")

        data += packet

    return data

def recv(sock: socket.socket) -> dict:
    size = int.from_bytes(recv_exact_bytes(sock, 4), "big")
    payload = recv_exact_bytes(sock, size)
    return json.loads(payload.decode("utf-8"))

def broadcast(room: Room, packet: dict):
    dead_clients = []

    for client in room.clients:
        if client is None: continue
        try: send(client, packet)
        except: dead_clients.append(client)

    for client in dead_clients:
        room.clients.remove(client)

def broadcast_game_state(room: Room):
    broadcast(room, {
        "type": "GAME_STATE",
        "game_state": room.game_state
    })

def create_room():
    global server_socket
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen()

    room = Room(None)

    room_list[room.code] = room
    print(f"room code: {room.code}")

    threading.Thread(
        target = accept_connections,
        args = (server_socket, room),
        daemon = True
    ).start()

    return room

def client_listener(client: socket.socket, room: Room):
    try:
        while True:
            packet = recv(client)

            handle_client_message(room, client, packet)
    except Exception as e:
        print("Client disconnected;", e)
        if client in room.clients: room.clients.remove(client)

        client.close()

def server_listener():
    global client_socket
    try:
        while True:
            packet = recv(client_socket)
            handle_server_message(packet)

    except Exception as e:
        print("Lost connection to server", e)

def join_room(ip: str):
    global client_socket

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, PORT))

    threading.Thread(
        target = server_listener,
        daemon = True
    ).start()

    print(f"Connected to: {ip}")

    return client_socket

def accept_connections(server: socket.socket, room: Room):
    while len(room.clients) < 4:
        client, address = server.accept()

        room.clients.append(client)

        send(client, {
            "type": "JOIN_OK", "player_id": len(room.clients) - 1
        })

        print(f"{address} joined room {room.code}")

        threading.Thread(
            target = client_listener, args = (client, room), daemon = True
        ).start()

def send_play_card(color: int, value: int, player_id: int):
    send(client_socket, {"type": "PLAY_CARD", "player_id": player_id, "color": color, "value": value})

def send_draw_card(): send(client_socket, {"type": "DRAW_CARD"})

def send_choose_color(color: int): send(client_socket, {"type": "CHOOSE_COLOR", "color": color})

def handle_client_message(room: Room, client: socket.socket, packet: dict):
    msg_type = packet["type"]
    print(packet)

    if msg_type == "PLAY_CARD":
        pass
    elif msg_type == "DRAW_CARD":
        pass
    elif msg_type == "CHOOSE_COLOR":
        pass

    broadcast_game_state(room)

def handle_server_message(packet: dict):
    import game

    msg_type = packet["type"]

    if msg_type == "GAME_STATE": game.game_state = packet["game_state"]
    elif msg_type == "START_GAME": game.currently_playing = True
    elif msg_type == "DISCONNECT": print("Server disconnected.")
    elif msg_type == "JOIN_OK": 
        game.game_state["local_player_id"] = packet["player_id"]

        print(f"Assigned player ID {packet["player_id"]}")

def is_host() -> bool: return server_socket is not None

def player_count(room: Room): return len(room.clients)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally: s.close()