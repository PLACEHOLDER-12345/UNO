# This file involves mechanics for the UNO game, including card management and game rules.

import random

class Card: # a single UNO card with a color and value.
    def __init__(self, color: int, value: int):
        self.color = color # 0-3 for red, yellow, green, blue; 4 for wild cards
        self.value = value # 10 is skip, 11 is reverse, 12 is draw 2, 13 is wild, 14 is wild draw 4

    def __repr__(self):
        return f"{self.color} {self.value}"

def get_random_card() -> Card:
    while True:
        color: int = random.randint(0, 4)
        value: int = random.randint(0, 14)

        if color == 4: # wild cards can only be 13 (wild) or 14 (wild draw 4)
            if value not in (13, 14): continue
        else: # standard colors cannot use wild values
            if value > 12: continue

        return Card(color, value)

def draw_card(hand: list[Card]) -> Card:
    while True:
        color: int = random.randint(0, 4)
        value: int = random.randint(0, 14)

        # wild cards can only be 13 (wild) or 14 (wild draw 4)
        if color == 4 and value in (13, 14): break
        # standard colors cannot use wild values
        if color != 4 and value <= 12: break

    hand.append(Card(color, value))
    return hand[-1] # return the card that was drawn

def play_card(hand: list[Card], card: Card) -> bool:

    from game import game_state

    if card not in hand:
        return False # cannot play a card that is not in your hand

    hand.remove(card)

    game_state["top_card"] = card # set the top card to the played card

    return True # successfully played the card