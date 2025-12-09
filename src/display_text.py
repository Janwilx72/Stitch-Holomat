import pygame
import sys
from dotenv import load_dotenv
import os

load_dotenv()

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# Initialize Pygame
pygame.init()
BLACK = (0, 0, 0)
LIGHT_BLUE = (173, 216, 230)
WHITE = (255, 255, 255)
NAVY_BLUE = (20, 20, 40)

# Font setup
font = pygame.font.Font(None, 50)  # Font size 50 for readability

# Scrolling variables
scroll_y = 100  # Starting Y position of text
line_height = 60  # Space between lines
scroll_speed = 30  # Scroll speed per mouse wheel event

def update_screen_with_text(screen, text_content):
    """
    Takes a string of text, splits it into lines, and displays it on the screen
    with scrolling functionality.
    """
    global scroll_y

    # Convert text into a list of rendered lines
    lines = text_content.split("\n")
    rendered_text = [font.render(line, True, WHITE) for line in lines]

    running = True
    while running:
        screen.fill(BLACK)  # Clear screen

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Quit the game
                running = False
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Press ESC to exit
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    scroll_y = min(scroll_y + scroll_speed, 100)
                elif event.button == 5:  # Scroll down
                    scroll_y = max(scroll_y - scroll_speed, SCREEN_HEIGHT - len(lines) * line_height)

        # Draw the text on the screen
        y_offset = scroll_y
        for text_surface in rendered_text:
            screen.blit(text_surface, (100, y_offset))  # Text aligned from the left
            y_offset += line_height  # Move down for the next line

        pygame.display.flip()  # Update screen


def run():
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)
    pygame.display.set_caption("Scrollable Text Display")

    sample_text = """This is a scrollable text display.
    You can scroll up and down using the mouse wheel.
    This text is displayed in full-screen mode.

    Pygame supports smooth scrolling using event-based input.
    Try scrolling down to see more text.

    Press ESC to exit full-screen mode."""

    update_screen_with_text(screen, sample_text)

# Example usage with sample text
if __name__ == "__main__":
    print('Started Recipe class')
    run()

