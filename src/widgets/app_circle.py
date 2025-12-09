import math
import os
import time

import pygame

from core.data.constants import ANIMATION_DURATION, SCREEN_SIZE, NAVY_BLUE, LIGHT_BLUE


class AppCircle:
    def __init__(self, center, radius, app_index, final_pos, is_main=False, hover_time=0):
        self.center = center
        self.radius = radius
        self.app_index = app_index
        self.text = 'Home' if is_main else f'App {app_index}'
        self.hover_time = hover_time
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
            # current_radius = self.radius + min((time.time() - self.hover_time) * 10, self.radius * 0.5)
            # Increase the growth rate from 10 to 30
            current_radius = self.radius + min((time.time() - self.hover_time) * 60, self.radius * 0.25)
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