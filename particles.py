# particle system for BIT rocket exhaust etc
import time
from random import randint

import pygame
from constants import *

class Mote:
    """ a single generic particle """

    def __init__(self, velocity, type='spark', offset = [0,0]):
        self.TERMINAL_VELOCITY = 1.0
        self.offset = offset.copy()  # position relative to the stream origin
        self.initial_velocity = velocity
        self.velocity = self.initial_velocity.copy()
        self.type = type
        self.age = randint(0, 20)  # start some particles older, for variety
        self.colour_table = {
            0: (218, 238, 239),
            1: (255, 255, 255),
            2: (237, 184, 121),
            3: (224, 123, 57),
            4: (128, 57, 30),
            5: (142, 117, 110),
        }

    def update(self):
        self.age += 1
        self.offset[X] += self.velocity[X]
        self.offset[Y] += self.velocity[Y]
        if self.type == 'dust':  # dust is subject to gravity
            self.velocity[Y] += GRAVITY
            if self.velocity[Y] > self.TERMINAL_VELOCITY:
                self.velocity[Y] = self.TERMINAL_VELOCITY

    def reset(self, origin = [0,0]):
        # turn this mote back into a fresh, new one
        self.age = randint(0, 20)
        self.offset = origin.copy()
        self.velocity = self.initial_velocity.copy()
        self.type = 'spark'

    def turn_to_dust(self):
        self.type = 'dust'
        self.velocity = [self.velocity[X] * 2,
                         self.velocity[Y] * randint(80, 150) / 100]

    def get_colour(self):
        if self.type == 'spark':
            # particles vary from white, to red as they age
            # colour = (255, 255-p.age*7, 255- p.age*7)
            colour_index = int(self.age / 7)
            if colour_index > 5:
                colour_index = 5
            return self.colour_table[colour_index]
        else:
            return self.colour_table[5]  # dust motes are all 1 colour

class Jet:
    """ a stream of particles that emerge from a point and slow down as
    they move through the air. If they strike a collidable surface, they will
    bounce and become subject to gravity"""

    def __init__(self, world, nozzle, velocity, intensity = 100):
        """ create a new jet with a certain direction and speed
        nozzle is the origin of the jet [X, Y]
        direction is the [X,Y] vector
        speed is the initial exhaust velocity
        intensity is the number of particles on the screen at once
        """
        self.world = world  # link to the game environment to allow collisions
        self.active = False  # initially off, call turn_on() to activate
        self.power = 0.0
        self.nozzle = [nozzle[X], nozzle[Y]]
        self.velocity = velocity
        self.intensity = intensity
        self.particles = []
        self.MOTE_LIFETIME = 35  # how many frames the motes exist for
        self.SPRAY_WIDTH = 0.01
        self.RAMP_UP_RATE = 0.1
        # prepopulate the jet with particles
        for i in range(self.intensity):
            velocity = [randint(-20, 20) * self.SPRAY_WIDTH, 1]
            self.particles.append(Mote(velocity))


    def update(self, surface, scroll):
        if self.active:
            for p in self.particles:
                # update position and age
                p.update()
                x = int(self.nozzle[X] + p.offset[X])
                y = int(self.nozzle[Y] + p.offset[Y])

                if self.world.blocks.point_collision_test((x,y)):
                    p.velocity[Y] = -p.velocity[Y]
                    p.offset[Y] += p.velocity[Y] * 2  # move out of collision
                    # turn this particle from a spark into dust
                    p.turn_to_dust()
                else:
                    # draw
                    pygame.draw.circle(surface, p.get_colour(),
                                       (x - scroll[X],
                                       y - scroll[Y]),
                                       1)

                    # remove any that are too old - should this be in its own loop?
                    if p.age > self.MOTE_LIFETIME:
                        p.reset()

    def turn_off(self):
        self.power = 0.0
        self.active = False

    def turn_on(self):
        self.active = True

    def is_active(self):
        # this checks the number of particles, rather than simply querying
        # self.active, so that the jet continues to update after calling
        # turn_off() until all the particles have aged out
        # TODO the test for len(self.particles) doesn't work
        # because the list is prepopulated with the max particles and they
        # are never removed - they just age and reset.
        # try removing this test after block collision is working ok
        # because currently it is wasting time checking jets
        # even on the player character, which doesn't have any!
        if self.active or len(self.particles) > 0:
            return True
        else:
            return False

    def get_power(self):
        # ramps up the power when the jet is activated
        if self.power < 1.0 and self.active:
            self.power += self.RAMP_UP_RATE
        return self.power

class DustStorm():
    """ motes that blow left to right across the whole play area """

    def __init__(self, world, intensity = 20):
        """ create a new storm of dust motes
        intensity is the number of particles on the screen at once
        """
        self.world = world  # link to the game environment to allow collisions
        self.active = True  # initially on
        self.intensity = intensity
        self.particles = []
        self.MOTE_LIFETIME = 35  # how many frames the motes exist for
        # prepopulate the storm with particles
        for i in range(self.intensity):
            velocity = [randint(0, 10), 0.1]
            origin = [0, randint(0, DISPLAY_SIZE[Y])]
            self.particles.append(Mote(velocity, 'dust', origin))


    def update(self, surface, y_origin, scroll):
        if self.active:
            for p in self.particles:
                # update position and age
                p.update()
                x = int(p.offset[X])
                y = int(p.offset[Y])

                if self.world.blocks.point_collision_test((x,y)):
                    p.velocity[Y] = -p.velocity[Y]
                    p.offset[Y] += p.velocity[Y] * 2  # move out of collision
                    # turn this particle from a spark into dust
                    p.turn_to_dust()
                else:
                    # draw
                    pygame.draw.circle(surface, p.get_colour(),
                                       (x - scroll[X],
                                       y - scroll[Y]),
                                       1)

                    # remove any that are too old - should this be in its own loop?
                    if p.age > self.MOTE_LIFETIME:
                        p.reset([0, randint(y_origin,
                                            WINDOW_SIZE[Y] - y_origin)])
