""" movement and animation for all the player and npc sprites """
import math
import random

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
    when a trigger activates. They are simply arbitrary collections
    of blocks that move in concert when activated."""

    def __init__(self, world, id, blocks):
        self.world = world  # so we can set camera_shake
        self.id = id  # unique number used for loading/saving
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
            # TODO what happens without this? It seems ok, but test when we ride a platform moving downwards
            # uncommenting it causes blocks moving up, to drift out of sync with the grid
            #if self.target_offset[Y] <0:  # moving up
            #    b.movement[Y] -= GRAVITY

    def reset(self):
        # return all blocks to their orginal (pre-triggered) locations
        for i in range(len(self.blocks)):
            if self.blocks[i]:  # guard against a null block in the list
                self.blocks[i].x = self.home_positions[i][X]
                self.blocks[i].y = self.home_positions[i][Y]
                self.activated = False
                self.target_offset = [0.0, 0.0]
                self.current_offset = [0.0, 0.0]
                self.movement = [0.0, 0.0]

    def update(self):
        """ move the blocks if this group has been triggered
        if the group is moving it returns True, otherwise False """
        if self.activated and self.movement != [0.0, 0.0]:
            for b in self.blocks:
                b.x += self.movement[X]
                b.y += self.movement[Y]
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
                return False
            else:
                return True

    def get_bounding_box(self):
        """ return a rectangle surrounding this group of blocks """
        left = self.blocks[0].x - self.world.scroll[X]
        top = self.blocks[0].y - self.world.scroll[Y]
        # the block x,y values are for the top left corner of the block
        # so we need to add one extra block's worth for the full width/height
        width = self.blocks[-1].x - self.world.scroll[X] - left + BLOCK_SIZE
        height = self.blocks[-1].y - self.world.scroll[Y] - top + BLOCK_SIZE
        return pygame.Rect(left, top, width, height)


class Trigger:
    """ contains the logic that handles the activation of the
    Moveable groups. Triggers are usually associated with a specific
    block, such as a pressure plate. But there may be others, such as
    laser tripwires that are activated when a character crosses that
    entire row or column."""

    def __init__(self, world, type, random, block):
        self.world = world
        self.type = type  # a string, eg 'pressure plate'
        self.block = block
        self.enabled = True
        # when random == true, the trigger sets random_action to one
        # of its possible actions. It will use this one until the trigger is
        # reset, when it will pick another one at random
        # when random == false, it activates all at once, every time
        self.random = random
        self.actions = []
        if self.random:
            self.pick_an_action()

    def pick_an_action(self):
        if self.actions:
            self.random_action = random.choice(self.actions)
        else:
            self.random_action = None

    def reset(self):
        self.enabled = True
        self.block.image = self.block.frames[0]
        if self.random:
            self.pick_an_action()

    def addAction(self, mover, movement):
        """ create an action - a mover + an (x,y) movement
        This is expressed as a call to the activate method of the mover
        When the trigger fires, this method is called to set off the mover
        """
        self.actions.append((mover, movement))
        # adding a new action causes random triggers to pick which one to use
        # at random. That way, the action is always chosen from the most
        # recent set of available actions
        if self.random:
            self.pick_an_action()

    def check(self, character_rect):
        """ check if the trigger has activated
        for now this just handles the pressure plate type of trigger
        others will be added - possibly by subclassing this
        """
        if self.type == 'pressure plate':
            trigger_rect = pygame.Rect(self.block.x,
                                       self.block.y,
                                       BLOCK_SIZE, BLOCK_SIZE)
            if character_rect.colliderect(trigger_rect):
                # switch to 'pressed' state
                self.block.image = self.block.frames[1]
                if self.random:
                    if not self.random_action[0].activated:
                        self.random_action[0].activate(self.random_action[1])
                else:
                    # fire all actions associated with this trigger
                    for action in self.actions:
                        if not action[0].activated:
                            # the action is a tuple of mover and movement
                            # so we call the activate method of the mover
                            # and pass the movement as the argument
                            action[0].activate(action[1])
                console_msg(
                    "trigger "
                    + "(" + str(self.block.x) + str(self.block.y) + ")"
                    + " activated!", 8)
                if SHOW_COLLIDERS:
                    # DEBUG draw block colliders in yellow
                    draw_collider(self.world.display,
                                  (255, 255, 0),
                                  trigger_rect, 1, self.world.scroll)

    def draw_bounding_box(self, surface):
        """ draw an outline around the trigger and each of its
        associated moveable groups of blocks, with lines connecting them """
        colour = (0, 0, 255)  # blue
        left = self.block.x - self.world.scroll[X]
        top = self.block.y - self.world.scroll[Y]
        # the block x,y values are for the top left corner of the block
        # so we need to add one extra block's worth for the full width/height
        t_rect = pygame.Rect(left, top, BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(surface, colour, t_rect, 1)

        # TODO fix the connecting lines from triggers to movers
        # draw connecting lines to all associated movers
#        for m in self.movers:
#            m_rect = m.get_bounding_box()
#            pygame.draw.rect(surface, colour, m_rect, 1)
#            pygame.draw.line(surface, colour,
#                             (t_rect.left, t_rect.top),
#                             (m_rect.left, m_rect.top)
#                             )


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
        self.movement = [0, 0]

    def top(self):
        return self.y

    def bottom(self):
        return self.y + BLOCK_SIZE

    def left(self):
        return self.x

    def right(self):
        return self.x + BLOCK_SIZE



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
        # TODO check if we still need this - isn't everything on the midground layer collideable?
        if self.type not in '-{|/}=':
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

        self.tile_sheet = sprite_sheet.SpriteSheet('assets/' + TILE_FILE)

        # store blocks in a dict indexed by grid position
        # this gives way better performance than a simple list
        # because collisions can check just the blocks in the
        # immediate vicinity, instead of searching the entire map
        self.midground_blocks = {}
        self.foreground_blocks = {}

        # movers are indexed by their (left, top, width height) tuple
        self.movers = {}
        # triggers aren't a dict, because I'm not sure what to index them with
        # - we might want triggers that aren't associated with a specific block
        self.triggers = []
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
        self.load_grid()  # build the layer dictionaries from the level map
        # set the default starting tile for the editor
        self.current_editor_tile = self.editor_palette[0]
        self.cursor_block = Block(self.tile_images,
                                  self.current_editor_tile,
                                  self.cursor)
        self.erasing = False
        self.selection = []
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

    def begin_selection(self):
        self.selection = [(self.cursor[X], self.cursor[Y])]

    def cancel_selection(self):
        self.selection = []

    def end_selection(self):
        # Create a new moving block group
        # they are defined by their (left, top) & (right, bottom) coords
        # in the block coordinate system
        # plus a move direction as a string
        # and a number of blocks to move
        self.selection.append((self.cursor[X], self.cursor[Y]))
        print("Blocks", self.selection[0], "to", self.selection[1], "selected")
        response = input("Enter trigger block coords:")
        if response != "":
            trigger_pos = eval(response)
            direction = \
                input("Enter direction to move (up/down/left/right):").lower()
            distance = int(input("Enter number of blocks to move:"))

            mover = Moveable(self, self.world,
                             (self.selection[0], self.selection[1]),
                             direction,
                             distance)
            self.movers[(self.selection[0], self.selection[1])] = mover

            # assign a trigger to this block group
            # the trigger needs:
            # 1. the trigger type (currently always 'pressure plate')
            # 2. the block object for the pressure plate tile
            # 3. a list of all the movers associated with it
            t = Trigger(self.world,
                        'pressure plate',
                        self.get_block(self.midground_blocks, *trigger_pos)
                        )
            # associate this mover with this trigger
            # TODO allow new movers to be associated with an existing trigger
            t.addMover(mover)
            # add the complete trigger to the list maintained by the map
            self.triggers.append(t)


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
            if level_data[i][0] != "#": # comment lines are ignored
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
            if level_data[i][0] != "#": # comment lines are ignored
                values = eval(level_data[i])
                console_msg(values, 8)
                t = Trigger(self.world,
                            values[0],  # type
                            values[1],  # random flag
                            # block object representing the trigger location
                            self.get_block(self.midground_blocks,
                                           values[2][X], values[2][Y])
                            )
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
                               +1)

        # draw each tile in its current location
        for coord in self.midground_blocks:
            if min_visible_block_x <= coord[X] <= max_visible_block_x:
                b = self.midground_blocks[coord]
                surface.blit(b.image,
                             (b.x - self.world.scroll[X],
                              b.y - self.world.scroll[Y]))
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
            if self.movers[m].update():
                self.busy = True

        if self.busy:
            # also must update the block dictionary, since it is keyed
            # by the block coords
            # we do this by iterating over a copy of the dictionary keys
            # so that we can modify the dictionary on the fly without
            # throwing runtime errors. This approach has fairly low
            # performance cost, since it only runs while a mover is moving
            # and only changes the dictionary when the blocks have moved
            # enough to change their position by a whole grid square.
            for coord in self.midground_blocks.copy():
                block = self.midground_blocks[coord]
                if block.grid_position != coord:
                    print("Block at", coord, "has moved to",
                          block.grid_position)
                    self.midground_blocks[block.grid_position] = block
                    del self.midground_blocks[coord]

        if MAP_EDITOR_ENABLED and self.show_grid:
            # draw boxes around each trigger and mover
            # with lines connecting them
            for t in self.triggers:
                t.draw_bounding_box(surface)

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
                                          self.world.scroll[X] / BLOCK_SIZE))
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
                                            self.world.scroll[Y] / BLOCK_SIZE))
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

    def collision_test(self, character_rect, movement):
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
            if abs(coord[X] - (character_rect.centerx // BLOCK_SIZE)) <= 1:
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

        # create a list of the blocks immediately surrounding the character
        adjacent_blocks = []

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
                        # just because the rectangles overlap, doesn't necessarily
                        # mean we want to call it a collision. We only count collisions
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

    def trigger_test(self, character_rect, movement):
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
