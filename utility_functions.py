# static helper functions used in various places

from constants import *

def grid_to_screen(grid_coords, scroll, offset):
    # converts grid coords to pixel coords,
    # taking scroll into account
    x = (grid_coords[X] * BLOCK_SIZE - scroll[X]) * SCALING_FACTOR + offset[X]
    y = (grid_coords[Y] * BLOCK_SIZE - scroll[Y]) * SCALING_FACTOR + offset[Y]
    return (x,y)

def screen_to_grid(screen_coords, scroll):
    scaled_mouse_pos = (screen_coords[X] // SCALING_FACTOR,
                        screen_coords[Y] // SCALING_FACTOR)
    return ((scaled_mouse_pos[X] + scroll[X]) // BLOCK_SIZE,
            (scaled_mouse_pos[Y] + scroll[Y]) // BLOCK_SIZE)