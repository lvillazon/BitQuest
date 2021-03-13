import random

from constants import *


class Camera(object):
    # the virtual camera tracks the focus character, but with a bit of lag
    # the view can also be manually panned using the keyboard

    def __init__(self):
        self._true_scroll = [0.0, 0.0]  # float version to allow for subpixel changes
        self._scroll = [0, 0]  # the actual value used to offset the display
        self._shake = False  # true when the camera should be shaking
        self._camera_pan = [0, 0]  # the amount of manual panning

    def update(self, focus):
        self._true_scroll[X] += (focus.location.x -
                                 self._true_scroll[X] - CAMERA_X_OFFSET) / 16
        if self._true_scroll[X] < 0:
            # can't scroll past the start of the world
            self._true_scroll[X] = 0
        self._true_scroll[Y] += (focus.location.y -
                                 self._true_scroll[Y] - CAMERA_Y_OFFSET) / 16
        self._scroll = [int(self._true_scroll[X]) + self._camera_pan[X],
                        int(self._true_scroll[Y]) + self._camera_pan[Y]]
        if self._shake:
            self._scroll[X] += random.randint(-1, 1)
            self._scroll[Y] += random.randint(-1, 1)

    def scroll(self):
        # return both scroll coordinates, as a tuple
        return self._scroll

    def scroll_x(self):
        # return current X scroll value
        return self._scroll[X]

    def scroll_y(self):
        # return current Y scroll value
        return self._scroll[Y]

    def start_shaking(self):
        self._shake = True

    def stop_shaking(self):
        self._shake = False
