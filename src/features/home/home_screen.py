import asyncio
from ctypes import Union

import pygame
from pygame import mixer, Surface, SurfaceType
import time
import os
import sys
import math
from core.camera.camera_manager import CameraManager
# from dotenv import load_dotenv

# load_dotenv()

# Initialize Pygame
pygame.init()
# Initialize the mixer
mixer.init()

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

NAVY_BLUE = (20, 20, 40)
LIGHT_BLUE = (173, 216, 230)
HOME_TOGGLE_DELAY = 1.0  # Delay in seconds for home button toggle

# Distance threshold for pinch detection (pixel distance between thumb & index)
PINCH_THRESHOLD = 100
# Animation duration in seconds (same as the 0.5 sec used in the code for circle movement)
ANIMATION_DURATION = 0.5

JARVIS_COMMANDS_MAP = {
    'home_command': False,
    'jarvis_app_index': 0
}


def play_sound(file_path):
    mixer.music.load(file_path)
    mixer.music.play()

class AppCircle:
    def __init__(self, center, radius, app_index, final_pos, is_main=False):
        self.center = center
        self.radius = radius
        self.app_index = app_index
        self.text = 'Home' if is_main else f'App {app_index}'
        self.hover_time = 0
        self.is_hovered_flag = False
        self.is_main = is_main
        self.visible = is_main
        self.final_pos = final_pos
        self.animation_start_time = None
        self.is_animating = False
        self.image = self.load_image()

    def load_image(self):
        if not self.is_main:
            image_path = f'./apps/app_{self.app_index}/app_{self.app_index}.jpg'
            if os.path.exists(image_path):
                image = pygame.image.load(image_path)
                return pygame.transform.scale(image, (2 * self.radius, 2 * self.radius))
        return None

    def draw(self, screen):
        # If circle is hovered, slightly enlarge radius over time
        if self.is_hovered_flag:
            current_radius = self.radius + min((time.time() - self.hover_time) * 10, self.radius * 0.5)
        else:
            current_radius = self.radius

        # Animate movement from center to final position (and back)
        if self.animation_start_time is not None:
            elapsed_time = time.time() - self.animation_start_time
            if elapsed_time < ANIMATION_DURATION:  # 0.5 seconds
                t = elapsed_time / ANIMATION_DURATION
                if self.visible:
                    self.center = (
                        int((1 - t) * SCREEN_SIZE[0] // 2 + t * self.final_pos[0]),
                        int((1 - t) * SCREEN_SIZE[1] // 2 + t * self.final_pos[1])
                    )
                else:
                    self.center = (
                        int(t * SCREEN_SIZE[0] // 2 + (1 - t) * self.final_pos[0]),
                        int(t * SCREEN_SIZE[1] // 2 + (1 - t) * self.final_pos[1])
                    )
            else:
                self.center = self.final_pos if self.visible else (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2)
                self.animation_start_time = None
                self.is_animating = False

        # Draw if visible or if still animating
        if self.visible or self.is_animating:
            if self.image:
                image_width, image_height = self.image.get_size()
                top_left = (self.center[0] - image_width // 2, self.center[1] - image_height // 2)
                screen.blit(self.image, top_left)
            else:
                pygame.draw.circle(screen, NAVY_BLUE, self.center, int(current_radius))
            pygame.draw.circle(screen, LIGHT_BLUE, self.center, int(current_radius), 5)

            # Draw text label if no image
            if not self.image:
                font = pygame.font.Font(None, 32)
                text_surface = font.render(self.text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=self.center)
                screen.blit(text_surface, text_rect)

    def is_hovered(self, pos):
        return math.hypot(pos[0] - self.center[0], pos[1] - self.center[1]) <= self.radius

def create_circles():
    circles = []
    num_circles = 8
    center_x, center_y = SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2
    main_circle_radius = 100
    app_circle_radius = 75
    distance = 250

    # Main "Home" circle
    main_circle = AppCircle((center_x, center_y), main_circle_radius, 0, (center_x, center_y), is_main=True)
    circles.append(main_circle)

    # Surrounding app circles
    angle_step = 360 / num_circles
    for i in range(num_circles):
        angle = math.radians(angle_step * i)
        x = center_x + int(distance * math.cos(angle))
        y = center_y + int(distance * math.sin(angle))
        circles.append(AppCircle((center_x, center_y), app_circle_radius, i + 1, (x, y)))
    return circles

def all_animations_completed(circles):
    """
    Returns True only if none of the circles are currently animating.
    A circle is done animating if circle.animation_start_time is None
    and circle.is_animating is False.
    """
    return all(not circle.is_animating for circle in circles)





def run_home_screen(screen, camera_manager):
    global JARVIS_COMMANDS_MAP

    circles = create_circles()
    main_circle = circles[0]
    running = True
    apps_visible = False
    last_toggle_time = 0

    # play_sound("./audio/startup.wav")

    while running:
        if not camera_manager.update():
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                camera_manager.release()
                sys.exit()

        screen.fill((0, 0, 0))

        # Draw all circles first
        for circle in circles:
            circle.is_hovered_flag = False
            circle.draw(screen)

        hovered_circle = None  # Track which circle is hovered this frame

        # Get landmarks from camera
        transformed_landmarks = camera_manager.get_transformed_landmarks()

        if JARVIS_COMMANDS_MAP['jarvis_app_index'] > 0:
            print('Voice App Launch')
            index = JARVIS_COMMANDS_MAP['jarvis_app_index']
            run_app_with_index(index, screen, camera_manager)
            JARVIS_COMMANDS_MAP['jarvis_app_index'] = 0
        else:
            if transformed_landmarks:
                # Assuming one hand for simplicity, or take the first hand
                for transformed_coords in transformed_landmarks:
                    # Index finger tip
                    index_tip = transformed_coords[camera_manager.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    screen_x = int(index_tip[0])
                    screen_y = int(index_tip[1])

                    # Thumb tip (for pinch detection)
                    thumb_tip = transformed_coords[camera_manager.mp_hands.HandLandmark.THUMB_TIP]
                    thumb_x = int(thumb_tip[0])
                    thumb_y = int(thumb_tip[1])

                    # Draw the index finger cursor
                    index_finger_pos = (screen_x, screen_y)
                    pygame.draw.circle(screen, LIGHT_BLUE, index_finger_pos, 15, 3)

                    # Check hover state
                    for circle in circles:
                        if circle.is_hovered(index_finger_pos):
                            circle.is_hovered_flag = True
                            hovered_circle = circle
                            # Record the first time we hovered (for animation)
                            if circle.hover_time == 0:
                                circle.hover_time = time.time()
                        else:
                            # Reset hover_time if not hovered
                            if not circle.is_main:
                                # Only reset if circle is visible to avoid messing up the main circle
                                if circle.visible:
                                    circle.hover_time = 0

                    # Check for pinch (distance between index tip & thumb tip)
                    dx = thumb_x - screen_x
                    dy = thumb_y - screen_y
                    distance = math.hypot(dx, dy)
                    is_pinched = (distance < PINCH_THRESHOLD)

                    # Only allow interaction if no circle is still animating
                    if JARVIS_COMMANDS_MAP["home_command"] is True or (hovered_circle and is_pinched and all_animations_completed(circles)):
                        current_time = time.time()
                        print('JARVIS HOME COMMAND: ', JARVIS_COMMANDS_MAP)

                        # If it's the Home circle
                        if JARVIS_COMMANDS_MAP["home_command"] is True or hovered_circle.is_main:
                            # set_jarvis_home_command()
                            JARVIS_COMMANDS_MAP["home_command"] = False
                            # Toggle app visibility (if enough time passed)
                            if current_time - last_toggle_time > HOME_TOGGLE_DELAY:
                                apps_visible = not apps_visible
                                print(f"Toggling apps visibility to: {apps_visible}")
                                play_sound("./audio/home.wav")
                                last_toggle_time = current_time

                                for app_circle in circles[1:]:
                                    app_circle.visible = apps_visible
                                    app_circle.animation_start_time = time.time()
                                    app_circle.is_animating = True

                        # Otherwise, an app circle
                        else:
                            # Launch an app if visible
                            if hovered_circle.visible and apps_visible:
                                run_app_with_index(hovered_circle.app_index, screen, camera_manager)
                                # try:
                                #     app_name = f'app_{hovered_circle.app_index}.app_{hovered_circle.app_index}'
                                #     print(f"Launching app: {app_name}")
                                #     mod = __import__(f'apps.{app_name}', fromlist=[''])
                                #     play_sound("./audio/confirmation.wav")
                                #     # Pass camera_manager to the app
                                #     mod.run(screen, camera_manager)
                                # except ModuleNotFoundError:
                                #     print(f"Module 'apps.{app_name}' not found.")
                                #     play_sound("./audio/reject.wav")


        # Redraw main circle on top (optional)
        main_circle.draw(screen)

        pygame.display.flip()
        pygame.time.delay(50)


def run_app_with_index(app_index, screen, camera_manager):
    try:
        app_name = f'app_{app_index}.app_{app_index}'
        print(f"Launching app: {app_name}")
        mod = __import__(f'apps.{app_name}', fromlist=[''])
        play_sound("./audio/confirmation.wav")

        # Pass camera_manager to the app
        mod.run(screen, camera_manager)
    except ModuleNotFoundError:
        print(f"Module 'apps.{app_name}' not found.")
        play_sound("./audio/reject.wav")


if __name__ == '__main__':
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

    os.environ['SDL_VIDEO_WINDOW_POS'] = '-3440,0'
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption('Home Screen')

    camera_manager = CameraManager('./M.npy', SCREEN_WIDTH, SCREEN_HEIGHT)
    run_home_screen(screen, camera_manager)





