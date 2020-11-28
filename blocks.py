""" movement and animation for all the player and npc sprites """
import math
import pygame
from console_messages import console_msg
from constants import *
import sprite_sheet
import triggers

ALPHA = (255, 255, 255)


def draw_collider(surface, colour, collider, width, scroll):
    """ debug routine to show colliders"""
    if SHOW_COLLIDERS:
        rect = pygame.Rect(collider.x - scroll[X],
                           collider.y - scroll[Y],
                           collider.width,
                           collider.height)
        pygame.draw.rect(surface, colour, rect, width)


class Moveable:
    """ pillars, drawbridges and other objects that move
    when a trigger activates. They are simply arbitrary collections
    of blocks that move in concert when activated."""

    def __init__(self, world, id_num, blocks):
        self.world = world  # so we can set camera_shake
        self.id = id_num  # unique number used for loading/saving
        self.blocks = blocks  # list of blocks
        self.home_positions = []  # initial x,y coords of all blocks (pixels)
        for b in blocks:
            if b:
                self.home_positions.append((b.x, b.y))
            else:
                # if a null block accidentally gets included in the mover list
                # insert a placeholder, so that the reset function
                # doesn't get out of sync
                self.home_positions.append(None)
        self.activated = False
        # target_offset is the number of x,y pixels the group should shift by
        # it is set by the trigger when it activates
        # as the group moves into place, current_offset
        # updates until they match
        self.current_offset = [0, 0]
        self.target_offset = [0, 0]
        self.speed = 1
        self.movement = [0.0, 0.0]  # movement x, y speed (set when activated)

    def activate(self, offset):
        self.activated = True
        self.target_offset = [coord * BLOCK_SIZE for coord in offset]
        self.world.camera_shake = True
        # the movement value of the block is used to transfer momentum
        # to any characters that are touching the blocks
        # this allows pillars to lift or push characters around
        for i in [X, Y]:
            if self.target_offset[i] != 0:
                self.movement[i] = math.copysign(self.speed,
                                                 self.target_offset[i])
        for b in self.blocks:
            if b:  # guard against a null block in the mover list
                b.movement = self.movement
            # TODO what happens without this?
            #  It seems ok, but test when we ride a platform moving downwards
            # uncommenting it causes blocks moving up, to drift out of sync
            # with the grid
            # if self.target_offset[Y] <0:  # moving up
            #    b.movement[Y] -= GRAVITY

    def reset(self):
        # return all blocks to their original (pre-triggered) locations
        for i in range(len(self.blocks)):
            if self.blocks[i]:  # guard against a null block in the list
                self.blocks[i].x = self.home_positions[i][X]
                self.blocks[i].y = self.home_positions[i][Y]
                self.activated = False
                self.target_offset = [0.0, 0.0]
                self.current_offset = [0.0, 0.0]
                self.movement = [0.0, 0.0]

    def update(self, block_map):
        """ move the blocks if this group has been triggered
        if the group is moving it returns True, otherwise False """
        if self.activated and self.movement != [0.0, 0.0]:
            for b in self.blocks:
                old_grid_pos = b.grid_position
                b.x += self.movement[X]
                b.y += self.movement[Y]

                # The block map is keyed by the grip positions of the blocks.
                # So if the block has moved enough to change its grid position,
                # we must update the block map - otherwise collisions won't
                # work properly.
                # Doing it here, rather than in BlockMap requires us to pass
                # a link to the midground_blocks dictionary (block_map)
                # But it is much cheaper to do it here, since we can just
                # check the blocks in the active mover, rather than the
                # whole map.
                if b.grid_position != old_grid_pos:
                    # remove the block from its previous position in the map
                    del block_map[old_grid_pos]

            # if we deleted blocks from the map, we must add them back in
            # at their new positions
            for b in self.blocks:
                block_map[b.grid_position] = b

            self.current_offset[X] += self.movement[X]
            self.current_offset[Y] += self.movement[Y]

            # check if the group has reached its destination
            # done in a loop, since X and Y are the same
            for i in [X, Y]:
                if self.movement[i] > 0:
                    if self.current_offset[i] >= self.target_offset[i]:
                        self.movement[i] = 0.0
                elif self.movement[i] < 0:
                    if self.current_offset[i] <= self.target_offset[i]:
                        self.movement[i] = 0.0

            if self.movement == [0.0, 0.0]:
                self.world.camera_shake = False
                for b in self.blocks:
                    b.movement = [0, 0]
            return True
        else:
            return False

    # def get_bounding_box(self):
    #     """ return a rectangle surrounding this group of blocks """
    #     left = self.blocks[0].x - self.world.scroll[X]
    #     top = self.blocks[0].y - self.world.scroll[Y]
    #     # the block x,y values are for the top left corner of the block
    #     # so we need to add one extra block's worth for the full width/height
    #     width = self.blocks[-1].x - self.world.scroll[X] - left + BLOCK_SIZE
    #     height = self.blocks[-1].y - self.world.scroll[Y] - top + BLOCK_SIZE
    #     return pygame.Rect(left, top, width, height)


