# This file contains helpers to draw elements on the screen.

import other

import pygame
import game

WIDTH, HEIGHT = 800, 600

SCREEN_BG = (68, 68, 68) # #444
TEXT_COLOR = (255, 255, 255) # #fff

class Button:
    def __init__(self, x, y, width, height, text, 
                 font_face = "Times New Roman", font_size = 36, onclick = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(font_face, font_size)
        self.text_surf = self.font.render(text, True, TEXT_COLOR)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        self.onclick = onclick

    def draw(self, screen: pygame.Surface): 
        # explicit type hint so that syntax highlighting works; it's quite annoying
        mouse = pygame.mouse.get_pos()

        # check if mouse hovers over the button, and adjust the color accordingly.
        color = (192, 192, 192) if self.rect.collidepoint(mouse) else (128, 128, 128) #CCC & #808080.
        pygame.draw.rect(screen, color, self.rect)
        screen.blit(self.text_surf, self.text_rect)

    def check_click(self, events: list[pygame.event.Event]):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos): 
                    if self.onclick: self.onclick()

class Textbox:
    def __init__(self, x, y, text, font_face = "Times New Roman", font_size = 36):
        self.font = pygame.font.SysFont(font_face, font_size)
        self.text = text
        self.text_surf = self.font.render(self.text, True, TEXT_COLOR)
        self.x = x
        self.y = y

    def draw(self, screen: pygame.Surface):
        screen.blit(self.text_surf, (self.x, self.y))

def draw_grid(screen: pygame.Surface): # grid to help with positioning elements on the screen
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

def draw_main_menu(screen: pygame.Surface, events: list[pygame.event.Event]):
    screen.fill(SCREEN_BG)

    text_1 = Textbox(125, 50, "Welcome to UNO!", font_size = 72)

    button_1 = Button(200, 200, 400, 75, "CPU Game", onclick = game.start_CPU_game)
    button_2 = Button(200, 300, 400, 75, "Create Room", onclick = lambda: print("Create Room button clicked!"))
    button_3 = Button(200, 400, 400, 75, "Join Room", onclick = lambda: print("Join Room button clicked!"))

    text_1.draw(screen)
    button_1.draw(screen)
    button_2.draw(screen)
    button_3.draw(screen)
    # check for clicks
    button_1.check_click(events)  
    button_2.check_click(events)  
    button_3.check_click(events)  

def draw_game_screen(screen: pygame.Surface, events: list[pygame.event.Event]):
    screen.fill(SCREEN_BG)

    # STEP 1: DRAW THE YOUR TURN ARROW
    your_turn = pygame.image.load(other.resource_path("assets\\YOUR_TURN.png")).convert_alpha()
    your_turn = pygame.transform.scale(your_turn, (160, 120))

    # a formula to rotate the image to point at the turn of whoever's turn it is.
    your_turn = pygame.transform.rotate(your_turn, 90 - (game.game_state["current_turn"] * 90))

    # reminder to accomodate a max of 4 players only.
    screen.blit(your_turn, (350, 225))

    # STEP 2: DRAW THE CARDS (up to 10 each)

    CARD_STRS = ["red", "yellow", "green", "blue", "wild"]
    CARD_VALS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", 
                 "skip", "reverse", "draw_two", "wild", "wild_draw_four"]

    CARD_SCALE = (80, 120) # width, height

    for i, card in enumerate(game.game_state["player_data"][0].hand):
        # load the image for the card & resize it.

        card_image = pygame.image.load(other.resource_path(
            f"assets\\cards\\{CARD_STRS[card.color]}_{CARD_VALS[card.value]}.png"
        )).convert_alpha()
        card_image = pygame.transform.scale(card_image, CARD_SCALE)

        # blit the card to the screen
        screen.blit(card_image, (250 + i * 30, 425))

    # CENSOR EVERY OTHER PERSON'S CARDS

    for i, card in enumerate(game.game_state["player_data"][1].hand):
        # load the image for the card & resize it.
        card_image = pygame.image.load(other.resource_path(f"assets\\cards\\empty-card.png")).convert_alpha()
        card_image = pygame.transform.scale(card_image, CARD_SCALE)
        card_image = pygame.transform.rotate(card_image, 90)

        # blit
        screen.blit(card_image, (50, 150 + i * 30))

    for i, card in enumerate(game.game_state["player_data"][2].hand):
        # load the image for the card & resize it.
        card_image = pygame.image.load(other.resource_path(f"assets\\cards\\empty-card.png")).convert_alpha()
        card_image = pygame.transform.scale(card_image, CARD_SCALE)
        card_image = pygame.transform.rotate(card_image, 180)

        # blit
        screen.blit(card_image, (450 - i * 30, 50))

    for i, card in enumerate(game.game_state["player_data"][3].hand):
        # load the image for the card & resize it.
        card_image = pygame.image.load(other.resource_path(f"assets\\cards\\empty-card.png")).convert_alpha()
        card_image = pygame.transform.scale(card_image, CARD_SCALE)
        card_image = pygame.transform.rotate(card_image, -90)

        # blit
        screen.blit(card_image, (625, 400 - i * 30))

    # STEP 3: DRAW THE TOP CARD OF THE DISCARD

    top_card = game.game_state["top_card"]
    if top_card: 
        # load the image for the card & resize it.
        card_image = pygame.image.load(other.resource_path(
            f"assets\\cards\\{CARD_STRS[top_card.color]}_{CARD_VALS[top_card.value]}.png"
        )).convert_alpha()
        card_image = pygame.transform.scale(card_image, CARD_SCALE)

        # blit
        screen.blit(card_image, (250, 250))

    # STEP 4: DRAW THE DRAW PILE
    draw_pile_image = pygame.image.load(other.resource_path(f"assets\\cards\\empty-card.png")).convert_alpha()
    draw_pile_image = pygame.transform.scale(draw_pile_image, CARD_SCALE)
    screen.blit(draw_pile_image, (475, 250))

    # STEP 5: WRITE PLAYER NAMES AND CARD AMOUNTS
    for i, player in enumerate(game.game_state["player_data"]):
        # draw the name of the player
        target_x, target_y, rotation = 0, 0, 0

        if i == 0: target_x, target_y = (250, 555) # bottom
        elif i == 1: target_x, target_y = (0, 200) # left
        elif i == 2: target_x, target_y = (350, 10) # top
        elif i == 3: target_x, target_y = (750, 250) # right

        rotation = i * 90

        name_text = Textbox(target_x, target_y, f"{player.name} ({len(player.hand)} cards)", font_size = 24)
        name_text.text_surf = pygame.transform.rotate(name_text.text_surf, rotation)
        name_text.draw(screen)

    # STEP 6: DRAW THE "PLAY CARD" AND "DRAW CARD" BUTTONS
    play_button = Button(100, 500, 100, 33, "Play Card", font_size = 18,
                         onclick = lambda: print("Play Card button clicked!"))
    draw_button = Button(100, 450, 100, 33, "Draw Card", font_size = 18,
                         onclick = lambda: print("Draw Card button clicked!"))

    play_button.draw(screen)
    draw_button.draw(screen)

def draw(screen: pygame.Surface, events: list[pygame.event.Event]):
    if game.currently_playing: draw_game_screen(screen, events)
    else: draw_main_menu(screen, events)