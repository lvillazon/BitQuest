""" movement and animation for all the player and npc sprites """

import pygame
import contextlib
import io
from constants import *
import sprite_sheet

TILE_FILE = 'block tiles.png'
ALPHA = (255, 255, 255)

def draw_collider(surface, colour, collider, width, scroll):
    """ debug routine to show colliders"""
    rect = pygame.Rect(collider.x - scroll['x'],
                       collider.y - scroll['y'],
                       collider.width,
                       collider.height)
    pygame.draw.rect(surface, colour, rect, width)

class Moveable:
    ''' pillars, drawbridges and other objects that move
    when a trigger activates'''
    def __init__(self, block_map, world, block_range, action, distance = 0):
        # add all the blocks in the block_range to the list of blocks
        # 'owned' by this movable object
        # the range is specified as (startx, starty, width, height)
        # and distance is how far the object moves when triggered
        # all specified using the block grid units
        self.world = world  # so we can set camera_shake
        self.blocks = []
        for x in range(block_range[0], block_range[0]+block_range[2]):
            for y in range(block_range[1], block_range[1]+block_range[3]):
                self.blocks.append(block_map.get_block(x,y))

        self.action = action
        self.distance = distance
        self.activated = False
        self.current_offset = 0
        self.speed = 1

    def activate(self):
        if not self.activated:
            self.activated = True
            self.world.camera_shake = True

    def update(self):
        if (not self.activated or
                self.current_offset >= self.distance * BLOCK_SIZE):
            return
        else:
            for b in self.blocks:
                b.y += self.speed
            self.current_offset += self.speed
            if self.current_offset >= self.distance * BLOCK_SIZE:
                self.world.camera_shake = False


