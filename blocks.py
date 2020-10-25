""" movement and animation for all the player and npc sprites """

import pygame
from console_messages import console_msg
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
    """ pillars, drawbridges and other objects that move
    when a trigger activates"""

    def __init__(self, block_map, world, block_range, action, distance=0):
        # add all the blocks in the block_range to the list of blocks
        # 'owned' by this movable object
        # the range is specified as (startx, starty, width, height)
        # and distance is how far the object moves when triggered
        # all specified using the block grid units
        self.world = world  # so we can set camera_shake
        self.block_range = block_range  # makes it easier when saving the map
        self.blocks = []
        for x in range(block_range[0][X], block_range[1][X]+1):
            for y in range(block_range[0][Y], block_range[1][Y]+1):
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
                if self.action == 'down':
                    b.y += self.speed
                elif self.action == 'up':
                    b.y -= self.speed
            self.current_offset += self.speed
            if self.current_offset >= self.distance * BLOCK_SIZE:
                self.world.camera_shake = False


class Block:
    """ any of the block tiles that define the foreground 'puzzle' blocks """

    def __init__(self, block_tiles, type, grid_position):
        self.block_tiles = block_tiles

        self.x = grid_position[X] * BLOCK_SIZE
        # to align the blocks with the bottom of the screen
        # the self.y needs an offset of -7
        # I'm not doing this for now
        self.y = grid_position[Y] * BLOCK_SIZE

        self.frame_count = 1
        self.frames = []
        self.type = ''
        self.name = ''
        self.image = None
        self.setType(type)

    def setType(self, type):
        """use the ASCII character passed as type to indicate which tile"""
        self.type = type

        # initialise the block from the tile sheet coordinates
        # given by the tile dictionary
        if type in self.block_tiles:
            self.frames = self.block_tiles[type]
            self.frame_count = len(self.frames)
            self.image = self.frames[0]
        else:
            console_msg("UNRECOGNISED BLOCK CODE:" + type, 3)

    def get_grid_position(self):
        return int(self.x / BLOCK_SIZE), int(self.y / BLOCK_SIZE)

    grid_position = property(get_grid_position)  # read only property

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
        """ The level maps are defined using text files that use
        ASCII symbols to represent each tile type.
        For example a complete pillar is
            Pp
           ¬[]
           |Bb/
        """
        self.world = world  # link back to the world game state

        # The tile dictionary is used to convert the ASCII tile symbols
        # used in the map file to the images for the tiles themselves.
        # It is read from a text file, to make it easy to add new tile types
        # key is an ASCII symbol used for the map file
        # value is another dictionary containing:
        #    * descriptive label,
        #    * list of (x,y) tuples giving the coordinates of the tile image
        #      in the tile sheet file. The coords are in multiples
        #      of the standard block size.
        #      The list is normally just one element long
        #      but triggers will have extra elements for animation frames

        file_name = 'BitQuest_tileset.txt'
        with open(file_name, 'r') as file:
            lines = file.readlines()
            tile_dict = {}
            for file_line in lines:
                # remove brackets around coords (which are just for looks)
                # so we convert "(8,1), (12,15)" to "8,1,12,15"
                csv_line = file_line.replace('(', '')
                csv_line = csv_line.replace(')', '')
                # convert comma separated text into a tile_dict record
                tile_info = csv_line.split(',')
                tile_coords = []
                for i in range(2, len(tile_info), 2):
                    tile_coords.append(
                        (int(tile_info[i]), int(tile_info[i+1]))
                    )
                tile_dict[tile_info[0]] = {
                    'name': tile_info[1],
                    'tiles': tile_coords
                }

        # editing cursor (used when editing the map)
        self.cursor = [5, 5]
        grid_size = BLOCK_SIZE * SCALING_FACTOR
        self.cursor_rect = pygame.Rect(self.cursor[X] * grid_size,
                                       self.cursor[Y] * grid_size,
                                       grid_size - GRID_LINE_WIDTH,
                                       grid_size - GRID_LINE_WIDTH)

        self.tile_sheet = sprite_sheet.SpriteSheet('assets/' + TILE_FILE)
        self.midground_blocks = []
        self.foreground_blocks = []
        self.movers = []
        self.triggers = {}
        self.tile_images = {}

        # build the dictionary of tile images from the dictionary
        # previously read in from the file
        for definition in tile_dict:
            images = []
            for coords in tile_dict[definition]['tiles']:
                images.append(self.tile_sheet.image_at(
                    (BLOCK_SIZE * coords[X], BLOCK_SIZE * coords[Y],
                     BLOCK_SIZE, BLOCK_SIZE),
                    ALPHA))
            self.tile_images[definition] = images
        self.load_grid()
        self.editor_palette = '1Pp[]Bb='
        # set the default starting tile for the editor
        self.current_editor_tile = self.editor_palette[0]
        self.cursor_block = Block(self.tile_images,
                                  self.current_editor_tile,
                                  self.cursor)
        self.erasing = False
        self.selection = []

    def begin_selection(self):
        self.selection = [(self.cursor[X], self.cursor[Y])]

    def end_selection(self):
        # Create a new moving block group
        # they are defined by their (left, top) & (right, bottom) coords
        # in the block coordinate system
        # plus a move direction as a string
        # and a number of blocks to move
        self.selection.append((self.cursor[X], self.cursor[Y]))
        print("Blocks", self.selection[0], "to", self.selection[1], "selected")
        trigger_pos = eval(input("Enter trigger block coords:"))
        direction = \
            input("Enter direction to move (up/down/left/right):").lower()
        distance = int(input("Enter number of blocks to move:"))

        mover = Moveable(self, self.world,
                         (self.selection[0], self.selection[1]),
                         direction,
                         distance)
        self.movers.append(mover)

        # assign a trigger to this block group
        # the triggers dictionary uses the grid coords of the trigger tile
        # as the key and the value is the index of the moveable object
        # that is activated
        self.triggers[trigger_pos] = len(self.movers)-1  # index most recently added

    def selecting(self):
        # true if we are in the middle of selecting a group of blocks
        # which we detect by checking if there is a start coordinate in
        # the selection list, but no end coordinate
        if len(self.selection) == 1:
            return True
        else:
            return False

    def save_grid(self, level=1):
        """save current grid map to the level file
        this function is only accessible in map editor mode"""
        # TODO add save dialogue to change name/folder

        # find size of the map by looking for the largest x & y coords
        max_x = 0
        max_y = 0
        for layer in [self.midground_blocks, self.foreground_blocks]:
            for b in layer:
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
 #DEBUG               # 2 blank lines as padding at the top of the level
 #               file.write('\n\n')
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
                file.write("'" + m.action + "', ")
                file.write(str(m.distance) + '\n')
            file.write(delimiter)

            # section 5
            for t in self.triggers:
                file.write(str(t) + ', ')
