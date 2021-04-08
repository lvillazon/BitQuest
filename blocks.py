""" movement and animation for all the player and npc sprites """
import math
import os

import pygame
from console_messages import console_msg
from constants import *
import sprite_sheet
import triggers

ALPHA = (255, 255, 255)


class Moveable:
    """ pillars, drawbridges and other objects that move
    when a trigger activates. They are simply arbitrary collections
    of blocks that move in concert when activated."""

    def __init__(self, id_num, blocks):
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
        self.activated = False  # True if the mover has ever been triggered
        self.moving = False  # True only while the mover is actually transitioning to the activated state
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
        self.moving = True
        self.target_offset = [coord * BLOCK_SIZE for coord in offset]
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

    def reset(self, block_map):
        # return all blocks to their original (pre-triggered) locations
        for i in range(len(self.blocks)):
            # guard against a null block in the list
            if self.blocks[i]:
                if self.blocks[i].grid_position in block_map:
                    # remove the block from its current position in the block map
                    del block_map[self.blocks[i].grid_position]

                # reset its position
                self.blocks[i].x = self.home_positions[i][X]
                self.blocks[i].y = self.home_positions[i][Y]
                self.activated = False
                self.target_offset = [0.0, 0.0]
                self.current_offset = [0.0, 0.0]
                self.movement = [0.0, 0.0]

                # add it back into the map at the reset position
                # see update() below, for details of why this is done this way
                block_map[self.blocks[i].grid_position] = self.blocks[i]

    def update(self, block_map):
        """ move the blocks if this group has been triggered
        if the group is moving it returns True, otherwise False """
        if self.activated and self.movement != [0.0, 0.0]:
            for b in self.blocks:
                old_grid_pos = b.grid_position
                b.x += self.movement[X]
                b.y += self.movement[Y]

                # The block map is keyed by the grid positions of the blocks.
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
                self.moving = False
                for b in self.blocks:
                    b.movement = [0, 0]
            return True
        else:
            return False


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

    @staticmethod
    def clone(source_block, grid_position):
        """ creates a new copy of source_block at grid_position"""
        return Block(source_block.block_tiles,
                     source_block.type,
                     grid_position)

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
            console_msg("UNRECOGNISED BLOCK CODE:" + block_type, 3)

    def copyTile(self, other_block):
        """ Makes this block use the same tile(s) as other_block
        without changing its position """
        self.setType(other_block.type)

    def get_grid_position(self):
        return int(self.x / BLOCK_SIZE), int(self.y / BLOCK_SIZE)

    def set_grid_position(self, pos):
        self.x = pos[X] * BLOCK_SIZE
        self.y = pos[Y] * BLOCK_SIZE

    # read only property
    grid_position = property(get_grid_position)

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

    def __init__(self, world, tile_dictionary_file, tileset_file, camera):
        """ The level maps are defined using text files that use
        ASCII symbols to represent each tile type.
        For example a complete pillar is
            Pp
           ¬[]
           |Bb/
        """
        self.world = world  # link back to the world game state
        self.camera = camera  # link to the game camera, so we can access the scroll value
        self.level = 0  # placeholder; load_grid sets this

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
        self.pending_link = None  # set when defining a trigger action

        self.tile_images = {}
        # build the dictionary of tile images from the dictionary
        # previously read in from the file
        for tile_id in tile_dict:
            images = []
            for coords in tile_dict[tile_id]['tiles']:
                images.append(self.tile_sheet.image_at(
                    (BLOCK_SIZE * coords[X], BLOCK_SIZE * coords[Y],
                     BLOCK_SIZE, BLOCK_SIZE),
                    ALPHA))
            self.tile_images[tile_id] = images

        # use the tile images to build the editor palette
        # this comprises a list of blocks, one for each tile
        # and a surface with all the tiles arranged in a grid
        self.palette_blocks = []
        for tile_id in tile_dict:
            b = Block(self.tile_images, tile_id, (0, 0))
            self.palette_blocks.append(b)

        self.editor_palette = pygame.Surface(PALETTE_SIZE)
        self.editor_palette.fill(COLOUR_MAP_EDITOR_BOXES)
        row, col = 0, 0
        for b in self.palette_blocks:
            position = (col * (BLOCK_SIZE * PALETTE_SCALE + PALETTE_GAP),
                        row * (BLOCK_SIZE * PALETTE_SCALE + PALETTE_GAP)
                        + PALETTE_GAP)
            scaled_image = pygame.transform.scale(b.image,
                                                  (BLOCK_SIZE * PALETTE_SCALE,
                                                   BLOCK_SIZE * PALETTE_SCALE)
                                                  )
            self.editor_palette.blit(scaled_image, position)
            col += 1
            if col >= EDITOR_PALETTE_WIDTH:
                col = 0
                row += 1

        # Each puzzle within the level also has a number, name
        # and the (x,y) coords for the start positions of player and dog
        # these are stored in a tuple of (name, player_start, dog_start)
        # with the puzzle number as the key
        self.puzzle_info = {}

        # build the layer dictionaries from the level map
        self.load_grid(level=1)
        # set the default starting tile for the editor
        # self.current_editor_tile = self.editor_palette[0]
        self.cursor_block = Block(self.tile_images,
                                  DEFAULT_BLOCK_TYPE,
                                  self.cursor)
        self.erasing = False
        # the selected_blocks list keeps track of the midground blocks that
        # are currently highlighted, when assigning a moveable group
        self.selected_blocks = []
        self.selecting = False
        self.show_grid = False
        self.map_edit_mode = False
        self.current_layer = self.midground_blocks
        self.busy = False  # True when blocks are moving

    def reset(self):
        # reset the whole map to its initial state
        # TODO reset checkpoint flags and other stuff that has changed
        for m in self.movers:
            self.movers[m].reset(self.midground_blocks)
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
        # if we are in linking mode, check if this completes a link
        # this happens when we connect a trigger block to a mover group
        if self.link_trigger:
            b = self.get_block(self.midground_blocks, *self.cursor)
            for m in self.movers:
                if b in self.movers[m].blocks:
                    console_msg("connecting to mover id:"
                                + str(self.movers[m].id), 7)
                    # a mover containing this block exists,
                    # so we can complete the link
                    # but first we must obtain the offset coords
                    # that the mover will be shifted by, when the trigger fires
                    # TODO replace the input with something in-game
                    # we do this by saving the link and the mover as a tuple
                    # ready for the next mouse click to define the offset
                    self.pending_link = (self.link_trigger, self.movers[m])
                    #                    response = input("Enter block offset (x,y):")
                    #                    if response != "":
                    #                        offset = eval(response)
                    #                        self.link_trigger.add_action(self.movers[m], offset)
                    self.link_trigger = None  # exit link mode
        elif self.pending_link:
            # add an action to the pending trigger, that moves the mover
            # to the position of the cursor
            mover = self.pending_link[1]
            mover_anchor = mover.blocks[0]
            trigger = self.pending_link[0]
            offset = (self.cursor[X] - mover_anchor.grid_position[X],
                      self.cursor[Y] - mover_anchor.grid_position[Y])
            trigger.add_action(mover, offset)
            self.pending_link = None  # exit this mode

    def grid_to_screen_pos(self, grid_pos):
        # convert grid coords to screen coords
        return (grid_pos[X] * BLOCK_SIZE
                - self.camera.scroll_x()
                + BLOCK_SIZE / 2,
                grid_pos[Y] * BLOCK_SIZE
                - self.camera.scroll_y()
                + BLOCK_SIZE / 2)

    def add_to_selection(self, mouse_pos):
        self.select_block(mouse_pos, 'add')

    def pick_block(self, mouse_pos):
        self.select_block(mouse_pos, 'pick')

    def select_block(self, mouse_pos, mode='set'):
        """ if mode is 'add', the current block is added to the selection
        otherwise just this block is selected, clearing any previous selection
        """
        self.cursor_to_mouse(mouse_pos)
        b = self.get_block(self.current_layer, *self.cursor)
        if mode == 'add':
            if b:
                self.selected_blocks.append(b)
        elif mode == 'set':
            self.selected_blocks = [b]
        elif mode == 'pick':
            # acts like an eye-drop tool, copying the block tile at
            # the cursor and setting this as the current block that will be
            # used for subsequent block placement
            # if the cursor is over the map, use the current block,
            # but if the cursor is over the palette, use the palette block
            # instead
            if self.get_palette_block(pygame.mouse.get_pos()):
                b = self.get_palette_block(pygame.mouse.get_pos())

            if b:  # avoid setting the cursor block to None
                self.cursor_block.copyTile(b)

    def get_palette_block(self, mouse_pos):
        """ return a block object corresponding to the tile on the palette
        at the mouse position, or None if the mouse isn't over the palette"""
        # we shrink the collision rect by palette_gap, to avoid the annoying
        # case where the pointer is over the very bottom margin of the
        # palette and this causes the selection rectangle to display
        # outside the palette area.
        palette_rect = pygame.Rect(PALETTE_POSITION,
                                   (PALETTE_SIZE[X],
                                    PALETTE_SIZE[Y] - PALETTE_GAP))
        if palette_rect.collidepoint(mouse_pos):
            row = int((mouse_pos[Y] - PALETTE_GAP) /
                      (BLOCK_SIZE * PALETTE_SCALE + PALETTE_GAP))
            col = int((mouse_pos[X] - PALETTE_POSITION[X]) /
                      (BLOCK_SIZE * PALETTE_SCALE + PALETTE_GAP))
            i = col + row * EDITOR_PALETTE_WIDTH
            # print(col, row, i)  # DEBUG
            if i < len(self.palette_blocks):
                return self.palette_blocks[i]
        return None

    def cancel_selection(self):
        self.selected_blocks = []

    def create_mover(self):
        # Create a new moving block group
        mover = Moveable(self.get_next_mover_id(),
                         self.selected_blocks)
        self.movers[mover.id] = mover
        # delete the selection now, because it is saved as a moveable group
        self.selected_blocks = []

    def is_trigger(self):
        """ returns true if the cursor is over a trigger block"""
        b = self.get_block(self.midground_blocks, *self.cursor)
        if not b:
            return False  # bail immediately, since there is no block here
        else:
            # check if this block is a trigger
            return b in [t.block for t in self.triggers]

    def trigger_at_cursor(self):
        """ returns the trigger object linked to the block at the cursor
        or None if there is no trigger there"""
        b = self.get_block(self.midground_blocks, *self.cursor)
        if not b:
            return None  # bail immediately, since there is no block here
        else:
            # check if this block is a trigger
            for t in self.triggers:
                if b == t.block:
                    return t
            return None  # the block is not a trigger

    def toggle_trigger_randomness(self):
        """ if the cursor is on a trigger, toggle the random flag"""
        self.cancel_selection()
        selected_trigger = self.trigger_at_cursor()
        if selected_trigger is not None:
            selected_trigger.toggle_random()

    def set_trigger(self):  # , mouse_pos):
        """ create a trigger at this position
        or add a new action to an existing trigger
        """
        self.cancel_selection()
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

    def get_next_mover_id(self):
        """ returns the next integer in the sequence to make sure that
        every mover has a unique id number.
        We store this number as a class variable and use it as the dict key,
        rather than using a simple list index, so that the id doesn't change
        if movers are later deleted"""
        highest_id = 0
        m = 0
        for m in self.movers:
            if m > highest_id:
                highest_id = m
        return m + 1

    def save_grid(self, level=1):
        """save current grid map to the level file
        this function is only accessible in map editor mode"""
        console_msg("Saving map...", 1, line_end='')

        # TODO add save dialogue to change name/folder
        file_name = LEVEL_MAP_FILE_STEM + str(level) + LEVEL_MAP_FILE_EXTENSION
        backup_file = LEVEL_MAP_FILE_STEM + str(level) + BACKUP_EXTENSION
        # backup the save file to protect against map file corruption
        try:
            os.remove(backup_file)  # delete any previous backup
        except OSError:
            pass  # fail silently
        try:
            os.rename(file_name, backup_file)  # prev save is now the backup
        except OSError:
            pass  # fail silently

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
        preamble = \
            "Level data is split into 6 sections,\n" \
            "each section ends with ### on its own line:\n" \
            "   1. This section is for comments only and is ignored.\n" \
            "   2. The midground section shows the arrangements of " \
            "collidable blocks \n      and triggers.\n" \
            "   3. Foreground layer is drawn on top of the player and " \
            "doesn't collide.\n" \
            "   4. The next section defines the blocks that move when " \
            "triggered.\n" \
            "   5. This section defines the trigger locations, as x, y and\n" \
            "      block group number, each on their own line.\n" \
            "   6. This lists the names of each puzzle on the level,\n" \
            "      and the (x,y) coordinates for the player and dog start " \
            "positions.\n"
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
                        else:  # b is None if not found
                            file.write(' ')
                    file.write('\n')  # new line
                file.write(delimiter)

            # section 4
            file.write("# movers\n")
            for i in self.movers:
                m = self.movers[i]
                file.write(str(m.id) + ", [")  # unique id number
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

            # section 6
            file.write("# puzzle start positions\n")
            for p in self.puzzle_info:
                file.write(str(p) + ', ')  # number
                file.write("'" + self.puzzle_info[p][0] + "', ")  # name
                file.write(str(self.puzzle_info[p][1]) + ', ')  # player
                file.write(str(self.puzzle_info[p][2]))  # dog
                file.write('\n')
            file.write(delimiter)
        console_msg("done", 1)

    def load_grid(self, level=1):
        """read in map data from the level file
        Each screen has room for 15 x 11 tiles
        but a map may be arbitrarily wide
        """
        # midground is the same layer as the player
        # collidable blocks on this layer will stop player progress

        self.level = level
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
        self.movers = {}
        i += 1  # skip over the ### section delimiter
        while i < len(level_data) and level_data[i] != '###':
            if level_data[i][0] != "#":  # comment lines are ignored
                values = eval(level_data[i])
                # create a list of block objects from the list of grid coords
                mover_blocks = [self.get_block(
                    self.midground_blocks, grid[X], grid[Y])
                    for grid in values[1]]
                mover = Moveable(values[0],  # id
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
        self.triggers = []
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
                        t.add_action(self.movers[action[0]], action[1])
                # add the complete trigger to the list maintained by the map
                self.triggers.append(t)
            i += 1

        # Each puzzle within the level also has a number, name
        # and the (x,y) coords for the start positions of player and dog
        # these are stored in a tuple of (name, player_start, dog_start)
        # with the puzzle number as the key
        self.puzzle_info = {}
        i += 1  # skip over the ### section delimiter
        console_msg("Puzzle info:", 8)
        while i < len(level_data) and level_data[i] != '###':
            if level_data[i][0] != "#":  # comment lines are ignored
                values = eval(level_data[i])
                console_msg(values, 8)
                self.puzzle_info[values[0]] = (
                    values[1],
                    values[2],
                    values[3]
                )
            i += 1

    @staticmethod
    def get_block(block_dict, x, y):
        """returns the block at grid coord x,y"""
        if (x, y) in block_dict:
            return block_dict[(x, y)]
        else:
            console_msg("No block found at " + str(x) + "," + str(y), 8)
            return None

    def mover_is_selected(self):
        """ returns true if the cursor is currently on a block that
        is part of a movable group"""
        for m in self.movers:
            if self.get_block(self.current_layer, *self.cursor) in \
                    self.movers[m].blocks:
                return True
        return False

    def trigger_is_selected(self):
        """ returns true if the cursor is currently on a trigger block"""
        if self.get_block(self.current_layer, *self.cursor) in [
            t.block for t in self.triggers
        ]:
            return True
        else:
            return False

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        if not self.show_grid:
            # make sure the edit mode turns off with the grid
            self.map_edit_mode = False

    def toggle_map_editor(self):
        self.map_edit_mode = not self.map_edit_mode
        # make sure grid turns on/off with the editor
        self.show_grid = self.map_edit_mode

    def update(self, surface, scroll):
        """ draw any blocks that are on-screen """

        # calculate the upper and lower bounds of the visible screen
        # so that we don't waste time drawing blocks that are off screen
        min_visible_block_x = scroll[X] // BLOCK_SIZE
        max_visible_block_x = (min_visible_block_x
                               + DISPLAY_SIZE[X] // BLOCK_SIZE
                               + 1)

        # draw each tile in its current location
        for coord in self.midground_blocks:
            if min_visible_block_x <= coord[X] <= max_visible_block_x:
                b = self.midground_blocks[coord]
                # fade out the midground blocks when editing the foreground
                if (self.map_edit_mode and
                        self.current_layer != self.midground_blocks):
                    b.image.set_alpha(100)
                else:
                    b.image.set_alpha(255)
                surface.blit(b.image,
                             (b.x - scroll[X],
                              b.y - scroll[Y]))

                if self.map_edit_mode:
                    # highlight the block if it is currently selected
                    if b in self.selected_blocks:
                        self.highlight_block(surface, b, COLOUR_SELECTED_BLOCK)
                    else:
                        # highlight triggers
                        for t in self.triggers:
                            if b == t.block:
                                self.highlight_block(surface, b, COLOUR_TRIGGER_BLOCK)
                        # highlight moving block groups
                        for m in self.movers:
                            if b in self.movers[m].blocks:
                                self.highlight_block(surface, b,
                                                     COLOUR_MOVING_BLOCK)

        for coord in self.foreground_blocks:
            if min_visible_block_x <= coord[X] <= max_visible_block_x:
                b = self.foreground_blocks[coord]
                # fade out the foreground blocks when editing the midground
                if (self.map_edit_mode and
                        self.current_layer != self.foreground_blocks):
                    b.image.set_alpha(100)
                else:
                    b.image.set_alpha(255)
                surface.blit(b.image,
                             (b.x - scroll[X],
                              b.y - scroll[Y]))

        # give any moving blocks a chance to update
        # if any are currently moving, we set busy to true, so that
        # the player program is paused until the moves are complete
        # and also tell the camera to shake
        self.busy = False
        self.camera.set_shaking(False)
        for m in self.movers:
            if self.movers[m].update(self.midground_blocks):
                self.busy = True
                self.camera.set_shaking(True)

        if self.map_edit_mode:
            # if we are in trigger linking mode, run a line from the
            # cursor to the trigger block
            if self.link_trigger:
                pygame.draw.line(surface, COLOUR_NEW_LINK,
                                 (pygame.mouse.get_pos()[X] / SCALING_FACTOR,
                                  pygame.mouse.get_pos()[Y] / SCALING_FACTOR),
                                 self.grid_to_screen_pos(
                                     self.link_trigger.block.grid_position), 1)
            # if we are in pending link mode, draw an arrow from the
            # anchor block in a mover to the cursor, so that we can specify
            # where the mover should move to
            elif self.pending_link:
                mover_pos = self.pending_link[1].blocks[0].grid_position
                mouse_pos = (pygame.mouse.get_pos()[X] / SCALING_FACTOR,
                             pygame.mouse.get_pos()[Y] / SCALING_FACTOR)

                # draw the arrow
                arrow(surface,
                      COLOUR_MOVER_OFFSET,
                      COLOUR_MOVER_OFFSET,
                      self.grid_to_screen_pos(mover_pos),
                      mouse_pos,
                      8,
                      )

            # draw lines from each trigger to its movers
            for t in self.triggers:
                trigger_pos = self.grid_to_screen_pos(t.block.grid_position)
                for a in t.actions:
                    mover_pos = self.grid_to_screen_pos(
                        a[0].blocks[0].grid_position
                    )
                    if t.random:
                        pygame.draw.line(surface, COLOUR_RANDOM_LINK,
                                         trigger_pos, mover_pos)
                    else:
                        pygame.draw.line(surface, COLOUR_NORMAL_LINK,
                                         trigger_pos, mover_pos)

    def highlight_block(self, surface, block, colour):
        left = block.x - self.camera.scroll_x()
        top = block.y - self.camera.scroll_y()
        # the block x,y values are for the top left corner of the block
        # so we need to add one extra block's worth for the full
        # width/height
        b_rect = pygame.Rect(left, top, BLOCK_SIZE, BLOCK_SIZE)
        # blend the highlight colour with the selected block image
        surface.fill(colour, b_rect, pygame.BLEND_RGB_ADD)

    def draw_edit_info_box(self, surface):
        """ overlays the panel showing the currently selected layer
        and block tile"""
        info_box = pygame.Rect(0, 0, 182, 104)
        text_colour = COLOUR_MAP_EDIT_TEXT
        surface.fill(COLOUR_MAP_EDITOR_BOXES,
                     info_box)  # pygame.BLEND_RGB_ADD)
        # add a label to say which block layer is currently selected
        if self.current_layer == self.midground_blocks:
            self.display_text("midground layer", (4, 0), text_colour)
        else:
            self.display_text("foreground layer", (4, 0), text_colour)
        # display currently selected tile
        # remembering to scale it, since we are drawing on the
        # unscaled surface
        self.cursor_block.image.set_alpha(255)  # force opacity to max
        surface.blit(pygame.transform.scale(self.cursor_block.image,
                                            (BLOCK_SIZE * SCALING_FACTOR,
                                             BLOCK_SIZE * SCALING_FACTOR)),
                     (10, 28))

        # draw block palette
        # currently anchored at the top of the screen
        surface.blit(self.editor_palette, PALETTE_POSITION)
        # draw selection rectangle, if the mouse is over the palette
        if self.get_palette_block(pygame.mouse.get_pos()):
            m = pygame.mouse.get_pos()  # for brevity
            left = (((m[X] - PALETTE_POSITION[X]) // PALETTE_CURSOR_SIZE[X])
                    * PALETTE_CURSOR_SIZE[X]
                    + PALETTE_POSITION[X]
                    - PALETTE_GAP)
            top = (((m[Y] - PALETTE_POSITION[Y]) // PALETTE_CURSOR_SIZE[Y])
                   * PALETTE_CURSOR_SIZE[Y]
                   + PALETTE_POSITION[Y])
            size = PALETTE_CURSOR_SIZE
            selection_rect = pygame.Rect((left, top), size)
            pygame.draw.rect(surface,
                             COLOUR_MAP_CURSOR,
                             selection_rect,
                             PALETTE_GAP * 2)

    def draw_grid(self, surface, origin):
        """ overlays a grid to show the block spacing """
        scroll = self.camera.scroll()  # for brevity
        grid_size = BLOCK_SIZE * SCALING_FACTOR
        grid_colour = COLOUR_GRID_LINES
        offset = [(s * SCALING_FACTOR) % grid_size for s in scroll]
        limit = [size * SCALING_FACTOR for size in DISPLAY_SIZE]
        label_offset = (grid_size / 2 - self.world.editor.char_width,
                        grid_size / 2 - self.world.editor.line_height / 2)
        # make sure grid lines don't cover the input box
        if self.world.input.is_active():
            input_offset = self.world.input.height + 2
        else:
            input_offset = 2  # the 2 is a fudge factor to tidy things up
        # vertical grid lines & X-axis labels
        for x in range(-offset[X], limit[X] - offset[X], grid_size):
            pygame.draw.line(surface, grid_colour,
                             (x, 0),
                             (x, limit[Y] + origin[Y] - input_offset),
                             GRID_LINE_WIDTH)
            axis_label = "{0:2d} ".format(int(x / grid_size + scroll[X] / BLOCK_SIZE))
            self.display_text(axis_label, (x + label_offset[X], 20), grid_colour)

        # horizontal grid lines & Y-axis labels
        for y in range(-offset[Y], limit[Y] - input_offset, grid_size):
            pygame.draw.line(surface, grid_colour,
                             (0, y + origin[Y]),
                             (limit[X], y + origin[Y]),
                             GRID_LINE_WIDTH)
            if y + label_offset[Y] < limit[Y] - input_offset - LABEL_HEIGHT:
                axis_label = "{0:2d} ".format(int(y / grid_size + scroll[Y] / BLOCK_SIZE))
                self.display_text(axis_label,
                                  (GRID_LINE_WIDTH * 2,
                                   y + origin[Y] + label_offset[Y]),
                                  grid_colour
                                  )

        if self.map_edit_mode:
            self.cursor_rect.x = (self.cursor[X] * grid_size
                                  - scroll[X] * SCALING_FACTOR
                                  + GRID_LINE_WIDTH)
            self.cursor_rect.y = (self.cursor[Y] * grid_size
                                  - scroll[Y] * SCALING_FACTOR
                                  + origin[Y] + GRID_LINE_WIDTH)

            # highlight cursor
            pygame.draw.rect(surface, COLOUR_MAP_CURSOR,
                             self.cursor_rect,
                             GRID_LINE_WIDTH)
            # add grid coords of cursor
            cursor_label = "({0},{1})".format(self.cursor[X], self.cursor[Y])
            self.display_text(cursor_label,
                              (self.cursor_rect[X], self.cursor_rect[Y] - 25),
                              grid_colour)

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
            int(self.camera.scroll_x() / BLOCK_SIZE
                + DISPLAY_SIZE[X] / BLOCK_SIZE / 2),
            int(self.camera.scroll_y() / BLOCK_SIZE
                + DISPLAY_SIZE[Y] / BLOCK_SIZE / 2)
        ]

    def blank_editor_tile(self):
        self.change_block(erasing=True)

    def change_block(self, erasing=False):
        """ changes the block at the cursor location to the current
        cursor block. If erasing is True, remove the block entirely."""
        existing_block = self.get_block(self.current_layer, *self.cursor)
        if erasing:
            if existing_block:
                # remove the block
                # need to turn the cursor list object into a tuple
                # so that it can be used to access the dict
                self.current_layer.pop((self.cursor[X], self.cursor[Y]))
        else:
            if existing_block:
                existing_block.setType(self.cursor_block.type)
            else:
                # create new block that is a clone of the currently
                # selected block shown in the edit info box
                b = self.cursor_block.clone(self.cursor_block,
                                            self.cursor)
                # create a tuple from the cursor list object
                # so that it can be used as a dict index
                # then assign current block tile to this index
                self.current_layer[(self.cursor[X], self.cursor[Y])] = b

    def delete(self):
        # removes an object, depending on what is at the cursor
        if self.mover_is_selected():
            console_msg("deleting mover", 8)
            self.remove_moveable_group()
        elif self.trigger_is_selected():
            console_msg("deleting trigger", 8)
            self.remove_trigger()
        else:
            self.blank_editor_tile()

    def remove_moveable_group(self):
        """ Remove the moveable block group from the map
        if the cursor is currently over any of the blocks, the entire
        group is removed.
        The blocks themselves are not affected - they just don't count
        as a movable group anymore.
        """
        existing_block = self.get_block(self.current_layer, *self.cursor)
        if existing_block:
            for m in self.movers.copy():
                if existing_block in self.movers[m].blocks:
                    # delete connections to any triggers
                    for t in self.triggers:
                        if t.is_linked_to(self.movers[m]):
                            t.remove_mover_actions(self.movers[m])
                    # only keep triggers that still have links
                    amended_trigger_list = [t for t in self.triggers
                                            if t.actions_count() > 0]
                    self.triggers = amended_trigger_list

                    # delete the mover itself
                    del (self.movers[m])
                    break

    def remove_trigger(self):
        """ Remove any and all triggers that are attached to this block
        The block itself is not affected - it just doesn't count
        as a trigger anymore.
        """
        existing_block = self.get_block(self.current_layer, *self.cursor)
        if existing_block in [t.block for t in self.triggers]:
            amended_trigger_list = [
                # keep all triggers except the one to delete
                t for t in self.triggers if t.block != existing_block
            ]
            self.triggers = amended_trigger_list

    def insert_column(self):
        """ add a new column of blocks at the current cursor """
        insert_col = self.cursor[X]  # for brevity
        self.reset()  # make sure we start from the neutral map position
        # update the block positions themselves
        # only need to do this for blocks at or beyond the inserting column
        # but we must do this for both the block maps
        all_maps = [self.foreground_blocks, self.midground_blocks]
        for this_map in all_maps:
            # find the highest x value in the map
            max_col = 0
            for coord in this_map:
                if coord[X] > max_col:
                    max_col = coord[X]
            # iterate over the map, starting at the right and working leftwards
            for col in range(max_col, insert_col - 1, -1):
                # check each block in the map for a matching x coord
                for coord in this_map.copy():
                    if coord[X] == col:
                        b = this_map[coord]
                        del this_map[coord]  # remove at old key
                        b.set_grid_position((coord[X] + 1,  # move block
                                             coord[Y]))
                        this_map[b.grid_position] = b  # add at new key

        # Movers shouldn't need to be changed much, since their blocks
        # are held in a list, not a dictionary
        # but we need to update the home (pixel) coords of each block
        # so the reset() method works correctly
        for mover_id in self.movers:
            self.movers[mover_id].home_positions = []
            for b in self.movers[mover_id].blocks:
                self.movers[mover_id].home_positions.append((b.x, b.y))

        # Triggers shouldn't need updating, since they are held in a list
        # and their block coord should already have been updated

    def delete_column(self):
        """ remove the column at the current cursor """
        delete_col = self.cursor[X]  # for brevity
        self.reset()  # make sure we start from the neutral map position
        # update the block positions themselves
        # only need to do this for blocks at or beyond the inserting column
        # but we must do this for both the block maps
        all_maps = [self.foreground_blocks, self.midground_blocks]
        for this_map in all_maps:
            # find the highest x value in the map
            max_col = 0
            for coord in this_map:
                if coord[X] > max_col:
                    max_col = coord[X]
            # iterate over the map, starting from the deletion point
            for col in range(delete_col, max_col + 1):
                # check each block in the map for a matching x coord
                for coord in this_map.copy():
                    if coord[X] == col:
                        b = this_map[coord]
                        del this_map[coord]  # remove at old key
                        b.set_grid_position((coord[X] - 1,  # move block
                                             coord[Y]))
                        this_map[b.grid_position] = b  # add at new key

        # Movers shouldn't need to be changed much, since their blocks
        # are held in a list, not a dictionary
        # but we need to update the home (pixel) coords of each block
        # so the reset() method works correctly
        for mover_id in self.movers:
            self.movers[mover_id].home_positions = []
            for b in self.movers[mover_id].blocks:
                self.movers[mover_id].home_positions.append((b.x, b.y))

        # Triggers shouldn't need updating, since they are held in a list
        # and their block coord should already have been updated

    def collision_test(self, character_rect):
        """ check if this character is colliding with any of the blocks
        blocks are categorised as:
        collidable - collision physics applies to characters
        trigger - characters can overlap the block, activating the trigger
        cosmetic - no collision physics or trigger (but may animate)
        """
        if SHOW_COLLIDERS:
            # DEBUG draw character collider in green
            self.draw_collider(self.world.display,
                               (0, 255, 0), character_rect, 1)

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
                        self.draw_collider(self.world.display,
                                           (255, 255, 0),
                                           collider, 1)

                    if character_rect.colliderect(collider):
                        collisions.append(b)

                        # DEBUG draw active colliders in red
                        if SHOW_COLLIDERS:
                            self.draw_collider(self.world.display,
                                               (255, 0, 0),
                                               collider, 0)

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

    def get_puzzle_name(self, puzzle_number):
        if puzzle_number not in self.puzzle_info:  # validation check
            puzzle_number = 0
        return self.puzzle_info[puzzle_number][PUZZLE_NAME]

    def get_player_start(self, puzzle_number):
        if puzzle_number not in self.puzzle_info:
            puzzle_number = 0
        return self.puzzle_info[puzzle_number][PLAYER_START]

    def get_dog_start(self, puzzle_number):
        if puzzle_number not in self.puzzle_info:
            puzzle_number = 0
        return self.puzzle_info[puzzle_number][DOG_START]

    def draw_collider(self, surface, colour, collider, width):
        """ debug routine to show colliders"""
        if SHOW_COLLIDERS:
            rect = pygame.Rect(collider.x - self.camera.scroll_x(),
                               collider.y - self.camera.scroll_y(),
                               collider.width,
                               collider.height)
            pygame.draw.rect(surface, colour, rect, width)


def arrow(screen, line_color, arrowhead_color, start, end, arrowhead_radius):
    # draws a line with a triangular arrow head
    # pinched from
    # https://stackoverflow.com/questions/43527894/drawing-arrowheads-which-follow-the-direction-of-the-line-in-pygame
    pygame.draw.line(screen, line_color, start, end, 1)
    rotation = math.degrees(
        math.atan2(start[1] - end[1], end[0] - start[0])) + 90
    pygame.draw.polygon(screen, arrowhead_color,
                        ((end[0],
                          end[1]),
                         (end[0] + arrowhead_radius * math.sin(
                             math.radians(rotation - 160)),
                          end[1] + arrowhead_radius * math.cos(
                              math.radians(rotation - 160))),
                         (end[0] + arrowhead_radius * math.sin(
                             math.radians(rotation + 160)),
                          end[1] + arrowhead_radius * math.cos(
                              math.radians(rotation + 160)))))
