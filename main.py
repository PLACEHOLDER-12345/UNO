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
pygame.display.set_caption('UNO Game')

# Set up the clock for managing the frame rate
FPS = 30
GAME_CLOCK = pygame.time.Clock()
WIN_DISPLAY_DURATION = 3000
winner_display_started_at = None

# Main game loop
while True:
    events = pygame.event.get()

    comms.process_server_messages()

    # Handle events
    for event in events:
        if event.type == QUIT:
            if comms.is_host(): comms.close_host()

            pygame.quit()
            sys.exit()

    # Update game state
    game.update()

    # Draw
    drawing.draw(screen, events, comms.current_room)
    drawing.draw_grid(screen)

    # Flip the display to show the new frame
    pygame.display.flip()

    if game.game_state["winner"] is not None:
        if winner_display_started_at is None:
            winner_display_started_at = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - winner_display_started_at >= WIN_DISPLAY_DURATION:
            pygame.quit()
            sys.exit()

    # Cap the frame rate
    GAME_CLOCK.tick(FPS)