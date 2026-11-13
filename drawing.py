import pygame

WIDTH, HEIGHT = 800, 600

SCREEN_BG = (68, 68, 68) # #444
TEXT_COLOR = (255, 255, 255) # #fff

class Button:
    def __init__(self, x, y, width, height, text, font_face = "Arial", font_size = 36, onclick = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(font_face, font_size)
        self.text_surf = self.font.render(text, True, TEXT_COLOR)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        self.onclickFunction = onclick

    def draw(self, screen):
        mouse = pygame.mouse.get_pos()

        # check if mouse hovers over the button, and adjust the color accordingly.
        color = (192, 192, 192) if self.rect.collidepoint(mouse) else (128, 128, 128) #CCC & #808080.
        pygame.draw.rect(screen, color, self.rect)
        screen.blit(self.text_surf, self.text_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.onclickFunction:
                    self.onclickFunction()

class Textbox:
    def __init__(self, x, y, text, font_face = "Arial", font_size = 36):
        self.font = pygame.font.SysFont(font_face, font_size)
        self.text = text
        self.text_surf = self.font.render(self.text, True, TEXT_COLOR)
        self.x = x
        self.y = y

    def draw(self, screen):
        screen.blit(self.text_surf, (self.x, self.y))

def draw_grid(screen): # grid to help with positioning elements on the screen
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

def draw_main_menu(screen):
    screen.fill(SCREEN_BG)

    text_1 = Textbox(WIDTH // 2 - 100, HEIGHT // 2 - 100, "Welcome to UNO!")

    text_1.draw(screen)