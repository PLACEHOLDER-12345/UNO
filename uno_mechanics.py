# This file involves mechanics for the UNO game, including card management and game rules.

import random
import other
import pygame

CARD_COLORS = ["Red", "Yellow", "Blue", "Green", "Wild"]
CARD_VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "+2", "wild", "wild +4"]

CARD_SCALE = (80, 120)

card_cache = {

}

class Card: # a single UNO card with a color and value.
    def __init__(self, color: int, value: int):
        self.color = color # 0-3 for red, yellow, green, blue; 4 for wild cards
        self.value = value # 10 is skip, 11 is reverse, 12 is draw 2, 13 is wild, 14 is wild draw 4

    def __repr__(self):
        return f"{CARD_COLORS[self.color]} {CARD_VALUES[self.value]}"

    def get_image(self):
        path = f"assets\\cards\\{CARD_COLORS[self.color].lower()}_{CARD_VALUES[self.value].lower()}.png"

        if path not in card_cache:
            image = pygame.image.load(other.resource_path(path)).convert_alpha()
            image = pygame.transform.scale(image, CARD_SCALE)

            card_cache[path] = image

        return card_cache[path]

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

def wild_card(card: Card) -> Card:
    from game import game_state

    if game_state["turn_player"] == game_state["player_data"][game_state["local_player_id"]]: # if local player
        color_keys = {
            pygame.K_r: 0,  # Red
            pygame.K_y: 1,  # Yellow
            pygame.K_b: 2,  # Blue
            pygame.K_g: 3,  # Green
        }

        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN and event.key in color_keys:
                card.color = color_keys[event.key]
                break
    else: # if CPU
        card.color = random.choice((0, 1, 2, 3))

def play_card(hand: list[Card], card: Card) -> Card:

    from game import game_state

    if card not in hand: return None # cannot play a card that is not in your hand

    hand.remove(card)

    game_state["top_card"] = card # set the top card to the played card

    # action cards affect the player after the current player.
    if card.value in {10, 12, 14}:
        players = game_state["player_data"]
        if players:
            current_player = game_state["current_turn"]["absolute"]
            target = players[(current_player + 1) % len(players)]

            if hasattr(target, "status"): target.status["skipped"] = True

            if card.value in {12, 14}:
                if hasattr(target, "hand"): target_hand = target.hand
                elif isinstance(target, list): target_hand = target
                elif isinstance(target, dict): target_hand = target.get("hand", target.get("cards"))
                else: target_hand = None

                if target_hand is not None:
                    for _ in range(2 if card.value == 12 else 4):
                        draw_card(target_hand)

                if card.value == 14: wild_card(card)

    # wild
    if card.value == 13: wild_card(card)

    # reverse
    if card.value == 11:
        game_state["turn_order"].reverse()
        game_state["current_turn"] = {
            "absolute": game_state["turn_order"][0],
            "relative": 0
        }

    return game_state["top_card"]

def is_card_playable(card: Card) -> bool:
    from game import game_state

    if game_state["top_card"] is None: 
        print("we might have a problem 'ere")
        return False

    if card.color == game_state["top_card"].color or card.color == 4: return True # matching colors or wild 
    if card.value == game_state["top_card"].value: return True # matching values

    return False