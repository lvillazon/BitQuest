import os
import pygame

from console_messages import console_msg
from constants import *

class Scenery:
    GROUND_LEVEL_OFFSET = -112  # offset for background layers

    def __init__(self, surface, level_number):
        self.surface = surface
        time_of_day, landscape = self.get_level_description(level_number)
        self.scenery_layers = self.load_scenery('assets', time_of_day,
                                                landscape)
        self.tile_width = self.scenery_layers[0]['tile'].get_rect().size[X]

    def get_level_description(self, level):
        # map level numbers to scenery types
        # these are used to look up the correct files for the background
        if level == 1:
            return 'Day', 'Field'
        elif level == 2:
            return 'Day', 'Desert'
        elif level == 3:
            return 'Day', 'Hills'
        else:
            console_msg("Invalid level number:" + str(level), 0)
            return None, None

    def load_scenery(self, folder, time_of_day, landscape):
        scenery = []
        path = '{0}/{1}/{2} {1}/'.format(folder, time_of_day, landscape)
        file_count = len(os.listdir(path))
        for i in range(file_count):
            # build the filename for each scenery image
            file_name = '{0} Layer {1:0>2}.png'.format(landscape, i+1)
            if CONSOLE_VERBOSE:
                print('loading', path + file_name)
            image = pygame.image.load(path + file_name).convert()
            # set the transparency colour on a case-by-case basis
            transparency = {
                "DayCity": (255, 255, 255),
                "DayDesert": (0, 0, 0),
                "DayField": (0, 0, 0),
                "DayForest": (255, 255, 255),
                "DayHills": (255, 255, 255),
                "DayMysterious": (255, 255, 255),
                "DaySnow": (255, 255, 255),
                "DayVolcano": (0, 0, 0),
            }
            image.set_colorkey(transparency[time_of_day+landscape],
                               pygame.RLEACCEL)
            # parallax is scaled to make distant layers *much* slower
            # I was using i-1, instead of i but this causes even the 1st
            # layer to have some parallax, which looks odd, at least for
            # the Field level.
            layer = {'tile': image, 'parallax': i ** 2 / 100}
            scenery.append(layer)
        print(len(scenery), "scenery layers loaded")
        return scenery

    def draw(self, scroll):
        self.draw_background(self.surface, scroll)

    def draw_background(self, surface, scroll):
        # draw the scenery before anything else, each frame
        # all but the last layer are used as background
        # the very last layer is drawn in front of the character

        # each layer is drawn using a relative offset, so that it will repeat
        # once it has slid completely off the screen
        for layer in self.scenery_layers:
            scenery_x = - (int(scroll[X] * layer['parallax'])
                           % self.tile_width)
            surface.blit(layer['tile'],
                         (scenery_x,
                          self.GROUND_LEVEL_OFFSET - scroll[Y]))
            # if the tile is partially off the screen, we also draw a second
            # copy after it, to make sure there is no gap between tiles.
            if scenery_x < -self.tile_width + surface.get_width():
                surface.blit(layer['tile'],
                             (scenery_x + self.tile_width,
                              self.GROUND_LEVEL_OFFSET - scroll[Y]))

    def draw_foreground(self, surface, scroll):
        # any layers that should appear in front of the character sprites
        tile = self.scenery_layers[-1]['tile']
        scenery_x = -(scroll[X] % self.tile_width)
        surface.blit(tile,
                     (scenery_x,
                      self.GROUND_LEVEL_OFFSET - scroll[Y]))
        if scenery_x < -self.tile_width + surface.get_rendered_text_width():
            surface.blit(tile,
                         (scenery_x + self.tile_width,
                          self.GROUND_LEVEL_OFFSET - scroll[Y]))

'''
    def draw_foreground(self, surface, scenery_scroll):
        # any layers that should appear in front of the character sprites
        for tile in range(len(self.scenery_layers[-1]['tiles'])):
            scenery_x = tile * 512 - scenery_scroll[X]
            surface.blit(self.scenery_layers[-1]['tiles'][tile],
                         (scenery_x,
                          self.GROUND_LEVEL_OFFSET - scenery_scroll[Y]))
'''