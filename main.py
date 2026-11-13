import pygame, sys

import drawing
import comms
import game
import uno_mechanics

from pygame.locals import *

# Initialize Pygame
pygame.init()

# Set up display
screen = pygame.display.set_mode((drawing.WIDTH, drawing.HEIGHT))
pygame.display.set_caption('Pygame Boilerplate')

# Set up the clock for managing the frame rate
FPS = 60
GAME_CLOCK = pygame.time.Clock()

# Main game loop
while True:
    events = pygame.event.get()

    # Handle events
    for event in events:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # Update game state

    # Draw
    drawing.draw_main_menu(screen, events)
    drawing.draw_grid(screen)

    # Flip the display to show the new frame
    pygame.display.flip()

    # Cap the frame rate
    GAME_CLOCK.tick(FPS)