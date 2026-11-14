# This file contains helpers to draw elements on the screen.

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

    pass # TODO

def draw(screen: pygame.Surface, events: list[pygame.event.Event]):
    if game.currently_playing: draw_game_screen(screen, events)
    else: draw_main_menu(screen, events)