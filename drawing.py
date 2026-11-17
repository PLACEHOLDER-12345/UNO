# This file contains helpers to draw elements on the screen.

import other

import pygame
import game

WIDTH, HEIGHT = 800, 600

SCREEN_BG = (68, 68, 68) # #444
TEXT_COLOR = (255, 255, 255) # #fff

def load_image(path: str) -> pygame.Surface:
    return pygame.image.load(other.resource_path(path)).convert_alpha()

def get_image_by_path(path: str, size: tuple[int, int], rotation: int = 0) -> pygame.Surface:
    image = pygame.transform.scale(load_image(path), size)
    if rotation: image = pygame.transform.rotate(image, rotation)
    return image

def get_font(font_face: str, font_size: int) -> pygame.font.Font:
    return pygame.font.SysFont(font_face, font_size)

def render_text(text: str, font_face: str, font_size: int, rotation: int = 0) -> pygame.Surface:
    text_surf = get_font(font_face, font_size).render(text, True, TEXT_COLOR)
    if rotation: text_surf = pygame.transform.rotate(text_surf, rotation)
    return text_surf

class Button:
    def __init__(self, x, y, width, height, text, 
                 font_face = "Times New Roman", font_size = 36, onclick = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = get_font(font_face, font_size)
        self.text_surf = render_text(text, font_face, font_size)
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

class ButtonImage:
    def __init__(self, x, y, image: pygame.Surface | str, size, onclick = None):
        if isinstance(image, str): self.image = get_image_by_path(image, size)
        else: self.image = image
        self.rect = self.image.get_rect(topleft = (x, y))
        self.onclick = onclick

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)

    def check_click(self, events: list[pygame.event.Event]):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
                if self.onclick:
                    self.onclick()

class Textbox:
    def __init__(self, x, y, text, font_face = "Times New Roman", font_size = 36):
        self.font = get_font(font_face, font_size)
        self.text = text
        self.text_surf = render_text(self.text, font_face, font_size)
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

def draw_wild_pick(screen: pygame.Surface, events: list[pygame.event.Event], chooser: game.Player):
    from uno_mechanics import CARD_COLORS
    from pygame.time import delay

    choosing_wild_color = game.game_state["choosing_wild_color"]

    if choosing_wild_color == 1:
        Textbox(100, 300, f"""{chooser.name}, pick a color!
    Press R for red, Y for yellow, G for green, B for blue.""").draw(screen)
    elif choosing_wild_color in {2, 3, 4, 5}:
        delay(2000)

        Textbox(
            300, 400, f"The chosen color was... {CARD_COLORS[choosing_wild_color - 2].upper()}!",
            font_size = 24
        ).draw(screen)

        pygame.display.flip()

        delay(2000)

        game.game_state["choosing_wild_color"] = 0

def draw_card_picker(screen: pygame.Surface, events: list[pygame.event.Event], card_picker: game.Player):
    from uno_mechanics import is_card_playable
    # COVER THE WHOLE SCREEN
    screen.fill(SCREEN_BG)

    Textbox(50, 50, f"{card_picker.name}, choose a card to play!").draw(screen)

    CARDS_PER_ROW = 5

    page = game.game_state["card_picker_page"]

    start = (page - 1) * 12
    end = start + 12

    pygame.draw.rect(screen, (128, 128, 128), pygame.rect.Rect(100, 100, 600, 450))

    playable_cards = [card for card in card_picker.hand if is_card_playable(card)]

    for i, card in enumerate(playable_cards[start:end]):
        row = i // CARDS_PER_ROW
        col = i %  CARDS_PER_ROW

        x = 100 + col * 120
        y = 100 + row * 140

        button = ButtonImage(x, y, card.get_image(), (80, 120),
                             onclick = lambda c=card: game.select_card(card_picker, c))
        button.draw(screen); button.check_click(events)

def draw_UNO_text(screen: pygame.Surface, recipient: game.Player):
    Textbox(250, 375, f"{recipient.name} UNO!").draw(screen)

    pygame.time.delay(3000)

def draw_win_text(screen: pygame.Surface, winner: game.Player):
    # a supplement to draw_game_screen that is also there on a win.
    Textbox(250, 375, f"{winner.name} WINS!").draw(screen)

    pygame.quit()

