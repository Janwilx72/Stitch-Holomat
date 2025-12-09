import os
import threading

import pygame

from core.camera.camera_manager import CameraManager
from core.assistant_module import jarvis


def start_jarvis():
    jarvis.init_jarvis()


def start_home(screen, camera_manager):
    from features.home.home_screen import run_home_screen
    run_home_screen(screen, camera_manager)


if __name__ == '__main__':
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

    os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = "1"
    # os.environ['SDL_VIDEO_WINDOW_POS'] = '-3440,0'

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption('Home Screen')

    camera_manager = CameraManager('./M.npy', SCREEN_WIDTH, SCREEN_HEIGHT)

    # thread1 = threading.Thread(target=start_home, args=(screen, camera_manager))
    thread2 = threading.Thread(target=start_jarvis)

    # Start threads
    # thread1.start()
    thread2.start()

    # Optionally, wait for threads to complete (infinite loop here means you may not want to join)
    # thread1.join()
    # thread2.join()

    # start_jarvis()
    start_home(screen, camera_manager)

