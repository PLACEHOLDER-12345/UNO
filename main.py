import pygame, sys
import drawing
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Set up display
screen = pygame.display.set_mode((drawing.WIDTH, drawing.HEIGHT))
pygame.display.set_caption('Pygame Boilerplate')

drawing.GAME_SCREEN = screen

# Set up the clock for managing the frame rate
fps = 60
fpsClock = pygame.time.Clock()

# Main game loop
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # Update game state

    # Draw
    drawing.draw_main_menu(screen)
    drawing.draw_grid(screen)

    # Flip the display to show the new frame
    pygame.display.flip()

    # Cap the frame rate
    fpsClock.tick(fps)