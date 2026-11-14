# This file involves game state & logic.

import uno_mechanics

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

    # deal cards to players

    for i in range(4): # 4 players

        # generate a player object with a name and ID
        # TODO: add a way to input the player's name instead of a default
        player = Player(f"Player {i + 1}", i)
        game_state["player_data"].append(player)

        for j in range(7): # 7 cards each
            uno_mechanics.draw_card(game_state["player_data"][i].hand)

        # set the top card to a random card
        game_state["top_card"] = uno_mechanics.get_random_card()