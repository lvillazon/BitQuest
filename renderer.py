# handles screen element scaling and compositing
from constants import *
import pygame


class Renderer:

    def __init__(self, surface):
        self.scaled_surface = pygame.Surface(DISPLAY_SIZE)
        self.final_surface = surface  # where the compositing will occur

    def draw_scaled(self, image, position):
        self.scaled_surface.blit(image, position)

    def draw_native(self, image, position):
        self.final_surface.blit(image, position)

    def update(self, origin):
        self.final_surface.blit(
            pygame.transform.scale(self.scaled_surface, WINDOW_SIZE),
            origin
        )

