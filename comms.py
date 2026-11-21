# This file has helpers for connection & joining rooms.

import json
import queue
import random, time
import socket, threading

import uno_mechanics

room_list = {}

server_socket = None
client_socket = None
incoming_messages = queue.Queue()
_send_locks = {}
_send_locks_guard = threading.Lock()

PORT = 13108 
DISCOVERY_PORT, DISCOVERY_INTERVAL = 13109, 0.25
MAX_PACKET_SIZE = 1_048_576

class Room:
    '''
    A room class.
    
    :param socket.socket host_socket: The host socket.
    :param str host_name: The name of the host.
    '''

    def __init__(self, host_socket: socket.socket = None, host_name = "Host"):
        self.code = generate_room_code()
        self.host = host_socket
        self.clients: list[socket.socket | None] = [None, None, None, None]
        self.player_names: list[str | None] = [host_name, None, None, None]
        self.game_state: dict | None = None
        self.lock = threading.RLock()

class DiscoveredRoom:
    '''
    Data about a discovered room.

    :param str ip: The IP address of the room.
    :param str code: The code of the room.
    :param str host_name: The name of the room host.
    :param int player_count: Self-explanatory.
    '''
    def __init__ (self, ip: str, code: str, host_name: str, player_count: int):
        self.ip, self.code = ip, code
        self.host_name = host_name
        self.player_count = player_count
    def __repr__ (self): return f"{self.code} | {self.host_name} @ {self.ip} | {self.player_count} / 4"

current_room: Room | None = None

def card_to_JSON(card: uno_mechanics.Card | None):
    '''
    Convert a card to a JSON.

    :param uno_mechanics.Card card: The card to convert.

    :returns object: A JSON object with attributes "color" and "value".
    '''
    if card is None: return None
    return {"color": card.color, "value": card.value}

def JSON_to_card(data: str):
    '''
    Converts a JSON card object to a Card object.

    :param str data: The JSON string to convert to a Card object.

    :returns card_obj: The Card object.
    '''
    if data is None or isinstance(data, uno_mechanics.Card): return data
    if isinstance(data, str): data = json.loads(data)
    if isinstance(data, dict):
        return uno_mechanics.Card(data["color"], data["value"])
    color, value = data
    return uno_mechanics.Card(color, value)

def game_state_to_JSON(state: dict, recipient_player_id: int) -> dict:
    '''
    Converts a game_state object to a JSON to be sent. Censors hands of people other than you.

    :param dict state: The game state.
    :param int recipient_player_id: The player ID of the recipient.

    :returns out: A new dictionary to be converted into a JSON.
    '''
    players: list = state["player_data"]
    serialized_players = []
    for player in players:
        is_recipient = player.player_id == recipient_player_id
        serialized_players.append({
            "name": player.name,
            "player_id": player.player_id,
            "hand": [card_to_JSON(card) for card in player.hand] if is_recipient else None,
            "hand_count": len(player.hand),
            "status": dict(player.status),
        })

    def player_id(player): return None if player is None else player.player_id

    return {
        "player_data": serialized_players,
        "winner": player_id(state["winner"]),
        "current_turn": dict(state["current_turn"]),
        "turn_player": player_id(state["turn_player"]),
        "turn_order": list(state["turn_order"]),
        "top_card": card_to_JSON(state["top_card"]),
        "UNO!": state["UNO!"],
        "UNO_player": player_id(state["UNO_player"]),
        "choosing_wild_color": state["choosing_wild_color"],
        "wild_player": player_id(state["wild_player"]),
    }

def JSON_to_game_state(data: dict) -> dict:
    from game import Player, game_state
    players = []
    for player_data in data["player_data"]:
        player = Player(player_data["name"], player_data["player_id"])
        if player_data["hand"] is not None:
            player.hand = [JSON_to_card(card) for card in player_data["hand"]]
            player.remote_hand_count = None
        else:
            player.remote_hand_count = player_data["hand_count"]
        player.status = dict(player_data["status"])
        players.append(player)

    def player_by_id(player_id):
        if player_id is None:
            return None
        return next(player for player in players if player.player_id == player_id)

    state = dict(game_state)
    state.update({
        "local_mult": True,
        "player_data": players,
        "winner": player_by_id(data["winner"]),
        "current_turn": dict(data["current_turn"]),
        "turn_player": player_by_id(data["turn_player"]),
        "turn_order": list(data["turn_order"]),
        "top_card": JSON_to_card(data["top_card"]),
        "UNO!": data["UNO!"],
        "UNO_player": player_by_id(data["UNO_player"]),
        "choosing_wild_color": data["choosing_wild_color"],
        "wild_player": player_by_id(data["wild_player"]),
        "player_on_card_picker": False,
        "card_picker_page": False,
    })
    return state

