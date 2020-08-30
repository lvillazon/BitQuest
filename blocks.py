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
    rect = pygame.Rect(collider.x - scroll[X],
                       collider.y - scroll[Y],
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
        self.block_range = block_range  # makes it easier when saving the map
        self.blocks = []
        for x in range(block_range[0], block_range[0]+block_range[2]):
            for y in range(block_range[1], block_range[1]+block_range[3]):
                self.blocks.append(block_map.get_block(
                    block_map.midground_blocks, x, y))

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
        self.y = grid_position[Y] * BLOCK_SIZE

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
        elif type == '-':
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
        else:
            print("UNRECOGNISED BLOCK CODE:", type)

        # set default frame list for tiles that do not animate
        if self.frame_count == 1:
            self.frames = [self.image]

    def is_collidable(self):
        if self.type in '1Pp[]Bb':
            return True
        else:
            return False

    def is_trigger(self):
        if self.type in '-=':
            return True
        else:
            return False

class BlockMap:

    def __init__(self, world):
        self.world = world  # link back to the world game state

        # editing cursor (used when editing the map)
        self.cursor = [5,5]
        self.cursor_rect = pygame.Rect(self.cursor[X] * BLOCK_SIZE,
                                       self.cursor[Y] * BLOCK_SIZE,
                                       BLOCK_SIZE -1, BLOCK_SIZE -1)

        # pillars
        # a complete pillar is
        #
        #    Pp
        #   ¬[]
        #   |Bb/
        self.block_tiles = sprite_sheet.SpriteSheet('assets/' + TILE_FILE)
        self.load_grid()
        self.editor_pallette = '1Pb[]Bb='
        self.current_editor_tile = self.editor_pallette[0]  # set the default starting tile for the editor

    def save_grid(self, level=1):
        """save current grid map to the level file
        this function is only accessible in map editor mode"""
        # TODO add save dialogue to change name/folder

        # find size of the map by looking for the largest x & y coords
        max_x = 0
        max_y = 0
        for b in self.collidable:
            if b.grid_position[X] > max_x:
                max_x = b.grid_position[X]
            if b.grid_position[Y] > max_y:
                max_y = b.grid_position[Y]

        # write this map to the file
        file_name = 'BitQuest_level' + str(level) + '.txt'
        preamble = \
            "Level data is split into 4 sections, each section ends with " \
            "### on its own line:\n" \
            "   1. This section is for comments only and is ignored.\n" \
            "   2. The midground section shows the arrangements of " \
            "collidable blocks and triggers.\n" \
            "   3. Foreground layer is drawn on top of the player and " \
            "doesn't collide.\n" \
            "   4. The next section defines the blocks that move when " \
            "triggered.\n" \
            "   5. This section defines the trigger locations, as x, y and " \
            "block group number, each on their own line.\n"
        delimiter = "###\n"
        with open(file_name, 'w') as file:
            file.write(preamble)  # section 1
            file.write(delimiter)
            # sections 2 and 3
            for blocks in (self.midground_blocks, self.foreground_blocks):
                for y in range(max_y + 1):
                    for x in range(max_x + 1):
                        b = self.get_block(blocks, x, y)
                        if b:
                            file.write(b.type)
                        else:  # b == None if not found
                            file.write(' ')
                    file.write('\n')  # new line
                file.write(delimiter)

            # section 4
            for m in self.movers:
                for br in m.block_range:
                    file.write(str(br) + ', ')
                file.write(m.action + ', ')
                file.write(str(m.distance) + '\n')
            file.write(delimiter)

            # section 5
            for t in self.triggers:
                file.write(str(t[0]) + ', ')
                file.write(str(t[1]) + ', ')
                file.write(str(self.triggers[t]) + '\n')
            file.write(delimiter)

    def load_grid(self, level=1):
        """read in map data from the level file
        Each screen has room for 15 x 11 tiles
        but a map may be arbitrarily wide
        """
        # midground is the same layer as the player
        # collidable blocks on this layer will stop player progress

        file_name = 'BitQuest_level' + str(level) + '.txt'
        with open(file_name, 'r') as file:
            lines = file.readlines()
            level_data = []
            for file_line in lines:
                level_data.append(file_line[:-1])

        # parse the raw level file into the midground, foreground,
        # block and trigger info
        # the level data is divided into sections, using ### between them
        # the start of the level is ignored, so it can be used for comments
        i = level_data.index('###') + 1  # marks the actual level data

        midground_map = []
        while i < len(level_data) and level_data[i] != '###':
            midground_map.append(level_data[i])
            i += 1

        foreground_map = []
        i += 1  # skip over the ### section delimiter
        while i < len(level_data) and level_data[i] != '###':
            foreground_map.append(level_data[i])
            i += 1

        # load block tile graphics for each block in the map
        # convert the map into a list of block objects, with their coords
        self.midground_blocks = []
        x = 0
        y = 0
        for row in midground_map:
            for tile in row:
                if tile != ' ':
                    self.midground_blocks.append(
                        Block(self.block_tiles, tile, (x, y)))
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
                        Block(self.block_tiles, tile, (x, y)))
                x += 1
            x = 0
            y += 1

        # the moveable objects are groups of blocks that all move together
        # in response to a trigger
        # they are defined by their top, left, width & height values
        # in the block coordinate system
        # plus a move direction as a string
        # and a number of blocks to move
        self.movers = []
        i += 1  # skip over the ### section delimiter
        while i < len(level_data) and level_data[i] != '###':
            values = level_data[i].split(',')
            mover = Moveable(self, self.world,
                             (int(values[0]), int(values[1]),
                              int(values[2]), int(values[3])),
                             values[4],
                             int(values[5]))
            self.movers.append(mover)
            i += 1

        # the triggers dictionary uses the grid coords of the trigger tile
        # as the key and the value is the index of the moveable object
        # that is activated
        self.triggers = {}
        i += 1  # skip over the ### section delimiter
        while i < len(level_data) and level_data[i] != '###':
            values = level_data[i].split(',')
            print(values)
            self.triggers[(int(values[0]), int(values[1]))] = int(values[2])
            i += 1

    def get_block(self, blocklist, x, y):
        """returns the block at grid coord x,y"""
        for b in blocklist:
            if b.grid_position == (x, y):
                return b
        if DEBUG:
            print("No block found at " + str(x) + "," + str(y))
        return None

    def update(self, surface, scroll):
        """ draw all the blocks on the map """
        # TODO optimise to draw just the ones on screen ?

        # give any moving blocks a chance to update before we draw them
        for m in self.movers:
            m.update()

        # now draw each tile in its current location
        for b in self.midground_blocks:
            surface.blit(b.image, (b.x - scroll[X], b.y - scroll[Y]))
        for b in self.foreground_blocks:
            surface.blit(b.image, (b.x - scroll[X], b.y - scroll[Y]))

    def draw_grid(self, surface, scroll):
        """ overlays a grid to show the block spacing """
        grid_colour = self.world.editor.get_bg_color()
        offset = scroll[X] % BLOCK_SIZE
        for x in range(-offset, DISPLAY_SIZE[X] - offset, BLOCK_SIZE):
            pygame.draw.line(surface, grid_colour, (x, 0),
                             (x, DISPLAY_SIZE[Y]))
        offset = scroll[Y] % BLOCK_SIZE
        for y in range(-offset, DISPLAY_SIZE[Y], BLOCK_SIZE):
            pygame.draw.line(surface, grid_colour, (0, y),
                             (DISPLAY_SIZE[X], y))
        if MAP_EDITOR_MODE:
            self.cursor_rect.x = (self.cursor[X] * BLOCK_SIZE) - scroll[X] + 1
            self.cursor_rect.y = (self.cursor[Y] * BLOCK_SIZE) - scroll[Y] + 1
            pygame.draw.rect(surface, (255,255,255),
                             self.cursor_rect, 1)  # highlight cursor

    def cursor_right(self):
        self.cursor[X] += 1

    def cursor_left(self):
        if self.cursor[X] > 0:
            self.cursor[X] -= 1

    def cursor_up(self):
        if self.cursor[Y] > 0:
            self.cursor[Y] -= 1

    def cursor_down(self):
        self.cursor[Y] += 1

    def change_block(self):
        """ if there is no block at the current grid cursor location, this adds the 1st block in the pallette
        otherwise, it swaps the current block for the next one in the pallette, wrapping around to the first."""
        existing_block = self.get_block(self.midground_blocks, self.cursor[X], self.cursor[Y])
        if existing_block == None:
            b = Block(self.block_tiles, self.current_editor_tile, self.cursor)
            self.midground_blocks.append(b)
        else:  # cycle to the next block in the pallette
            self.current_editor_tile = (self.current_editor_tile + 1) % len(self.editor_pallette)
            existing_block.type = self.current_editor_tile
            # TODO this only changes the symbol - it doesn't change the image
            # we will need a pallette of actual blocks, rather than just the tile symbols

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
        for t in self.midground_blocks:
            if t.is_trigger():
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
        for b in self.midground_blocks:
            if b.is_collidable():
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