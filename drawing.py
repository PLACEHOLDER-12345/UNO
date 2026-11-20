# This file contains helpers to draw elements on the screen.

import other

import pygame
import game

WIDTH, HEIGHT = 800, 600

SCREEN_BG = (68, 68, 68) # #444
TEXT_COLOR = (255, 255, 255) # #fff

_wild_result_started_at: int | None = None
_uno_text_started_at: int | None = None

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

class TextInput:
    def __init__(self, x, y, l, w, font_face = "Times New Roman", font_size = 36, max_chars_input = 32):
        self.font = get_font(font_face, font_size)
        self.input = ""
        self.x, self.y = x, y
        self.l, self.w = l, w
        self.font_face: int = font_face
        self.font_size: int = font_size
        self.text_surf = render_text(self.input, font_face, font_size)
        self.max_chars_input = max_chars_input
        self.active = False
        self.rect = pygame.Rect(x, y, l, w)

    def draw(self, screen: pygame.Surface):
        # Draw the input box
        color = (192, 192, 192) if self.active else (128, 128, 128)
        pygame.draw.rect(screen, SCREEN_BG, self.rect)
        pygame.draw.rect(screen, color, self.rect, 2)
        # Render the text
        self.text_surf = render_text(self.input, self.font_face, self.font_size)
        screen.blit(self.text_surf, (self.x + 5, self.y + (self.w - self.text_surf.get_height()) // 2))

    def activate(self, screen: pygame.Surface):
        '''Accept text until Enter is pressed.'''
        global draw_grid

        clock = pygame.time.Clock()
        done = False
        self.active = True

        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: done = True
                    elif event.key == pygame.K_BACKSPACE: self.input = self.input[:-1]
                    elif (self.max_chars_input == -1 or
                          len(self.input) < self.max_chars_input):
                        if event.unicode.isprintable(): self.input += event.unicode
            draw_grid(screen)
            self.draw(screen)
            
            pygame.display.flip()
            clock.tick(30)

        self.active = False

def draw_grid(screen: pygame.Surface): # grid to help with positioning elements on the screen
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

def name_entry() -> str:
    screen = pygame.display.get_surface()
    player_name = "Player 1"

    screen.fill(SCREEN_BG)
    Textbox(50, 500, "Enter your name:", font_size=36).draw(screen)

    name_input = TextInput(
        400, 500, 400, 50,
        font_face = "Times New Roman",
        font_size = 36,
        max_chars_input = 32
    )
    name_input.draw(screen)
    name_input.activate(screen)

    player_name = name_input.input.strip() or "Player 1"

    return player_name

def draw_main_menu(screen: pygame.Surface, events: list[pygame.event.Event]):
    from comms import create_room, find_room, join_room

    screen.fill(SCREEN_BG)

    text_1 = Textbox(125, 50, "Welcome to UNO!", font_size = 72)

    def prompt_entry(screen: pygame.Surface, label: str, y: int,
                    width: int = 400, max_chars: int = 32) -> str:
        screen.fill(SCREEN_BG)
        Textbox(50, y, label, font_size = 36).draw(screen)
        text_input = TextInput(
            400, y, width, 50,
            font_face = "Times New Roman",
            font_size = 36,
            max_chars_input = max_chars
        )
        text_input.draw(screen)
        text_input.activate(screen)
        return text_input.input.strip()

    def CPU_game_handler(): game.start_CPU_game()

    def create_room_handler():
        print("Create Room button clicked!")
        create_room(name_entry())
        game.waiting_for_players = True

    def join_room_handler():
        print("Join Room button clicked.")

        player_name = name_entry()
        code = prompt_entry(screen, "Room code:", 300, max_chars = 4).strip().upper()

        if len(code) != 4 or not code.isalpha(): print("Room code must be 4 letters"); return

        try:
            ip = find_room(code)
            if ip is None: print("Room not found"); return
            join_room(ip, code, player_name)
            game.waiting_for_players = True
        except (OSError, ConnectionError) as error: print("Could not join room:", error)

    button_1 = Button(200, 200, 400, 75, "CPU Game", onclick = CPU_game_handler)
    button_2 = Button(200, 300, 400, 75, "Create Room", onclick = create_room_handler)
    button_3 = Button(200, 400, 400, 75, "Join Room", onclick = join_room_handler)

    text_1.draw(screen)
    button_1.draw(screen)
    button_2.draw(screen)
    button_3.draw(screen)
    # check for clicks
    button_1.check_click(events)  
    button_2.check_click(events)  
    button_3.check_click(events)  

def draw_LAN_wait(screen: pygame.Surface, events: list[pygame.event.Event], room):
    from comms import player_count
    
    '''Draw the waiting screen in a LAN game.'''

    screen.fill(SCREEN_BG)

    if room is not None:
        # FOR THE HOST 
        room_code = room.code
        with room.lock: players = list(room.player_names)
        num_players = player_count(room)
        Textbox(250, 40, "Waiting for players.").draw(screen)
    else:
        # FOR THE CLIENT
        room_code = game.waiting_room["room_code"] or "----"
        players = list(game.waiting_room["player_names"])
        num_players = sum(name is not None for name in players)
        Textbox(250, 40, "Joined room.").draw(screen)
        Textbox(250, 120, "Waiting for host.").draw(screen)

    Textbox(250, 40, "Waiting for Players", font_size = 48).draw(screen)
    Textbox(300, 120, f"Room Code: {room_code}", font_size = 28).draw(screen)

    with room.lock: players = list(room.player_names)

    Textbox(225, 180, "Players", font_size = 32).draw(screen)

    for index in range(4):
        y = 230 + index * 55
        pygame.draw.rect(screen, (128, 128, 128), (225, y, 350, 45), 2)

        name = players[index]
        Textbox(
            240, y + 7, name if name is not None else "Waiting...",
            font_size = 24
        ).draw(screen)

    if room is not None:
        if num_players in {0, 1}:
            dots = "." * (1 + (pygame.time.get_ticks() // 500) % 3)
            Textbox(250, 500, f"Searching for players{dots}", font_size = 36).draw(screen)
        else: 
            button = Button(225, 500, 200, 75, f"Start!", onclick = game.start_LAN_game)
            button.draw(screen); button.check_click(events)

def draw_wild_pick(screen: pygame.Surface, events: list[pygame.event.Event], chooser: game.Player):
    from uno_mechanics import CARD_COLORS
    global _wild_result_started_at

    choosing_wild_color = game.game_state["choosing_wild_color"]

    if choosing_wild_color == 1:
        Textbox(150, 375, f"""{chooser.name}, pick a color!
    Press R for red, Y for yellow, G for green, B for blue.""", font_size = 18).draw(screen)
        color_keys = {
            pygame.K_r: 0, pygame.K_y: 1,
            pygame.K_g: 2, pygame.K_b: 3,
        }
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in color_keys:
                game.game_state["top_card"].color = color_keys[event.key]
                game.game_state["choosing_wild_color"] = color_keys[event.key] + 2

                game.end_turn()

                _wild_result_started_at = pygame.time.get_ticks()
                break
    elif choosing_wild_color in {2, 3, 4, 5}:
        if _wild_result_started_at is None:
            _wild_result_started_at = pygame.time.get_ticks()
        Textbox(
            300, 400, f"The chosen color was... {CARD_COLORS[choosing_wild_color - 2].upper()}!",
            font_size = 24
        ).draw(screen)

        if pygame.time.get_ticks() - _wild_result_started_at >= 2000:
            game.game_state["choosing_wild_color"] = 0
            game.game_state["wild_player"] = None
            _wild_result_started_at = None

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

    playable_cards = [card for card in card_picker.hand if is_card_playable(card, game.game_state["top_card"])]

    for i, card in enumerate(playable_cards[start:end]):
        row = i // CARDS_PER_ROW
        col = i %  CARDS_PER_ROW

        x = 100 + col * 120
        y = 100 + row * 140

        button = ButtonImage(x, y, card.get_image(), (80, 120),
                             onclick = lambda c=card: game.select_card(card_picker, c))
        button.draw(screen); button.check_click(events)

def draw_UNO_text(screen: pygame.Surface, recipient: game.Player):
    global _uno_text_started_at

    if _uno_text_started_at is None: _uno_text_started_at = pygame.time.get_ticks()

    Textbox(275, 375, f"{recipient.name} UNO!", font_size = 36).draw(screen)

    if pygame.time.get_ticks() - _uno_text_started_at >= 3000:
        game.game_state["UNO!"] = 0
        game.game_state["UNO_player"] = None
        _uno_text_started_at = None

def draw_win_text(screen: pygame.Surface, winner: game.Player):
    # a supplement to draw_game_screen that is also there on a win.
    Textbox(250, 375, f"{winner.name} WINS!").draw(screen)

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

    CARD_LOCATIONS = {
        0: (250, 425, 30, 0, 0), # x, y, x spacing, y spacing, rotation
        1: (50, 150, 0, 30, 90),
        2: (450, 50, -30, 0, 180),
        3: (625, 400, 0, -30, -90),
    }

    for player_id, player in enumerate(game.game_state["player_data"]):
        seat = (player_id - viewer_id) % player_count

        start_x, start_y, spacing_x, spacing_y, rotation = CARD_LOCATIONS[seat]

        for card_index in range(player.card_count):
            # show the viewer's cards
            if card_index < 10:
                if player_id == viewer_id: 
                    card = player.hand[card_index]
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

        name_text = Textbox(target_x, target_y, f"{player.name} ({player.card_count} cards)", font_size = 24)
        name_text.text_surf = render_text(name_text.text, "Times New Roman", 24, rotation)
        name_text.draw(screen)

    # STEP 6: DRAW THE "PLAY CARD" AND "DRAW CARD" BUTTONS
    local_player = next(
        p for p in game.game_state["player_data"]
        if p.player_id == viewer_id
    )
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
    if game.game_state["UNO!"]: draw_UNO_text(screen, game.game_state["uno_player"])
    
    # CHECK FOR WINNER
    if game.game_state["winner"] is not None: draw_win_text(screen, game.game_state["winner"])

    # CHECK IF ON CARD PICKER
    if game.game_state["player_on_card_picker"] and not game.game_state["choosing_wild_color"]:
        draw_card_picker(screen, events, game.game_state["turn_player"])

    # CHECK IF CHOOSING WILD
    if game.game_state["choosing_wild_color"]:
        draw_wild_pick(screen, events, game.game_state["wild_player"])

def draw(screen: pygame.Surface, events: list[pygame.event.Event], room):
    if game.currently_playing: draw_game_screen(screen, events)
    elif game.waiting_for_players: draw_LAN_wait(screen, events, room)
    else: draw_main_menu(screen, events)