def generate_room_code() -> str:
    while True:
        code = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))

        if code not in room_list: return code

def send(sock: socket.socket, data):
    payload = json.dumps(data).encode("utf-8")
    header = len(payload).to_bytes(4, "big")

    with _send_locks_guard:
        lock = _send_locks.setdefault(sock, threading.Lock())
    with lock:
        sock.sendall(header + payload)

def recv_exact_bytes(sock: socket.socket, size: int) -> bytes:
    data = b""

    while len(data) < size:
        packet = sock.recv(size - len(data))

        if not packet: raise ConnectionError("Connection closed. BYE!")

        data += packet

    return data

def recv(sock: socket.socket) -> dict:
    size = int.from_bytes(recv_exact_bytes(sock, 4), "big")
    if size > MAX_PACKET_SIZE:
        raise ValueError(f"Packet exceeds {MAX_PACKET_SIZE} bytes")
    payload = recv_exact_bytes(sock, size)
    return json.loads(payload.decode("utf-8"))

def broadcast(room: Room, packet: dict):
    dead_clients = []

    with room.lock: clients = list(room.clients)

    for client in clients:
        if client is None: continue
        try: send(client, packet)
        except OSError: dead_clients.append(client)

    with room.lock:
        for client in dead_clients:
            if client in room.clients: room.clients[room.clients.index(client)] = None

def broadcast_room_update(room: Room):
    broadcast(room, {
        "type": "ROOM_UPDATE",
        "room_code": room.code,
        "player_names": room.player_names
    })

def broadcast_game_state(room: Room | None = None):

    print("BROADCASTING GAME STATE")

    if room is None: room = current_room
    if room is None: raise RuntimeError("Cannot broadcast game state without an active room")
    if room.game_state is None: return

    with room.lock: clients = list(enumerate(room.clients))

    for player_id, client in clients:
        if client is None: continue

        try:
            send(client, {
                "type": "GAME_STATE",
                "game_state": game_state_to_JSON(room.game_state, player_id)
            })
        
        except OSError:
            with room.lock:
                if room.clients[player_id] is client: room.clients[player_id] = None

def create_room(your_name: str):
    global server_socket, current_room
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen()

    room = Room(server_socket, your_name.strip() or "Host")
    current_room = room

    room_list[room.code] = room
    print(f"room code: {room.code}")

    threading.Thread(target = accept_connections, args = (server_socket, room), daemon = True).start()
    threading.Thread(target = discovery_listener, args = (room,), daemon = True).start()

    return room

def find_room(code: str, timeout: float = 10.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)

    packet = {"type": "ROOM_LOOKUP", "code": code.upper()}

    print("Looking for room.")

    sock.sendto(json.dumps(packet).encode(), ("255.255.255.255", DISCOVERY_PORT))

    print("Broadcast sent.")

    try:
        data, addr = sock.recvfrom(2048)
        response = json.loads(data.decode())

        if response["type"] == "ROOM_FOUND" and response["code"] == code.upper(): return addr[0]
    except socket.timeout: return None
    finally: sock.close()

def client_listener(client: socket.socket, room: Room):
    try:
        while True:
            packet = recv(client)
            handle_client_message(room, client, packet)
    except Exception as e:
        print("Client disconnected;", e)
        with room.lock:
            player_id = None

            if client in room.clients:
                player_id = room.clients.index(client)
                room.clients[player_id] = None
                room.player_names[player_id] = None

            # Remove player from active game if a game is running
            if room.game_state is not None and player_id is not None:
                state = room.game_state

                # Remove from player list
                state["player_data"] = [p for p in state["player_data"] if p.player_id != player_id]

                # Remove from turn order
                if player_id in state["turn_order"]:
                    leaving_turn_index = state["turn_order"].index(player_id)

                    state["turn_order"].remove(player_id)

                    if state["turn_order"]:

                        # If the player whose turn it was disconnected,
                        # advance to whoever now occupies that slot.
                        if player_id == state["current_turn"]["absolute"]:
                            if leaving_turn_index >= len(state["turn_order"]):
                                leaving_turn_index = 0

                            state["current_turn"]["relative"] = leaving_turn_index

                        # If somebody before the current turn left,
                        # shift the relative index back by one.
                        elif leaving_turn_index < state["current_turn"]["relative"]:
                            state["current_turn"]["relative"] -= 1

                        state["current_turn"]["relative"] %= len(state["turn_order"])
                        state["current_turn"]["absolute"] = (
                            state["turn_order"][state["current_turn"]["relative"]]
                        )

                        state["turn_player"] = next(
                            (
                                p
                                for p in state["player_data"]
                                if p.player_id == state["current_turn"]["absolute"]
                            ), None,
                        )
                if not state["turn_order"]: room.game_state = None

                # remove from Room
                room.clients[player_id] = None
                room.player_names[player_id] = None

        broadcast_room_update(room)
        broadcast_game_state(room)
        client.close()

