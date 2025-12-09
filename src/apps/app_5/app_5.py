import sys
import math
import time
import pygame

# Import your existing AppCircle class and constants
# (Adjust the import paths based on your project structure.)
from core.data.constants import (
    SCREEN_SIZE,  # e.g., (1920, 1080)
    ANIMATION_DURATION,  # e.g., 0.5
    NAVY_BLUE,
    LIGHT_BLUE
)
from widgets.app_circle import AppCircle

pygame.init()

# Example list of cooking categories
CATEGORIES = ["Lamb", "Beef", "Pasta", "Seafood", "Mince"]


def create_category_circles():
    """
    Creates a list of AppCircle instances arranged in a circle around screen center.
    Each circle is labeled with a category and starts invisible at screen center,
    ready to animate outward if desired.
    """
    circles = []
    center_x, center_y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2

    distribution_radius = 250  # distance from center to final position
    circle_radius = 85         # radius of each circle

    # Place each category in a circular layout
    for i, category in enumerate(CATEGORIES):
        # Compute final (x, y) for the circle on the circumference
        angle = 2 * math.pi * i / len(CATEGORIES)
        final_x = center_x + int(distribution_radius * math.cos(angle))
        final_y = center_y + int(distribution_radius * math.sin(angle))

        # Create the AppCircle, starting at the center
        circle = AppCircle(
            center=(center_x, center_y),
            radius=circle_radius,
            app_index=i + 1,          # or any unique ID
            final_pos=(final_x, final_y),
            is_main=False,            # so text defaults to "App X"
            hover_time=5
        )
        # Override the default text with our custom category
        circle.text = category
        # Make them visible immediately (so they'll animate out)
        circle.visible = True
        # Trigger animation if you want them to move out from center at startup
        circle.animation_start_time = time.time()
        circle.is_animating = True

        circles.append(circle)

    return circles


def main():
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Circular Cooking Categories")

    # Create all our category circles
    circles = create_category_circles()

    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left-click detection; check if any circle is hovered
                for circle in circles:
                    if circle.is_hovered_flag:
                        print(f"You clicked on: {circle.text}")

        # Clear the screen
        screen.fill((0, 0, 0))

        # Update hover states & draw each circle
        for circle in circles:
            # Check if mouse is inside this circle
            if circle.is_hovered(mouse_pos):
                circle.is_hovered_flag = True
                # Start hover timer if first time hovered
                if circle.hover_time == 0:
                    circle.hover_time = time.time()
            else:
                circle.is_hovered_flag = False
                circle.hover_time = 0  # reset hover timer if not hovered

            circle.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
