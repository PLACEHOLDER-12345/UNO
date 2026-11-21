# This file involves game state & logic.

import uno_mechanics
from pygame import time
import comms

class Player: # a single player object
    def __init__ (self, name: str, player_id: int):
        self.name = name
        self.player_id = player_id
        self.hand = [] # list of Card objects
        self.remote_hand_count: int | None = None

        self.status = {
            "skipped": False
        }

    @property
    def card_count(self) -> int:
        if self.remote_hand_count is not None:
            return self.remote_hand_count
        return len(self.hand)

currently_playing: bool = False # whether the game is currently starting
waiting_for_players: bool = False

waiting_room = {
    "room_code": "",
    "player_names": [None, None, None, None]
}

game_state = {
    # PUBLIC DATA FOR EVERYONE

    "local_mult": False, # False = CPU Game, True = Local Multiplayer

    "player_data": [], # list of player objects
    "winner": None, # the player object of the winner
    "current_turn": {
        "absolute": 0,
        "relative": 0, # relative to the list turn_order
    }, # index of the player whose turn it is
    "turn_player": None, # the player object of the current turn
    "turn_order": [0, 1, 2, 3], # the turn order in indices

    "top_card": None, # card on top of the discard pile

    "UNO!": False,
    "UNO_player": None,

    # LOCAL GAME STATE DATA

    "local_player_id": 0, # your local player ID

    "player_on_card_picker": False,
    "card_picker_page": False,

    "next_CPU_turn_time": 0,

    "choosing_wild_color": 0, # 0 is false, 1 is choosing, 2, 3, 4, 5 is chosen red, yellow, green, blue.
    "wild_player": None
}

def end_turn(played_card: uno_mechanics.Card | None = None):
    turn_order = game_state["turn_order"]
    if played_card is not None and played_card.value == 11 and len(turn_order) == 2:
        current_player = next(
            p for p in game_state["player_data"]
            if p.player_id == game_state["current_turn"]["absolute"]
        )
        game_state["turn_player"] = current_player
        game_state["player_on_card_picker"] = False
        print(f"next turn: {current_player.name}")
        return

    relative = game_state["current_turn"]["relative"]
    next_player = None
    for _ in turn_order:
        relative = (relative + 1) % len(turn_order)
        next_player_id = turn_order[relative]
        next_player = next(
            p for p in game_state["player_data"] if p.player_id == next_player_id
        )
        if next_player.status.get("skipped", False):
            next_player.status["skipped"] = False
            print(f"{next_player.name} was skipped")
            continue
        break

    game_state["current_turn"]["relative"] = relative
    game_state["current_turn"]["absolute"] = turn_order[relative]

    game_state["turn_player"] = next_player
    game_state["player_on_card_picker"] = False

    print(f"next turn: {next_player.name}")

def play_button_handler(player: Player):
    from uno_mechanics import is_card_playable
    print("Play card button clicked!")

    if player.player_id != game_state["current_turn"]["absolute"]: 
        print("not ur turn"); return

    playable_cards = [card for card in player.hand if is_card_playable(card, game_state["top_card"])]

    if len(playable_cards) != 0: # if any playable cards
        game_state["turn_player"] = player
        game_state["player_on_card_picker"] = True
        game_state["card_picker_page"] = 1 # 1-indexed

    # the card picker code will turn it back to False when finished

def select_card(player: Player, card: uno_mechanics.Card): 
    '''Select a card from the Card Picker, as implemented in drawing.draw_card_picker()'''
    if game_state["local_mult"] and not comms.is_host():
        comms.send_play_card(card.color, card.value, player.player_id)
        game_state["player_on_card_picker"] = False
        return

    from uno_mechanics import play_card

    played_card = play_card(game_state, player.hand, card)
    game_state["player_on_card_picker"] = False

    winner = check_for_winner()
    if winner is None:
        if played_card is not None and game_state["choosing_wild_color"] != 1: end_turn(played_card)

    if game_state["local_mult"] and comms.is_host(): comms.broadcast_game_state(comms.current_room)

def draw_button_handler(player: Player):
    print("Draw card button clicked!")

    if player.player_id != game_state["current_turn"]["absolute"]: print("not ur turn"); return # safeguard

    if game_state["local_mult"] and not comms.is_host(): comms.send_draw_card(); return

    uno_mechanics.draw_card(player.hand)
    end_turn()

    if game_state["local_mult"] and comms.is_host(): comms.broadcast_game_state(comms.current_room)

def take_turn(player: Player):
    # not this player's turn
    if player.player_id != game_state["current_turn"]["absolute"]: return
    if game_state["player_on_card_picker"]: return

    if player.status["skipped"]:
        print("You're skipped!")

        player.status["skipped"] = False
        end_turn()

        if game_state["local_mult"] and comms.is_host(): comms.broadcast_game_state()
        return

    # enable turn controls
    game_state["turn_player"] = player