class Block:
    """ any of the block tiles that define the foreground 'puzzle' blocks """

    def __init__(self, block_tiles, block_type, grid_position):
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
        self.setType(block_type)
        self.movement = [0, 0]

    def top(self):
        return self.y

    def bottom(self):
        return self.y + BLOCK_SIZE

    def left(self):
        return self.x

    def right(self):
        return self.x + BLOCK_SIZE

    def setType(self, block_type):
        """use the ASCII character passed as type to indicate which tile"""
        self.type = block_type

        # initialise the block from the tile sheet coordinates
        # given by the tile dictionary
        if block_type in self.block_tiles:
            self.frames = self.block_tiles[block_type]
            self.frame_count = len(self.frames)
            self.image = self.frames[0]
        else:
            console_msg("UNRECOGNISED BLOCK CODE:" + type, 3)

    def get_grid_position(self):
        return int(self.x / BLOCK_SIZE), int(self.y / BLOCK_SIZE)

    grid_position = property(get_grid_position)  # read only property

    def is_collidable(self):
        """ These blocks are not collidable,
        even if they are on the midground layer
        This allows triggers to be placed behind cosmetic foliage etc
        without blocking character movement
        """
        if self.type not in '-{|/}=ZXCVNM':
            return True
        else:
            return False

    def is_trigger(self):
        # TODO check if we still need this now we have a separate Trigger class
        if self.type in '-=':
            return True
        else:
            return False


