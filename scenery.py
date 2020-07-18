import pygame


class Scenery:
    GROUND_LEVEL_OFFSET = -86  # offset for background layers

    def __init__(self, time_of_day, landscape):
        self.scenery_layers = self.load_scenery('assets', time_of_day,
                                                landscape)

    def load_scenery(self, folder, time_of_day, landscape):
        scenery = []
        # build the folder name for this set of scenery images
        path = '{0}/{1}/{2}/'.format(folder, time_of_day, landscape)
        for i in range(1, 11):
            # build the filename for each scenery image
            file_name = '{0} Layer {1:0>2}.png'.format(landscape, i)
            print('loading', path + file_name)
            image = pygame.image.load(path + file_name).convert()
            # use white as the alpha transparency color
            image.set_colorkey((0, 0, 0), pygame.RLEACCEL)
            tiles = []
            for j in range(10):
                tiles.append(image)
            # parallax is scaled to make distant layers *much* slower
            layer = {'tiles': tiles, 'parallax': (i - 1) ** 2 / 100}
            scenery.append(layer)
        print("Layers = ", len(scenery))
        return scenery

    def draw_background(self, surface, scroll):
        # draw the scenery before anything else, each frame
        # all but the last layer are used as background
        # the very last layer is drawn in front of the character

        # this version uses a single call to blits()
        # but doesn't allow for new scenery tiles scrolling in from the right
        # display.blits((layer[IMAGE],
        #               (WORLD_START - int(scroll[X] * layer[PARALLAX]),
        #                GROUND_LEVEL_OFFSET - scroll[Y]))
        #              for layer in scenery_layers[0:-1])

        # this version blits multiple tiles for each layer
        # to make sure there is always another one available to scroll in
        # hopefully pygame won't actually render the ones off-screen
        for layer in self.scenery_layers[0:-1]:
            for tile in range(len(layer['tiles'])):
                scenery_x = tile * 512 - int(scroll['x'] * layer['parallax'])
                surface.blit(layer['tiles'][tile],
                             (scenery_x,
                              self.GROUND_LEVEL_OFFSET - scroll['y']))

    def draw_foreground(self, surface, scenery_scroll):
        # any layers that should appear in front of the character sprites
        for tile in range(len(self.scenery_layers[-1]['tiles'])):
            scenery_x = tile * 512 - scenery_scroll['x']
            surface.blit(self.scenery_layers[-1]['tiles'][tile],
                         (scenery_x,
                          self.GROUND_LEVEL_OFFSET - scenery_scroll['y']))