def draw_game_screen(screen: pygame.Surface, events: list[pygame.event.Event]):
    screen.fill(SCREEN_BG)

    viewer_id = game.game_state["local_player_id"]
    player_count = len(game.game_state["player_data"])

    # STEP 1: DRAW THE YOUR TURN ARROW
    relative_turn = (game.game_state["current_turn"]["absolute"] - viewer_id) % player_count

    # a formula to rotate the image to point at the turn of whoever's turn it is.
    your_turn = get_image_by_path("assets\\YOUR_TURN.png", (160, 120), 90 - (relative_turn * 90))

    # reminder to accomodate a max of 4 players only.
    screen.blit(your_turn, (350, 225))

    # STEP 2: DRAW THE CARDS (up to 10 each)

    CARD_STRS = ["red", "yellow", "green", "blue", "wild"]
    CARD_VALS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", 
                 "skip", "reverse", "draw_two", "wild", "wild_draw_four"]

    # PLAYER'S CARDS (first player in a CPU game is the human, so show cards)

    CARD_LOCATIONS = {
        0: (250, 425, 30, 0, 0), # x, y, x spacing, y spacing, rotation
        1: (50, 150, 0, 30, 90),
        2: (450, 50, -30, 0, 180),
        3: (625, 400, 0, -30, -90),
    }

    for player_id, player in enumerate(game.game_state["player_data"]):
        seat = (player_id - viewer_id) % player_count

        start_x, start_y, spacing_x, spacing_y, rotation = CARD_LOCATIONS[seat]

        for card_index, card in enumerate(player.hand):
            # show the viewer's cards
            if card_index < 10:
                if player_id == viewer_id: 
                    screen.blit(card.get_image(), (
                        start_x + card_index * spacing_x,
                        start_y + card_index * spacing_y
                    ))
                else: 
                    filename = "assets\\cards\\empty-card.png"
                    card_image = get_image_by_path(filename, (80, 120), rotation)

                    screen.blit(card_image, (
                        start_x + card_index * spacing_x,
                        start_y + card_index * spacing_y
                    ))
            else: break

    # STEP 3: DRAW THE TOP CARD OF THE DISCARD

    top_card = game.game_state["top_card"]
    if top_card is not None: screen.blit(top_card.get_image(), (250, 250))

    # STEP 4: DRAW THE DRAW PILE
    draw_pile_image = get_image_by_path("assets\\cards\\empty-card.png", (80, 120))
    screen.blit(draw_pile_image, (500, 250))

    # STEP 5: WRITE PLAYER NAMES AND CARD AMOUNTS
    for player_id, player in enumerate(game.game_state["player_data"]):
        seat = (player_id - viewer_id) % player_count
        
        # draw the name of the player
        target_x, target_y, rotation = 0, 0, 0

        if seat == 0: target_x, target_y = (250, 555) # bottom
        elif seat == 1: target_x, target_y = (0, 200) # left
        elif seat == 2: target_x, target_y = (350, 10) # top
        elif seat == 3: target_x, target_y= (750, 250) # right

        rotation = seat * 90

        name_text = Textbox(target_x, target_y, f"{player.name} ({len(player.hand)} cards)", font_size = 24)
        name_text.text_surf = render_text(name_text.text, "Times New Roman", 24, rotation)
        name_text.draw(screen)

    # STEP 6: DRAW THE "PLAY CARD" AND "DRAW CARD" BUTTONS
    local_player = game.game_state["player_data"][viewer_id]
    play_button = Button(100, 500, 100, 33, "Play Card", font_size = 18,
                         onclick = lambda: game.play_button_handler(local_player))
    draw_button = Button(100, 450, 100, 33, "Draw Card", font_size = 18,
                         onclick = lambda: game.draw_button_handler(local_player))

    if game.game_state["current_turn"]["absolute"] == game.game_state["local_player_id"]:
        play_button.draw(screen)
        draw_button.draw(screen)
        play_button.check_click(events)
        draw_button.check_click(events)

    # CHECK FOR UNO!
    if game.game_state["UNO!"]: draw_UNO_text(screen, game.game_state["turn_player"])
    
    # CHECK FOR WINNER
    if game.game_state["winner"] is not None: draw_win_text(screen, game.game_state["winner"])

    # CHECK IF CHOOSING WILD
    if game.game_state["choosing_wild_color"]: draw_wild_pick(screen, events, game.game_state["turn_player"])

    # CHECK IF ON CARD PICKER
    if game.game_state["player_on_card_picker"]: draw_card_picker(screen, events, game.game_state["turn_player"])

def draw(screen: pygame.Surface, events: list[pygame.event.Event]):
    if game.currently_playing: draw_game_screen(screen, events)
    else: draw_main_menu(screen, events)