class Block:
    ''' any of the block tiles that define the foreground 'puzzle' blocks '''

    def __init__(self, block_tiles, type, grid_position):
        self.type = type
        self.grid_position = grid_position
        self.x = grid_position[X] * BLOCK_SIZE
        # offset of -7 to align the blocks with the bottom of the screen
        self.y = grid_position[Y] * BLOCK_SIZE - 7
        self.frame_count = 1
        if type == '1':
            self.name = 'ground type 1'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 8, BLOCK_SIZE * 1, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == 'P':
            self.name = 'left pillar top'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 12, BLOCK_SIZE * 22, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == 'p':
            self.name = 'right pillar top'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 13, BLOCK_SIZE * 22, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '[':
            self.name = 'left pillar middle'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 12, BLOCK_SIZE * 23, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == ']':
            self.name = 'right pillar middle'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 13, BLOCK_SIZE * 23, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == 'B':
            self.name = 'left pillar bottom'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 12, BLOCK_SIZE * 24, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == 'b':
            self.name = 'right pillar bottom'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 13, BLOCK_SIZE * 24, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '¬':
            self.name = 'left leaf top'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 8, BLOCK_SIZE * 23, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '{':
            self.name = 'left leaf1'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 8, BLOCK_SIZE * 24, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '|':
            self.name = 'left leaf2'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 9, BLOCK_SIZE * 24, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '/':
            self.name = 'right leaf1'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 10, BLOCK_SIZE * 24, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '}':
            self.name = 'right leaf2'
            self.image = block_tiles.image_at(
                (BLOCK_SIZE * 11, BLOCK_SIZE * 24, BLOCK_SIZE, BLOCK_SIZE),
                ALPHA)
        elif type == '=':
            self.name = 'pressure plate'
            self.frame_count = 2
            self.frames = block_tiles.images_at(
                ((BLOCK_SIZE * 25, BLOCK_SIZE * 27, BLOCK_SIZE, BLOCK_SIZE),
                 (BLOCK_SIZE * 24, BLOCK_SIZE * 27, BLOCK_SIZE, BLOCK_SIZE)),
                ALPHA)
            self.image = self.frames[0]

        # set default frame list for tiles that do not animate
        if self.frame_count == 1:
            self.frames = [self.image]

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
        self.load_grid()
        self.collidable = [b for b in self.midground_blocks
                           if b.type in '1Pp[]Bb']
        self.triggerable = [b for b in self.midground_blocks
                            if b.type in '-=']
        #self.cosmetic = [b for b in self.blocks if b.type in '¬|/']

    def load_grid(self):
        ''' TODO read in map data from a file
        Each screen has room for 15 x 11 tiles
        but a map may be arbitrarily wide
        '''
        # midground is the same layer as the player
        # collidable blocks on this layer will stop player progress
        midground_map = [
            '               ',
            '               ',
            '               ',
            '               ',
            '               ',
            '               ',
            '                                    Pp   ',
            '                                    []   ',
            ' Pp                 Pp              []   ',
            ' []                 []              []   ',
            ' Bb               = Bb   Pp=    =   Bb   ',
            '111111111111111111111111111111111111111111',
            ]

        # foreground layer is drawn on top of the player and doesn't collide
        foreground_map = [
            '               ',
            '               ',
            '               ',
            '               ',
            '               ',
            '               ',
            '               ',
            '               ',
            '                   ',
            '¬     ¬            ¬                ¬   ',
            '{|/}  {|/}         {|/}             {|    ',
        ]


        # load block tile graphics
        block_tiles = sprite_sheet.SpriteSheet('assets/' + TILE_FILE)
        # convert the map into a list of block objects, with their coords
        self.midground_blocks = []
        x = 0
        y = 0
        for row in midground_map:
            for tile in row:
                if tile != ' ':
                    self.midground_blocks.append(
                        Block(block_tiles, tile, (x, y)))
                x += 1
            x = 0
            y += 1

        self.foreground_blocks = []
        x = 0
        y = 0
        for row in foreground_map:
            for tile in row:
                if tile != ' ':
                    self.foreground_blocks.append(
                        Block(block_tiles, tile, (x, y)))
                x += 1
            x = 0
            y += 1
        # the triggers dictionary uses the grid coords of the trigger tile
        # as the key and the value is the index of the moveable object
        # that is activated
        self.triggers = {(18,10): 0,
                         (27,10): 1,
                         (32,10): 2,
                         }
        pillar1 = Moveable(self, self.world, (20, 8, 2, 3), 'down', 3)
        pillar2 = Moveable(self, self.world, (25, 10, 2, 1), 'down', 1)
        pillar3 = Moveable(self, self.world, (36, 6, 2, 5), 'down', 5)
        self.movers = [pillar1, pillar2, pillar3]

    def get_block(self, x, y):
        """returns the block at grid coord x,y"""
        for b in self.midground_blocks:
            if b.grid_position == (x, y):
                return b
        raise ValueError("No block found at " + str(x) + "," + str(y))

    def update(self, surface, scroll):
        """ draw all the blocks on the map """
        # TODO optimise to draw just the ones on screen ?

        # give any moving blocks a chance to update before we draw them
        for m in self.movers:
            m.update()

        # now draw each tile in its current location
        for b in self.midground_blocks:
            surface.blit(b.image, (b.x - scroll['x'], b.y - scroll['y']))
        for b in self.foreground_blocks:
            surface.blit(b.image, (b.x - scroll['x'], b.y - scroll['y']))

    def collision_test(self, character_rect, movement, scroll):
        """ check if this character is colliding with any of the blocks
        blocks are categorised as:
        collidable - collision physics applies to characters
        trigger - characters can overlap the block, activating the trigger
        cosmetic - no collision physics or trigger (but may animate)
        """
        direction = {'left': False,
                     'right': False,
                     'up': False,
                     'down': False,}
        if DEBUG:
            # DEBUG draw character collider in green
            draw_collider(self.world.display,
                          (0, 255, 0), character_rect, 1, scroll)

        # check for collisions with triggers
        for t in self.triggerable:
            collider = pygame.Rect(t.x,
                                   t.y,
                                   BLOCK_SIZE, BLOCK_SIZE)
            if character_rect.colliderect(collider):
                if t.grid_position in self.triggers.keys():
                    t.image = t.frames[1]  # switch to 'pressed' state
                    self.movers[self.triggers[t.grid_position]].activate()
                    if DEBUG:
                        print("trigger", self.triggers[t.grid_position], "activated!")

        # check for collisions with solid objects
        collisions = {'left': None,
                      'right': None,
                      'up': None,
                      'down': None}
        # find the first colliding block in each direction
        for b in self.collidable:
            collider = pygame.Rect(b.x,
                                   b.y,
                                   BLOCK_SIZE, BLOCK_SIZE)
            if DEBUG:
                # DEBUG draw block colliders in yellow
                draw_collider(self.world.display,
                              (255, 255, 0), collider, 1, scroll)

            if character_rect.colliderect(collider):
                # just because the rectangles overlap, doesn't necessarily
                # mean we want to call it a collision. We only count collisions
                # where the character is moving towards the block
                # this prevents characters from getting stuck in blocks
                if (movement[X] > 0 and
                    character_rect.centerx < collider.centerx and
                    (character_rect.bottom > collider.top
                     + COLLIDE_THRESHOLD) and
                    collisions['right'] == None
                    ):
                    collisions['right'] = collider

                if movement[X] < 0:
                    if (character_rect.left <= collider.right and
                    (character_rect.bottom > collider.top
                     + COLLIDE_THRESHOLD) and
                        collisions['left'] == None
                        ):
                        collisions['left'] = collider
                        # DEBUG draw active colliders in red
                        if DEBUG:
                            draw_collider(self.world.display,
                                          (255, 0, 0), collider, 0, scroll)

                # TODO may need similar logic for Y movement, to allow
                # falling when you are next to a wall
                if (movement[Y] < 0 and
                        character_rect.top <= collider.bottom and
                        collisions['up'] == None):
                    collisions['up'] = collider

                if (movement[Y] > 0 and
                        character_rect.bottom >= collider.top and
                        collisions['down'] == None):
                    collisions['down'] = collider

                    # DEBUG draw active colliders in red
#                    if DEBUG:
#                        draw_collider(self.world.display,
#                                      (255, 0, 0), collider, 0, scroll)

        return collisions