""" movement and animation for all the player and npc sprites """

import pygame
import contextlib
import io
from constants import *
import sprite_sheet

BLOCK_SIZE = 16  # size in pixels of a the block 'grid'
TILE_FILE = 'block tiles.png'
ALPHA = (255, 255, 255)

class Moveable:
    ''' pillars, drawbridges and other objects that move
    when a trigger activates'''
    def __init__(self, blocks, action, distance = 0):
        self.blocks = blocks
        self.action = action
        self.distance = distance
        self.activated = False
        self.speed = 1

    def activate(self):
        self.activated = True

    def update(self):
        if not self.activated:
            return

class Block:
    ''' any of the block tiles that define the foreground 'puzzle' blocks '''

    def __init__(self, block_tiles, type, grid_position):
        self.type = type
        self.grid_position = grid_position
        self.x = grid_position[X] * BLOCK_SIZE
        # offset of -7 to align the blocks with the bottom of the screen
        self.y = grid_position[Y] * BLOCK_SIZE - 7
        if type == 'P':
            self.name = 'left pillar top'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 9, BLOCK_SIZE * 25, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == 'p':
            self.name = 'right pillar top'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 10, BLOCK_SIZE * 25, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '[':
            self.name = 'left pillar middle'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 9, BLOCK_SIZE * 26, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == ']':
            self.name = 'right pillar middle'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 10, BLOCK_SIZE * 26, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '¬':
            self.name = 'left pillar leaf top'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 8, BLOCK_SIZE * 26, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '|':
            self.name = 'left pillar leaf bottom'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 8, BLOCK_SIZE * 27, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == 'B':
            self.name = 'left pillar bottom'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 9, BLOCK_SIZE * 27, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == 'b':
            self.name = 'right pillar bottom'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 10, BLOCK_SIZE * 27, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '/':
            self.name = 'right pillar leaf'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 11, BLOCK_SIZE * 27, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '-':
            self.name = 'pressure plate down'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 24, BLOCK_SIZE * 27, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '=':
            self.name = 'pressure plate up'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 25, BLOCK_SIZE * 27, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)


class BlockMap:

    def __init__(self, world):
        self.world = world  # link back to the world game state
        self.blocks = []

        # pillars
        # a complete pillar is
        #
        #    Pp
        #   ¬[]
        #   |Bb/
        self.blocks = self.load_grid()
        self.collidable = [b for b in self.blocks if b.type in 'Pp[]Bb']
        self.triggerable = [b for b in self.blocks if b.type in '-=']
        self.cosmetic = [b for b in self.blocks if b.type in '¬|/']

    def load_grid(self):
        ''' TODO read in map data from a file
        Each screen has room for 15 x 11 tiles
        but a map may be arbitrarily wide
        '''
        map =  ['               ',
                '               ',
                '               ',
                '               ',
                '               ',
                '               ',
                '               ',
                '               ',
                ' Pp            ',
                '¬[]   ¬         ',
                '|Bb/  |/      -=Pp    ',
                ]
        # load block tile graphics
        block_tiles = sprite_sheet.SpriteSheet('assets/' + TILE_FILE)
        # convert the map into a list of block objects, with their coords
        blocks = []
        x = 0
        y = 0
        for row in map:
            for tile in row:
                if tile != ' ':
                    blocks.append(Block(block_tiles, tile, (x, y)))
                x += 1
            x = 0
            y += 1

        return blocks

        # obstacles is a list of
        # triggers is a dictionary that uses the block coordinates
        # of the trigger as the key. The value is a list of tuples,
        # each tuple represents an action performed on a block:
        # the first value in the tuple is the x,y block coordinates
        # then an action: left, right, up, down, appear, disappear
        # then a number of spaces


    def update(self, surface, scroll):
        """ draw all the blocks on the map """
        # TODO optimise to draw just the ones on screen ?
        for b in self.blocks:
            surface.blit(b.image, (b.x - scroll['x'], b.y - scroll['y']))

    def collision_test(self, character_rect, movement, scroll):
        """ check if this character is colliding with any of the blocks
        blocks are categorised as:
        collidable - collision physics applies to characters
        trigger - characters can overlap the block, activating the trigger
        cosmetic - no collision physics or trigger (but may animate)
        """
        if DEBUG:
            # DEBUG draw character collider in green
            pygame.draw.rect(self.world.display, (0, 255, 0),
                             character_rect, 1)
        collisions = []
        for b in self.collidable:
            collider = pygame.Rect(b.x - scroll['x'],
                                   b.y - scroll['y'],
                                   BLOCK_SIZE, BLOCK_SIZE)
            if DEBUG:
                # DEBUG draw block colliders in red
                pygame.draw.rect(self.world.display, (255, 0, 0),
                                 collider, 1)

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