class BlockMap:

    def __init__(self, world, tile_dictionary_file, tileset_file):
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

        with open(tile_dictionary_file, 'r') as file:
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
                        (int(tile_info[i]), int(tile_info[i + 1]))
                    )
                tile_dict[tile_info[0]] = {
                    'name': tile_info[1],
                    'tiles': tile_coords
                }
        # load all the tile types into the editor palette
        self.editor_palette = [t for t in tile_dict]

        # editing cursor (used when editing the map)
        self.cursor = [5, 5]
        grid_size = BLOCK_SIZE * SCALING_FACTOR
        self.cursor_rect = pygame.Rect(self.cursor[X] * grid_size,
                                       self.cursor[Y] * grid_size,
                                       grid_size - GRID_LINE_WIDTH,
                                       grid_size - GRID_LINE_WIDTH)

        self.tile_sheet = sprite_sheet.SpriteSheet(tileset_file)

        # store blocks in a dict indexed by grid position
        # this gives way better performance than a simple list
        # because collisions can check just the blocks in the
        # immediate vicinity, instead of searching the entire map
        self.midground_blocks = {}
        self.foreground_blocks = {}

        # movers are indexed by their unique ID number
        self.movers = {}
        # triggers aren't a dict, because I'm not sure what to index them with
        # - we might want triggers that aren't associated with a specific block
        self.triggers = []
        self.link_trigger = None  # set when connecting a trigger to movers

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
        self.load_grid(1)  # build the layer dictionaries from the level map
        # set the default starting tile for the editor
        self.current_editor_tile = self.editor_palette[0]
        self.cursor_block = Block(self.tile_images,
                                  self.current_editor_tile,
                                  self.cursor)
        self.erasing = False
        # the selected_blocks list keeps track of the midground blocks that
        # are currently highlighted, when assigning a moveable group
        self.selected_blocks = []
        self.selecting = False
        self.show_grid = False
        self.current_layer = self.midground_blocks
        self.busy = False  # True when blocks are moving

    def reset(self):
        # reset the whole map to its initial state
        # TODO reset checkpoint flags and other stuff that has changed
        for m in self.movers:
            self.movers[m].reset()
        for t in self.triggers:
            t.reset()

    def switch_layer(self):
        """ toggle the map editor between the midground and foreground
         block layers"""
        if self.current_layer == self.midground_blocks:
            self.current_layer = self.foreground_blocks
        else:
            self.current_layer = self.midground_blocks

    def cursor_to_mouse(self, mouse_pos):
        # select the grid square closest to the mouse cursor
        self.cursor = [
            int(mouse_pos[X] / BLOCK_SIZE),
            int(mouse_pos[Y] / BLOCK_SIZE)
        ]

    def grid_to_screen_pos(self, grid_pos):
        # convert grid coords to screen coords
        return (0,0)  # TODO replace this with a proper calculation!

    def select_block(self, mouse_pos):
        if self.selecting:
            self.cursor_to_mouse(mouse_pos)
            b = self.get_block(self.midground_blocks, *self.cursor)
            if b:
                self.selected_blocks.append(b)
            print(self.selected_blocks)

    def begin_selection(self):
        self.selecting = True
        print("Selecting...")

    def cancel_selection(self):
        self.selected_blocks = []

    def end_selection(self):
        print("selection complete")
        self.selecting = False
        # Create a new moving block group
        mover = Moveable(self.world,
                         self.get_next_mover_id(),
                         self.selected_blocks)
        self.movers[mover.id] = mover
        # delete the selection now, because it is saved as a moveable group
        self.selected_blocks = []

    def set_trigger(self, mouse_pos):
        """ create a trigger at this position
        or add a new action to an existing trigger?
        """

        self.cursor_to_mouse(mouse_pos)
        b = self.get_block(self.midground_blocks, *self.cursor)
        if not b:
            return  # bail immediately, since there is no block here

        # check if this block is already a trigger
        existing_trigger = None
        for t in self.triggers:
            if t.block == b:
                existing_trigger = t
        if not existing_trigger:
            # create a new trigger. The trigger needs:
            # 1. a link to the world object
            # 2. the trigger type (currently always 'pressure plate')
            # 3. the random flag (True if the trigger picks actions at random)
            # 4. the block object for the pressure plate tile
            # this just creates a trigger with no actions
            # use the Trigger.add_action() method for this
            t = triggers.Trigger(self.world,
                                 'pressure plate',
                                 False,
                                 b
                                 )
            # # TODO allow new movers to be associated with an existing trigger
            # t.addMover(mover)
            # add the complete trigger to the list maintained by the map
            self.triggers.append(t)
        else:
            # if the trigger already exists, enter linking mode
            self.link_trigger = existing_trigger
            print("exisiting trigger,", t)

    # response = input("Enter trigger block coords:")
    # if response != "":
    #     trigger_pos = eval(response)
    #     direction = \
    #         input("Enter direction to move (up/down/left/right):").lower()
    #     distance = int(input("Enter number of blocks to move:"))
    #

    def get_next_mover_id(self):
        """ returns the next integer in the sequence to make sure that
        every mover has a unique id number.
        We store this number as a class variable and use it as the dict key,
        rather than using a simple list index, so that the id doesn't change
        if movers are later deleted"""
        return len(self.movers)

    def save_grid(self, level=1):
        """save current grid map to the level file
        this function is only accessible in map editor mode"""
        # TODO add save dialogue to change name/folder

        # reset the map to its original state before saving
        # otherwise triggered blocks will be saved in their current state
        self.reset()

        # find size of the map by looking for the largest x & y coords
        max_x = 0
        max_y = 0
        for layer in [self.midground_blocks, self.foreground_blocks]:
            for coord in layer:
                b = layer[coord]
                if b.grid_position[X] > max_x:
                    max_x = b.grid_position[X]
                if b.grid_position[Y] > max_y:
                    max_y = b.grid_position[Y]

        # write this map to the file
        file_name = LEVEL_MAP_FILE_STEM + str(level) + LEVEL_MAP_FILE_EXTENSION
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
            file.write("# movers\n")
            for i in range(len(self.movers)):
                file.write(str(i) + ", [")  # unique id number
                m = self.movers[i]
                for b in m.blocks:
                    file.write(str(b.grid_position) + ', ')
                file.write(']\n')
            file.write(delimiter)

            # section 5
            file.write("# triggers\n")
            for t in self.triggers:
                file.write("'" + t.type + "', ")
                if t.type == 'flagpole':
                    file.write("'" + t.name + "', ")
                    file.write(str(t.block.grid_position) + '\n')
                else:
                    file.write(str(t.random) + ", ")
                    file.write(str(t.block.grid_position) + ', [')
                    for a in t.actions:
                        file.write('(' + str(a[0].id) + ', ')
                        file.write(str(a[1]) + '), ')
                    file.write(']\n')
            file.write(delimiter)

    def load_grid(self, level=1):
        """read in map data from the level file
        Each screen has room for 15 x 11 tiles
        but a map may be arbitrarily wide
        """
        # midground is the same layer as the player
        # collidable blocks on this layer will stop player progress

        file_name = LEVEL_MAP_FILE_STEM + str(level) + LEVEL_MAP_FILE_EXTENSION
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
                    b = Block(self.tile_images, tile_symbol, (x, y))
                    self.midground_blocks[(x, y)] = b
                x += 1
            x = 0
            y += 1

        x = 0
        y = 0
        for row in foreground_map:
            for tile_symbol in row:
                if tile_symbol != ' ':
                    b = Block(self.tile_images, tile_symbol, (x, y))
                    self.foreground_blocks[(x, y)] = b
                x += 1
            x = 0
            y += 1

        # the moveable objects are groups of blocks that all move together
        # in response to a trigger
        # they are have a unique id number
        # and a list of blocks, specified using the block coordinate system
        i += 1  # skip over the ### section delimiter
        while i < len(level_data) and level_data[i] != '###':
            if level_data[i][0] != "#":  # comment lines are ignored
                values = eval(level_data[i])
                # create a list of block objects from the list of grid coords
                mover_blocks = [self.get_block(
                    self.midground_blocks, grid[X], grid[Y])
                    for grid in values[1]]
                mover = Moveable(self.world,
                                 values[0],  # id
                                 mover_blocks
                                 )
                key = values[0]
                self.movers[key] = mover
            i += 1

        # the triggers are stored with the name of the trigger type,
        # followed by a grid coord representing the trigger block
        # then a list of actions as (id, (x, y)) tuples
        # representing the mover id and the number of blocks to move
        # when activated
        i += 1  # skip over the ### section delimiter
        console_msg("Block triggers:", 8)
        while i < len(level_data) and level_data[i] != '###':
            if level_data[i][0] != "#":  # comment lines are ignored
                values = eval(level_data[i])
                console_msg(values, 8)
                if values[0] == 'flagpole':
                    trigger_pos = values[2]
                    # the trigger is the bottom left of the group of 2x2
                    # that make up the flagpole image
                    # we add all of them to a list to send to the trigger
                    flagpole_blocks = [
                        self.get_block(self.midground_blocks,
                                       trigger_pos[X], trigger_pos[Y]),
                        self.get_block(self.midground_blocks,
                                       trigger_pos[X] + 1, trigger_pos[Y]),
                        self.get_block(self.midground_blocks,
                                       trigger_pos[X], trigger_pos[Y] - 1),
                        self.get_block(self.midground_blocks,
                                       trigger_pos[X] + 1, trigger_pos[Y] - 1),
                        self.get_block(self.midground_blocks,
                                       trigger_pos[X], trigger_pos[Y] - 2),
                        self.get_block(self.midground_blocks,
                                       trigger_pos[X] + 1, trigger_pos[Y] - 2),
                    ]
                    t = triggers.Flagpole(self.world,
                                          # name of the corresponding level
                                          values[1],
                                          # all the blocks for the flagpole
                                          flagpole_blocks)
                else:
                    t = triggers.Trigger(self.world,
                                         values[0],  # type
                                         values[1],  # random flag
                                         # block object representing the
                                         # trigger location
                                         self.get_block(self.midground_blocks,
                                                        values[2][X],
                                                        values[2][Y]))
                    # add all the actions associated with this trigger
                    for action in values[3]:
                        t.addAction(self.movers[action[0]], action[1])
                # add the complete trigger to the list maintained by the map
                self.triggers.append(t)
            i += 1

    def get_block(self, block_dict, x, y):
        """returns the block at grid coord x,y"""
        if (x, y) in block_dict:
            return block_dict[(x, y)]
        else:
            console_msg("No block found at " + str(x) + "," + str(y), 8)
            return None

    def update(self, surface):
        """ draw any blocks that are on-screen """

        # calculate the upper and lower bounds of the visible screen
        # so that we don't waste time drawing blocks that are off screen
        min_visible_block_x = self.world.scroll[X] // BLOCK_SIZE
        max_visible_block_x = (min_visible_block_x
                               + DISPLAY_SIZE[X] // BLOCK_SIZE
                               + 1)

        # draw each tile in its current location
        for coord in self.midground_blocks:
            if min_visible_block_x <= coord[X] <= max_visible_block_x:
                b = self.midground_blocks[coord]
                surface.blit(b.image,
                             (b.x - self.world.scroll[X],
                              b.y - self.world.scroll[Y]))

                if self.show_grid and MAP_EDITOR_ENABLED:
                    # highlight the block if it is currently selected
                    if b in self.selected_blocks:
                        self.highlight_block(surface, b, COLOUR_SELECTED_BLOCK)
                    else:
                        # highlight triggers
                        for t in self.triggers:
                            if b == t.block:
                                self.highlight_block(surface, b,
                                                     COLOUR_TRIGGER_BLOCK)
                        # highlight moving block groups
                        for m in self.movers:
                            if b in self.movers[m].blocks:
                                self.highlight_block(surface, b,
                                                     COLOUR_MOVING_BLOCK)

        for coord in self.foreground_blocks:
            if min_visible_block_x <= coord[X] <= max_visible_block_x:
                b = self.foreground_blocks[coord]
                surface.blit(b.image,
                             (b.x - self.world.scroll[X],
                              b.y - self.world.scroll[Y]))

        # give any moving blocks a chance to update
        # if any are currently moving, we set busy to true, so that
        # the player program is paused until the moves are complete
        self.busy = False
        for m in self.movers:
            if self.movers[m].update(self.midground_blocks):
                self.busy = True

        # if we are in trigger linking mode, run a line from the
        # cursor to the trigger block
        if self.link_trigger:
            print("linking...",
                  self.grid_to_screen_pos(self.cursor),
                  ",",
                  self.grid_to_screen_pos(
                      self.link_trigger.block.grid_position)
                  )
            pygame.draw.line(surface, COLOUR_TRIGGER_BLOCK,
                             self.grid_to_screen_pos(self.cursor),
                             self.grid_to_screen_pos(self.link_trigger.block.grid_position)
                             , 1)

    def highlight_block(self, surface, block, colour):
        left = block.x - self.world.scroll[X]
        top = block.y - self.world.scroll[Y]
        # the block x,y values are for the top left corner of the block
        # so we need to add one extra block's worth for the full
        # width/height
        b_rect = pygame.Rect(left, top, BLOCK_SIZE, BLOCK_SIZE)
        # add some grey to lighten the selected block image
        surface.fill(colour, b_rect, pygame.BLEND_RGB_ADD)

    def draw_grid(self, surface, origin, grid_colour):
        """ overlays a grid to show the block spacing """
        grid_size = BLOCK_SIZE * SCALING_FACTOR
        offset = [(s * SCALING_FACTOR) % grid_size for s in self.world.scroll]
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
                                              self.world.scroll[
                                                  X] / BLOCK_SIZE))
            self.display_text(axis_label,
                              (x + label_offset[X], 20), grid_colour)

        # horizontal grid lines & Y-axis labels
        for y in range(-offset[Y], limit[Y], grid_size):
            pygame.draw.line(surface, grid_colour,
                             (0, y + origin[Y]),
                             (limit[X], y + origin[Y]),
                             GRID_LINE_WIDTH)
            if y + label_offset[Y] < limit[Y]:
                axis_label = "{0:2d} ".format(int(y / grid_size +
                                                  self.world.scroll[
                                                      Y] / BLOCK_SIZE))
                self.display_text(axis_label,
                                  (GRID_LINE_WIDTH * 2,
                                   y + origin[Y] + label_offset[Y]),
                                  grid_colour
                                  )

        if MAP_EDITOR_ENABLED:
            self.cursor_rect.x = (self.cursor[X] * grid_size
                                  - self.world.scroll[X] * SCALING_FACTOR
                                  + GRID_LINE_WIDTH)
            self.cursor_rect.y = (self.cursor[Y] * grid_size
                                  - self.world.scroll[Y] * SCALING_FACTOR
                                  + origin[Y] + GRID_LINE_WIDTH)

            if not self.erasing:
                # draw the currently selected tile type at the cursor pos
                # this has to be separately scaled, because we are drawing
                # on the unscaled surface (so the grid axes text looks nice)
                surface.blit(
                    pygame.transform.scale(
                        self.cursor_block.image,
                        (grid_size, grid_size)),
                    (self.cursor_rect[X], self.cursor_rect[Y])
                )

            # highlight cursor
            pygame.draw.rect(surface, (255, 255, 255),
                             self.cursor_rect,
                             GRID_LINE_WIDTH)
            # add grid coords of cursor
            cursor_label = "({0},{1})".format(self.cursor[X], self.cursor[Y])
            self.display_text(cursor_label,
                              (self.cursor_rect[X], self.cursor_rect[Y] - 25),
                              grid_colour)
            # add a label to say which block layer is currently selected
            if self.current_layer == self.midground_blocks:
                self.display_text("midground layer", (4, -2), grid_colour)
            else:
                self.display_text("foreground layer", (4, -2), grid_colour)

    def display_text(self, text, position, colour):
        """ render text at the native resolution to make it look nicer"""
        rendered_text = self.world.code_font.render(
            text, True, colour)
        self.world.screen.blit(rendered_text, position)

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

    def home_cursor(self):
        """ move the cursor to the centre of the screen
        taking into account the current scroll value"""
        self.cursor = [
            int(self.world.scroll[X] / BLOCK_SIZE
                + DISPLAY_SIZE[X] / BLOCK_SIZE / 2),
            int(self.world.scroll[Y] / BLOCK_SIZE
                + DISPLAY_SIZE[Y] / BLOCK_SIZE / 2)
        ]

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
        existing_block = self.get_block(self.current_layer,
                                        self.cursor[X],
                                        self.cursor[Y])
        if self.erasing:
            if existing_block:
                # if the block is a trigger, remove from the trigger list
                # to do this we need to build a tuple with the same coords
                # as the cursor pos, and see if this is listed in the
                # triggers dictionary
                block_coords = (self.cursor[X], self.cursor[Y])
                if block_coords in self.triggers:
                    self.triggers.pop(block_coords)
                # now remove the block itself
                # need to turn the cursor list object into a tuple
                # so that it can be used to access the dict
                self.current_layer.pop((self.cursor[X], self.cursor[Y]))
        elif existing_block:
            existing_block.setType(self.current_editor_tile)
        else:
            # create new block
            b = Block(self.tile_images, self.current_editor_tile, self.cursor)
            # create a tuple from the cursor list object
            # so that it can be used as a dict index
            # then assign current block tile to this index
            self.current_layer[(self.cursor[X], self.cursor[Y])] = b

    def remove_moveable_group(self):
        """ Remove the moveable block group from the map
        if the cursor is currently over any of the blocks, the entire
        group is removed.
        The blocks themselves are not affected - they just don't count
        as a movable group anymore.
        """
        existing_block = self.get_block(self.current_layer,
                                        self.cursor[X],
                                        self.cursor[Y])
        if existing_block:
            for m in self.movers:
                if existing_block in m.blocks:
                    # confirmation dialog
                    if input("Delete this movable group? (y/n)") == 'y':
                        self.movers.remove(m)
                        # deleting an element inside the for loop
                        # could cause the  loop to skip an element
                        # but we can quit the loop immediately anyway,
                        # so it's ok (albeit a bit scruffy)
                        break

    def collision_test(self, character_rect):
        """ check if this character is colliding with any of the blocks
        blocks are categorised as:
        collidable - collision physics applies to characters
        trigger - characters can overlap the block, activating the trigger
        cosmetic - no collision physics or trigger (but may animate)
        """
        if SHOW_COLLIDERS:
            # DEBUG draw character collider in green
            draw_collider(self.world.display,
                          (0, 255, 0), character_rect, 1, self.world.scroll)

        # check for collisions with solid objects
        collisions = []

        # check all collidable blocks (the foreground layer is not collidable)
        for coord in self.midground_blocks:
            # only check blocks within 1 square of the character
            # horizontally. This is a performance optimisation, so the
            # collision check doesn't slow down on large maps
            if abs(coord[X] - (character_rect.centerx // BLOCK_SIZE)) <= 2:
                b = self.midground_blocks[coord]
                if b.is_collidable():
                    collider = pygame.Rect(b.x,
                                           b.y,
                                           BLOCK_SIZE, BLOCK_SIZE)
                    if SHOW_COLLIDERS:
                        # DEBUG draw block colliders in yellow
                        draw_collider(self.world.display,
                                      (255, 255, 0),
                                      collider, 1, self.world.scroll)

                    if character_rect.colliderect(collider):
                        collisions.append(b)

                        # DEBUG draw active colliders in red
                        if SHOW_COLLIDERS:
                            draw_collider(self.world.display,
                                          (255, 0, 0),
                                          collider, 0, self.world.scroll)

        return collisions

    def old_collision_test(self, character_rect, movement):
        """ check if this character is colliding with any of the blocks
        blocks are categorised as:
        collidable - collision physics applies to characters
        trigger - characters can overlap the block, activating the trigger
        cosmetic - no collision physics or trigger (but may animate)
        """
        if SHOW_COLLIDERS:
            # DEBUG draw character collider in green
            draw_collider(self.world.display,
                          (0, 255, 0), character_rect, 1, self.world.scroll)

        # check for collisions with solid objects
        collisions = {'left': None,
                      'right': None,
                      'up': None,
                      'down': None,
                      'down left': None,
                      'down right': None}

        # find the first colliding block in each direction
        for coord in self.midground_blocks:
            # only check blocks within 1 grid of the character, horizontally
            if abs(coord[X] - (character_rect.centerx // BLOCK_SIZE)) < 2:
                b = self.midground_blocks[coord]
                if b.is_collidable():
                    collider = pygame.Rect(b.x,
                                           b.y,
                                           BLOCK_SIZE, BLOCK_SIZE)
                    if SHOW_COLLIDERS:
                        # DEBUG draw block colliders in yellow
                        draw_collider(self.world.display,
                                      (255, 255, 0),
                                      collider, 1, self.world.scroll)

                    if character_rect.colliderect(collider):
                        # just because the rectangles overlap, doesn't
                        # necessarily
                        # mean we want to call it a collision. We only count
                        # collisions
                        # where the character is moving towards the block
                        # or vice versa. This prevents characters from getting
                        # stuck in blocks
                        if (movement[X] - b.movement[X] > 0 and
                                character_rect.right >= collider.left and
                                (character_rect.bottom > collider.top
                                 + COLLIDE_THRESHOLD_Y) and
                                collisions['right'] is None):
                            collisions['right'] = b  # collider

                        if (movement[X] - b.movement[X] < 0 and
                                character_rect.left <= collider.right and
                                (character_rect.bottom > collider.top
                                 + COLLIDE_THRESHOLD_Y) and
                                collisions['left'] is None):
                            collisions['left'] = b

                        if (movement[Y] - b.movement[Y] >= 0 and
                                character_rect.bottom >= collider.top):

                            # where more than one block collides
                            # upwards-moving > stationary > downward-moving
                            if b.movement[Y] != 0:
                                collisions['down'] = b
                            else:
                                collisions['down'] = b

                        if (movement[Y] - b.movement[Y] <= 0 and
                                collisions['up'] is None):
                            collisions['up'] = b

                        # DEBUG draw active colliders in red
                        if SHOW_COLLIDERS:
                            draw_collider(self.world.display,
                                          (255, 0, 0),
                                          collider, 0, self.world.scroll)

        return collisions

    def trigger_test(self, character_rect):
        """ check each trigger on the map to see if it should go off """
        for t in self.triggers:
            if t.enabled:  # saves checking triggers that have already gone off
                t.check(character_rect)

    def point_collision_test(self, position):
        """ a much simpler collision test used for the particle system
        returns true if the particle position is inside any block"""
        x = int(position[X] / BLOCK_SIZE)
        y = int(position[Y] / BLOCK_SIZE)
        if (x, y) in self.midground_blocks:
            return True
        else:
            return False