#                file.write(str(t[1]) + ', ')
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
        x = 0
        y = 0
        for row in midground_map:
            for tile_symbol in row:
                if tile_symbol != ' ':
                    self.midground_blocks.append(
                        Block(self.tile_images, tile_symbol, (x, y)))
                x += 1
            x = 0
            y += 1

        x = 0
        y = 0
        for row in foreground_map:
            for tile_symbol in row:
                if tile_symbol != ' ':
                    self.foreground_blocks.append(
                        Block(self.tile_images, tile_symbol, (x, y)))
                x += 1
            x = 0
            y += 1

        # the moveable objects are groups of blocks that all move together
        # in response to a trigger
        # they are defined by their (left, top) & (right, bottom) coords
        # in the block coordinate system
        # plus a move direction as a string
        # and a number of blocks to move
        i += 1  # skip over the ### section delimiter
        while i < len(level_data) and level_data[i] != '###':
            values = eval(level_data[i])
            mover = Moveable(self, self.world,
                             (values[0], values[1]),
                              values[2],
                              values[3],
                             )
            self.movers.append(mover)
            i += 1

        # the triggers dictionary uses the grid coords of the trigger tile
        # as the key and the value is the index of the moveable object
        # that is activated
        i += 1  # skip over the ### section delimiter
        console_msg("Block triggers:", 8)
        while i < len(level_data) and level_data[i] != '###':
            values = eval(level_data[i])
            console_msg(values, 8)
            self.triggers[values[0]] = int(values[1])
            i += 1

    def get_block(self, blocklist, x, y):
        """returns the block at grid coord x,y"""
        for b in blocklist:
            if b.grid_position == (x, y):
                return b
        console_msg("No block found at " + str(x) + "," + str(y), 8)
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

    def draw_grid(self, surface, origin, scroll, grid_colour):
        """ overlays a grid to show the block spacing """
        grid_size = BLOCK_SIZE * SCALING_FACTOR
        offset = [(s * SCALING_FACTOR) % grid_size for s in scroll]
        limit = [size * SCALING_FACTOR for size in DISPLAY_SIZE]
        label_offset = (grid_size / 2 - self.world.editor.char_width,
                        grid_size / 2 - self.world.editor.line_height / 2)

        # vertical grid lines & X-axis labels
        for x in range(-offset[X], limit[X] - offset[X], grid_size):
            pygame.draw.line(surface, grid_colour,
                             (x, 0),
                             (x, limit[Y] + origin[Y]),
                             GRID_LINE_WIDTH)
            axis_label = "{0:2d} ".format(int(x / grid_size +
                                              scroll[X] / BLOCK_SIZE))
            rendered_text = self.world.code_font.render(
                axis_label, True, grid_colour)
            self.world.screen.blit(rendered_text,
                                   (x + label_offset[X], 20))

        # horizontal grid lines & Y-axis labels
        for y in range(-offset[Y], limit[Y], grid_size):
            pygame.draw.line(surface, grid_colour,
                             (0, y + origin[Y]),
                             (limit[X], y + origin[Y]),
                             GRID_LINE_WIDTH)
            if y + label_offset[Y] < limit[Y]:
                axis_label = "{0:2d} ".format(int(y / grid_size +
                                                  scroll[Y] / BLOCK_SIZE))
                rendered_text = self.world.code_font.render(
                    axis_label, True, grid_colour)
                self.world.screen.blit(rendered_text,
                                       (GRID_LINE_WIDTH * 2,
                                        y + origin[Y] + label_offset[Y]))

        if MAP_EDITOR_ENABLED:
            # +2 added to Y to make the cursor line up with the grid labels
            # this is arbitrary, just to make 0,0 be the first whole block
            # in the top left of the screen
            self.cursor_rect.x = (self.cursor[X] * grid_size
                                  - scroll[X] * SCALING_FACTOR
                                  + GRID_LINE_WIDTH)
            self.cursor_rect.y = (self.cursor[Y] * grid_size
                                  - scroll[Y] * SCALING_FACTOR
                                  + origin[Y] + GRID_LINE_WIDTH)

            if not self.erasing:
                # draw translucent image of the currently selected tile
    #            surface.blit(self.cursor_block.image,
    #                         (self.cursor_rect[X], self.cursor_rect[Y]))

                surface.blit(
                    pygame.transform.scale(self.cursor_block.image,
                                           (grid_size-1, grid_size-1)),
                    (self.cursor_rect[X], self.cursor_rect[Y])
                    )

            # highlight cursor
            pygame.draw.rect(surface, (255, 255, 255),
                             self.cursor_rect,
                             GRID_LINE_WIDTH)
            # add grid coords of cursor
            # the cursor is labelled as if it is 1 block higher
            # than the actual block number to make it agree with the
            # way that BIT reports its own position.
            # Because the dog states his Y coord as being the block number that
            # his paws are *resting on*, he reports that he is
            # "at" Y=9 when his sprite actually occupies the block above
            # By subtracting one from Y when we label the cursor, we make the
            # coordinates indicated by the cursor match the coordinates
            # reported by BIT.
            cursor_label = "({0},{1})".format(self.cursor[X], self.cursor[Y])
            rendered_text = self.world.code_font.render(
                cursor_label, True, grid_colour)
            self.world.screen.blit(rendered_text,
                                   (self.cursor_rect[X],
                                    self.cursor_rect[Y] - 25))

    def cursor_right(self):
        self.cursor[X] += 1
        print(self.cursor)

    def cursor_left(self):
        if self.cursor[X] > 0:
            self.cursor[X] -= 1
        print(self.cursor)

    def cursor_up(self):
        if self.cursor[Y] > 0:
            self.cursor[Y] -= 1
        print(self.cursor)

    def cursor_down(self):
        self.cursor[Y] += 1
        print(self.cursor)

    def _change_editor_tile(self, direction):
        """ cycle the selected editor tile the number of places
        given by direction - should be just +/- 1"""
        if not self.erasing:
            palette_index = self.editor_palette.index(
                self.current_editor_tile)
            palette_index = (palette_index + direction) \
                % len(self.editor_palette)
            self.current_editor_tile = self.editor_palette[palette_index]
            self.cursor_block.setType(self.current_editor_tile)

    def next_editor_tile(self):
        self.erasing = False
        self._change_editor_tile(1)

    def previous_editor_tile(self):
        self.erasing = False
        self._change_editor_tile(-1)

    def blank_editor_tile(self):
        self.erasing = True
        self.change_block()

    def change_block(self):
        """ changes the block at the cursor location to the current
        cursor block. If erasing is True, remove the block entirely."""
        existing_block = self.get_block(self.midground_blocks,
                                        self.cursor[X],
                                        self.cursor[Y])
        if self.erasing:
            if existing_block:
                self.midground_blocks.remove(existing_block)
        elif existing_block:
            existing_block.setType(self.current_editor_tile)
        else:
            # create new block
            b = Block(self.tile_images, self.current_editor_tile, self.cursor)
            self.midground_blocks.append(b)

    def collision_test(self, character_rect, movement, scroll):
        """ check if this character is colliding with any of the blocks
        blocks are categorised as:
        collidable - collision physics applies to characters
        trigger - characters can overlap the block, activating the trigger
        cosmetic - no collision physics or trigger (but may animate)
        """
        if SHOW_COLLIDERS:
            # DEBUG draw character collider in green
            draw_collider(self.world.display,
                          (0, 255, 0), character_rect, 1, scroll)

        # check for collisions with triggers
        for t in self.midground_blocks:
            if t.is_trigger():
                collider = pygame.Rect(t.x,
                                       t.y,
                                       BLOCK_SIZE, BLOCK_SIZE)
                if SHOW_COLLIDERS:
                    # DEBUG draw block colliders in yellow
                    draw_collider(self.world.display,
                                  (255, 255, 0), collider, 1, scroll)
                if character_rect.colliderect(collider):
                    if t.grid_position in self.triggers.keys():
                        t.image = t.frames[1]  # switch to 'pressed' state
                        self.movers[self.triggers[t.grid_position]].activate()
                        console_msg(
                            "trigger "
                            + str(self.triggers[t.grid_position])
                            + " activated!", 8)

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
                if SHOW_COLLIDERS:
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
                            collisions['right'] is None):
                        collisions['right'] = collider

                    if movement[X] < 0:
                        if (character_rect.left <= collider.right and
                                (character_rect.bottom > collider.top
                                 + COLLIDE_THRESHOLD) and
                                collisions['left'] is None):
                            collisions['left'] = collider
                            # DEBUG draw active colliders in red
                            if SHOW_COLLIDERS:
                                draw_collider(self.world.display,
                                              (255, 0, 0), collider, 0, scroll)

                    # TODO may need similar logic for Y movement, to allow
                    # falling when you are next to a wall
                    if (movement[Y] < 0 and
                            character_rect.top <= collider.bottom and
                            collisions['up'] is None):
                        collisions['up'] = collider

                    if (movement[Y] > 0 and
                            character_rect.bottom >= collider.top and
                            collisions['down'] is None):
                        collisions['down'] = collider

        return collisions

    def point_collision_test(self, position):
        """ a much simpler collision test used for the particle system
        returns true if the particle position is inside any block"""
        x = int(position[X] / BLOCK_SIZE)
        y = int(position[Y] / BLOCK_SIZE)
        for b in self.midground_blocks:
            if (x, y) == b.grid_position:
                return True
        return False
