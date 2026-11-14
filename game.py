# This file involves game state & logic.

from uno_mechanics import Card

class Player: # a single player object
    def __init__ (self, name: str, player_id: int):
        self.name = name
        self.player_id = player_id
        self.hand = [] # list of Card objects

currently_playing = False # whether the game is currently starting

game_state = {
    "player_data": [], # list of player objects
    "current_turn": 0, # index of the player whose turn it is

    "top_card": None, # card on top of the discard pile
}

def start_CPU_game(): # start a game against CPU players
    print("Starting CPU game.")

    global currently_playing
    currently_playing = True

    pass # TODO: implement game logic for CPU players