# This file involves game state & logic.

import uno_mechanics
from pygame import time

class Player: # a single player object
    def __init__ (self, name: str, player_id: int):
        self.name = name
        self.player_id = player_id
        self.hand = [] # list of Card objects

        self.status = {
            "skipped": False
        }

currently_playing = False # whether the game is currently starting

game_state = {
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

    "local_player_id": 0, # your local player ID

    "player_on_card_picker": False,

    "next_CPU_turn_time": 0,

    "choosing_wild_color": 0 # 0 is false, 1 is choosing, 2, 3, 4, 5 is chosen red, yellow, green, blue.
}

def end_turn():
    game_state["current_turn"]["relative"] = (
        game_state["current_turn"]["relative"] + 1
    ) % len(game_state["player_data"])
    game_state["current_turn"]["absolute"] = game_state["turn_order"][game_state["current_turn"]["relative"]]
    game_state["player_on_card_picker"] = False

    print(f"next turn: {game_state["player_data"][game_state['current_turn']["absolute"]].name}")

def play_button_handler(player: Player):
    print("Play card button clicked!")

    if player.player_id != game_state["current_turn"]["absolute"]: 
        print("not ur turn"); return

def draw_button_handler(player: Player):
    print("Draw card button clicked!")

    if player.player_id != game_state["current_turn"]["absolute"]: 
        print("not ur turn"); return # safeguard

    uno_mechanics.draw_card(player.hand)
    end_turn()

def take_turn(player: Player):
    # not this player's turn
    if player.player_id != game_state["current_turn"]["absolute"]: return

    if player.status["skipped"]:
        print("You're skipped!")

        player.status["skipped"] = False
        end_turn()
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

    playable_cards = [card for card in player.hand if uno_mechanics.is_card_playable(card)]

    if len(playable_cards) == 0:
        drawn = uno_mechanics.draw_card(player.hand).__repr__()

        print(f"{player.name} drew {drawn}, and now has {len(player.hand)} cards.")

        end_turn(); return

    played = uno_mechanics.play_card(player.hand, random.choice(playable_cards))

    print(f"{player.name} played {played} and now has {len(player.hand)} cards.")

    end_turn()

    return

def check_for_winner() -> Player | None: # check if any player has won the game
    for player in game_state["player_data"]:
        if len(player.hand) == 0:
            game_state["winner"] = player
            return player # return the winning player
    return None # no winner yet

def update():
    if not currently_playing: return
    if game_state["winner"] is not None: return

    current_player: Player = game_state["player_data"][game_state["current_turn"]["absolute"]]

    now = time.get_ticks()
    if now <= game_state["next_CPU_turn_time"]: return

    CPU_play(current_player)

    check_for_winner()

    game_state["next_CPU_turn_time"] = now + 2000

def start_CPU_game(): # start a game against CPU players
    print("Starting CPU game.")

    global currently_playing
    currently_playing = True

    # reset game state

    game_state["player_data"] = []
    game_state["current_turn"] = {
        "absolute": 0,
        "relative": 0
    }
    game_state["top_card"] = None
    game_state["turn_order"] = [0, 1, 2, 3]

    game_state["local_player_id"] = 0

    game_state["player_on_card_picker"] = False

    # deal cards to players

    for i in range(4): # 4 players

        # generate a player object with a name and ID
        # TODO: add a way to input the player's name instead of a default
        player = Player(f"Player {i + 1}", i)
        game_state["player_data"].append(player)

        for _ in range(7): uno_mechanics.draw_card(player.hand)

        # set the top card to a random card
        game_state["top_card"] = uno_mechanics.get_random_card()

    game_state["turn_player"] = game_state["player_data"][0]