def close_host():
    global server_socket, current_room

    if current_room is not None: shutdown_room(current_room)

    if server_socket is not None:
        try: server_socket.close()
        except OSError: pass

    server_socket = None
    current_room = None

def server_listener(client: socket.socket):
    try:
        while True: incoming_messages.put(recv(client))

    except Exception as e:
        print("Lost connection to server", e)
        incoming_messages.put({"type": "DISCONNECT", "reason": str(e)})

def shutdown_room(room: Room, reason: str = "Host disconnected"):
    try: broadcast(room, {"type": "DISCONNECT", "reason": reason})
    except Exception: pass

    with room.lock:
        for client in room.clients:
            if client is not None:
                try: client.close()
                except OSError: pass

        room.clients = [None, None, None, None]
        room.player_names = [None, None, None, None]
        room.game_state = None

    room_list.pop(room.code, None)

def join_room(ip: str, code: str, your_name: str = "Player"):
    global client_socket

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((ip, PORT))
        send(client_socket, {
            "type": "JOIN",
            "code": code.upper(),
            "name": your_name.strip() or "Player",
        })
    except OSError:
        client_socket.close()
        client_socket = None
        raise

    threading.Thread(target = server_listener, args = (client_socket,), daemon = True).start()

    print(f"Connected to: {ip}")
    return client_socket

def discovery_listener(room: Room):
    print("Discovery listener started.")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(("", DISCOVERY_PORT))

    while True:
        try:
            print("Waiting for lookup")
            data, addr = sock.recvfrom(2048)
            print("Recieved lookup!", addr)
            print(data.decode())

            packet = json.loads(data.decode())
            print(packet)

            if packet["type"] != "ROOM_LOOKUP": continue
            if packet["code"] != room.code: continue

            print("sending ROOM_FOUND")

            response = {
                "type": "ROOM_FOUND",
                "code": room.code,
                "port": PORT,
                "host_name": room.player_names[0]
            }

            sock.sendto(json.dumps(response).encode(), addr)
        except Exception as e: print("Discovery error: ", e)

def accept_connections(server: socket.socket, room: Room):
    while True:
        try:
            client, address = server.accept()
            try:
                request = recv(client)
                if request.get("type") != "JOIN" or request.get("code") != room.code:
                    send(client, {"type": "JOIN_ERROR", "reason": "Invalid room code"})
                    client.close()
                    continue

                with room.lock:
                    player_id = next(
                        (index for index in range(1, len(room.clients))
                        if room.clients[index] is None),
                        None
                    )
                    if player_id is None:
                        send(client, {"type": "JOIN_ERROR", "reason": "Room is full"})
                        client.close()
                        continue
                    room.clients[player_id] = client
                    name = request.get("name")
                    room.player_names[player_id] = (
                        name.strip()[:32]
                        if isinstance(name, str) and name.strip()
                        else f"Player {player_id + 1}"
                    )

                send(client, {
                    "type": "JOIN_OK", "player_id": player_id,
                    "room_code": room.code, "player_names": room.player_names
                })
                print(f"{address} joined room {room.code} as player {player_id + 1}")
                broadcast_room_update(room)

                threading.Thread(target=client_listener, args=(client, room), daemon=True).start()
            except (ConnectionError, OSError, ValueError, json.JSONDecodeError) as error:
                print(f"Rejected connection from {address}: {error}")
                client.close()
        except OSError: break

def send_play_card(color: int, value: int, player_id: int):
    send(client_socket, {"type": "PLAY_CARD", "color": color, "value": value, "player_id": player_id})

def send_wild_color(color: int):
    send(client_socket, {"type": "CHOOSE_WILD_COLOR", "color": color})

