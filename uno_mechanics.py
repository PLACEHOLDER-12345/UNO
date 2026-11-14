# This file involves mechanics for the UNO game, including card management and game rules.

import random

class Card: # a single UNO card with a color and value.
    def __init__(self, color: int, value: int):
        self.color = color # 0-3 for red, yellow, green, blue; 4 for wild cards
        self.value = value # 10 is skip, 11 is reverse, 12 is draw 2, 13 is wild, 14 is wild draw 4

    def __repr__(self):
        return f"{self.color} {self.value}"

def get_random_card() -> Card:
    color: int = random.randint(0, 4)
    value: int = random.randint(0, 14)

    # fix "limbo" card states
    if color == 4: # wild cards can only be 13 (wild) or 14 (wild draw 4)
        if value not in (13, 14): value = random.choice((13, 14))
    else: # standard colors cannot use wild values
        if value > 12: value = random.randint(0, 12)

    return Card(color, value)

def draw_card(hand: list[Card]) -> Card:
    color: int = random.randint(0, 4)
    value: int = random.randint(0, 14)

    # fix "limbo" card states
    if color == 4: # wild cards can only be 13 (wild) or 14 (wild draw 4)
        if value not in (13, 14): value = random.choice((13, 14))
    else: # standard colors cannot use wild values
        if value > 12: value = random.randint(0, 12)

    hand.append(Card(color, value))