def CPU_play(player: Player):
    import random

    print(f"\n{player.name}'s turn\n")

    if player.status["skipped"]:
        print(f"{player.name} was skipped")

        player.status["skipped"] = False
        end_turn()
        return

    playable_cards = [card for card in player.hand if uno_mechanics.is_card_playable(card, game_state["top_card"])]

    if len(playable_cards) == 0:
        drawn = uno_mechanics.draw_card(player.hand).__repr__()

        print(f"{player.name} drew {drawn}, and now has {len(player.hand)} cards.")

        end_turn(); return

    played = uno_mechanics.play_card(game_state, player.hand, random.choice(playable_cards))

    print(f"{player.name} played {played} and now has {len(player.hand)} cards.")

    end_turn(played)

    return

def check_for_winner() -> Player | None: 
    '''
    Check if any player has won the game.
    '''
    if game_state["local_mult"] and not comms.is_host(): return None

    for player in game_state["player_data"]:
        if player.card_count == 0:
            game_state["winner"] = player

            if comms.is_host() and game_state["local_mult"]: comms.broadcast_game_state(comms.current_room)
            return player # return the winning player
    return None # no winner yet

def update():
    '''Update game state'''

    if not currently_playing: return
    if game_state["local_mult"]: return
    if game_state["winner"] is not None: return
    if game_state["choosing_wild_color"]: return
    if game_state["UNO!"]: return

    current_player: Player = next(
        p for p in game_state["player_data"]
        if p.player_id == game_state["current_turn"]["absolute"]
    )
    local_player: Player = next(
        p for p in game_state["player_data"] 
        if p.player_id == game_state["local_player_id"]
    )

    if current_player == local_player: 
        take_turn(current_player)
        check_for_winner()
        return

    now = time.get_ticks()
    if now < game_state["next_CPU_turn_time"]: return

    if not game_state["local_mult"]: CPU_play(current_player)

    check_for_winner()

    if game_state["local_mult"] and comms.is_host(): comms.broadcast_game_state(comms.current_room)

    game_state["next_CPU_turn_time"] = now + 2000 if current_player == local_player else now

def start_CPU_game(): # start a game against CPU players
    """Start a game against CPU players."""

    print("Starting CPU game.")

    global currently_playing
    currently_playing = False

    # reset game state

    game_state["player_data"] = []
    game_state["current_turn"] = {
        "absolute": 0,
        "relative": 0
    }
    game_state["top_card"] = None
    game_state["UNO!"] = False
    game_state["uno_player"] = None
    game_state["winner"] = None
    game_state["local_mult"] = False
    game_state["choosing_wild_color"] = 0
    game_state["wild_player"] = None
    game_state["turn_order"] = [0, 1, 2, 3]

    game_state["local_player_id"] = 0

    game_state["player_on_card_picker"] = False

    # deal cards to players
    from drawing import name_entry

    for i in range(4): # 4 players
        # generate a player object with a name and ID
        name = name_entry() if i == 0 else f"Player {i + 1}"
        player = Player(name, i)
        game_state["player_data"].append(player)

        for _ in range(7): uno_mechanics.draw_card(player.hand)

        # set the top card to a random card
        game_state["top_card"] = uno_mechanics.get_random_card(no_wilds = True)

    game_state["turn_player"] = game_state["player_data"][0]
    currently_playing = True

def start_LAN_game(): # START A LAN GAME
    """Start a LAN game."""

    print("Starting LAN game.")

    room = comms.current_room
    if room is None or not comms.is_host():
        raise RuntimeError("Create a LAN room before starting the game")

    global currently_playing
    currently_playing = True

    game_state["player_data"] = []
    game_state["current_turn"] = {"absolute": 0, "relative": 0}
    game_state["top_card"] = None
    game_state["UNO!"] = False
    game_state["UNO_player"] = None
    game_state["winner"] = None
    game_state["local_mult"] = True
    game_state["local_player_id"] = 0
    game_state["player_on_card_picker"] = False
    game_state["card_picker_page"] = False
    game_state["choosing_wild_color"] = 0
    game_state["wild_player"] = None

    for player_id, name in enumerate(comms.current_room.player_names):
        if name is None: continue

        player = Player(name, player_id)
        game_state["player_data"].append(player)
        for _ in range(7): uno_mechanics.draw_card(player.hand)

    game_state["turn_order"] = [player.player_id for player in game_state["player_data"]]
    game_state["top_card"] = uno_mechanics.get_random_card(no_wilds=True)
    game_state["turn_player"] = game_state["player_data"][0]

    room.game_state = game_state
    comms.broadcast_game_state()
    comms.broadcast(room, {"type": "START_GAME"})