def send_draw_card(): send(client_socket, {"type": "DRAW_CARD"})

def handle_client_message(room: Room, client: socket.socket, packet: dict):
    msg_type = packet["type"]
    print(packet)

    with room.lock:
        try: player_id = room.clients.index(client)
        except ValueError:
            send(client, {"type": "JOIN_ERROR", "reason": "Client is no longer in the room"})
            return

        from game import game_state

        state = room.game_state if room.game_state is not None else game_state

        if msg_type == "PLAY_CARD":
            from game import end_turn, check_for_winner

            if packet["player_id"] != player_id:
                send(client, {"type": "JOIN_ERROR", "reason": "Invalid player ID"})
                return

            if state["current_turn"]["absolute"] != player_id:
                send(client, {"type": "JOIN_ERROR", "reason": "Not your turn."})
                return

            player = next((p for p in state["player_data"] if p.player_id == player_id), None)

            if player is None: send(client, {"type": "JOIN_ERROR", "reason": "Invalid player"}); return

            card: uno_mechanics.Card = next(
                (c for c in player.hand if c.color == packet["color"] and c.value == packet["value"]), None
            )

            if card is None: send(client, {"type": "JOIN_ERROR", "reason": "Card not in hand"}); return

            played_card = uno_mechanics.play_card(state, player.hand, card)
            
            winner = check_for_winner()
            if winner is None:
                if played_card is not None and state["choosing_wild_color"] != 1: end_turn(played_card)

            room.game_state = state
            broadcast_game_state(room)
            return

        elif msg_type == "CHOOSE_WILD_COLOR":
            from game import end_turn

            if state["current_turn"]["absolute"] != player_id:
                send(client, {"type": "JOIN_ERROR", "reason": "Not your turn."})
                return

            color = packet.get("color")
            if (
                state["choosing_wild_color"] != 1
                or state["wild_player"] is None
                or state["wild_player"].player_id != player_id
                or state["top_card"] is None
                or type(color) is not int
                or color not in range(4)
            ):
                send(client, {"type": "JOIN_ERROR", "reason": "Invalid wild color choice."})
                return

            state["top_card"].color = color
            state["choosing_wild_color"] = color + 2
            end_turn()

        elif msg_type == "DRAW_CARD":
            from game import end_turn, check_for_winner

            if state["current_turn"]["absolute"] != player_id:
                send(client, {"type": "JOIN_ERROR", "reason": "Not your turn."})
                return

            player = next((p for p in state["player_data"] if p.player_id == player_id), None,)

            if player is None: send(client, {"type": "JOIN_ERROR", "reason": "Invalid player"}); return

            uno_mechanics.draw_card(player.hand)
            winner = check_for_winner()
            if winner is None: end_turn()


            room.game_state = state
            broadcast_game_state(room)
            return

    room.game_state = state
    broadcast_game_state(room)

def handle_server_message(packet: dict):
    import game

    msg_type = packet["type"]

    if msg_type == "GAME_STATE":
        state = JSON_to_game_state(packet["game_state"])
        game.game_state.clear()
        game.game_state.update(state)
    elif msg_type == "START_GAME": game.currently_playing = True
    elif msg_type == "DISCONNECT":
        print("Server disconnected.", packet["reason"])

        game.currently_playing = False
        game.waiting_for_players = False

        global client_socket
        if client_socket is not None:
            client_socket.close()
            client_socket = None
    elif msg_type == "ROOM_UPDATE":
        game.waiting_room["room_code"] = packet["room_code"]
        game.waiting_room["player_names"] = packet["player_names"]

        print("room code:", game.waiting_room["room_code"])
        print("player names:", game.waiting_room["player_names"])        
    elif msg_type == "JOIN_OK": 
        game.game_state["local_player_id"] = packet["player_id"]
        game.waiting_room["room_code"] = packet["room_code"]
        game.waiting_room["player_names"] = packet["player_names"]
        print(f"Assigned player ID {packet["player_id"]}")
        print(f"Room code: {packet["room_code"]}")
        print(f"Player names: {packet["player_names"]}")
    elif msg_type == "JOIN_ERROR":
        print("Could not join room:", packet.get("reason", "Unknown error"))

def process_server_messages():
    while True:
        try: packet = incoming_messages.get_nowait()
        except queue.Empty: return
        handle_server_message(packet)

def is_host() -> bool: return current_room is not None and server_socket is not None

def player_count(room: Room):
    with room.lock: return sum(name is not None for name in room.player_names)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally: s.close()