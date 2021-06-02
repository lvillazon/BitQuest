import random
import pygame

from characters import Person
from console_messages import console_msg
from constants import *


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
        # when random == false, it activates all actions at once, every time
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

    def toggle_random(self):
        self.random = not self.random
        if self.random:
            self.pick_an_action()

    def is_linked_to(self, mover):
        """ returns true if the trigger contains an action for this mover"""
        if mover in [a[0] for a in self.actions]:
            return True
        else:
            return False

    def add_action(self, mover, movement):
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

    def remove_mover_actions(self, mover):
        """ delete any actions that reference this mover """
        amended_actions = [a for a in self.actions if a[0] != mover]
        self.actions = amended_actions

    def actions_count(self):
        """ number of actions attached to this trigger"""
        return len(self.actions)

    def check(self, character):
        """ check if the trigger has activated
        for now this just handles the pressure plate type of trigger
        others will be added - possibly by subclassing this
        """
        if self.type == 'pressure plate':
            trigger_rect = pygame.Rect(self.block.x,
                                       self.block.y,
                                       BLOCK_SIZE, BLOCK_SIZE)
            if character.location.colliderect(trigger_rect):
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

class Flagpole(Trigger):
    """ crossing this signifies the end of the level """

    def __init__(self, world, name, blocks):
        # the first block in the list corresponds to
        # the actual trigger location (bottom, left of the flagpole base)
        super().__init__(world, 'flagpole', False, blocks[0])
        self.name = name
        self.activated = False
        self.blocks = blocks
        self.frame_number = 0
        self.frame_count = len(blocks[0].frames)
        self.flap_count = 1
        self.text_area = None

    def reset(self):
        # override default behaviour, since flagpoles are unaffected by reset
        # but we replay the unfurling animation of any activated flagpoles
        # just because it looks nice and provides a visual hint of the
        # current progress
        self.flap_count = 1
        self.frame_number = 0

    def check(self, character):
        # check if the flagpole has been activated
        trigger_rect = pygame.Rect(self.blocks[0].x,
                                   self.blocks[0].y,
                                   BLOCK_SIZE, BLOCK_SIZE)
        if (isinstance(character, Person) and
                not self.activated and
                character.location.colliderect(trigger_rect)):
            # unfurl the flag
            console_msg(self.name + " complete!", 1)
            # pass the level name to the save function
            self.world.complete_level(self.name)
            self.activated = True
        elif self.activated:
            # update the animation frame for the waving effect
            if self.flap_count > 0:
                self.frame_number = self.frame_number + .1
                if self.frame_number >= self.frame_count:
                    self.frame_number = 4.0
                    self.flap_count -= 1

                f = int(self.frame_number)
                for b in self.blocks:
                    b.image = b.frames[f]
