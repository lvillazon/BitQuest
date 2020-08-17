""" movement and animation for all the player and npc sprites """

import pygame
import contextlib
import io
from constants import *
import sprite_sheet

class Blocks:
    BLOCK_SIZE = 16  # size in pixels of a the block 'grid'
    TILE_FILE = 'block tiles.png'
    ALPHA = (255,255,255)

    def __init__(self, world):
        self.world = world  # link back to the world game state
        # load block tile graphics
        self.block_tiles = \
            sprite_sheet.SpriteSheet('assets/' + self.TILE_FILE)
        self.blocks = {}
#        self.blockA = self.block_tiles.image_at((16, 32, self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)

        # pillars
        # a complete pillar is
        #
        #    Pp
        #   ¬[]
        #   |Bb/
        self.blocks['P'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 9, self.BLOCK_SIZE * 25,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks['p'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 10, self.BLOCK_SIZE * 25,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks['['] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 9, self.BLOCK_SIZE * 26,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks[']'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 10, self.BLOCK_SIZE * 26,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks['¬'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 8, self.BLOCK_SIZE * 26,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks['|'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 8, self.BLOCK_SIZE * 27,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks['B'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 9, self.BLOCK_SIZE * 27,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks['b'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 10, self.BLOCK_SIZE * 27,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks['/'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 11, self.BLOCK_SIZE * 27,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)

        # pressure plate
        self.blocks['-'] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 24, self.BLOCK_SIZE * 27,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)
        self.blocks['='] = self.pillar_top = self.block_tiles.image_at(
            (self.BLOCK_SIZE * 25, self.BLOCK_SIZE * 27,
             self.BLOCK_SIZE, self.BLOCK_SIZE), self.ALPHA)

        self.load_grid()
        self.colliders = []


    def load_grid(self):
        ''' TODO read in map data from a file
        Each screen has room for 15 x 11 tiles
        but a map may be arbitrarily wide
        '''
        self.map = ['               ',
                    '               ',
                    '               ',
                    '               ',
                    '               ',
                    '               ',
                    '               ',
                    '               ',
                    ' Pp            ',
                    '¬[]            ',
                    '|Bb/          -=Pp    ',
                    ]


    def update(self, surface, scroll):
        ''' draw all the blocks on the map
        TODO optimise to draw just the ones on screen ?'''
        x = -scroll['x']
        y = -7 - scroll['y']
        self.colliders = []
        for row in self.map:
            for tile in row:
                if tile != ' ':
                    surface.blit(self.blocks[tile], (x, y))
                    collider = pygame.Rect(x, y,
                                           self.BLOCK_SIZE, self.BLOCK_SIZE)
                    self.colliders.append(collider)
                    if DEBUG:
                        # DEBUG draw collider in red
                        pygame.draw.rect(surface, (255,0,0), collider, 1)
                x += self.BLOCK_SIZE
            x = -scroll['x']
            y += self.BLOCK_SIZE

    def collision_test(self, character_rect, movement):
        ''' check if this character is colliding with any of the blocks'''
        if DEBUG:
            # DEBUG draw character collider in green
            pygame.draw.rect(self.world.display, (0, 255, 0),
                             character_rect, 1)
        collisions = []
        for collider in self.colliders:
            if character_rect.colliderect(collider):
                # just because the rectangles overlap, doesn't necessarily
                # mean we want to call it a collision. We only count collisions
                # where the character is moving towards the block
                # this prevents characters from getting stuck in blocks
                if (movement[X] > 0 and
                                character_rect.centerx < collider.centerx):
                    collisions.append(collider)

                if (movement[X] < 0 and
                                character_rect.centerx > collider.centerx):
                    collisions.append(collider)

        return collisions