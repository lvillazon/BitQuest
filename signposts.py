from constants import *
from text_panel import TextPanel


class Signposts:
    """ the info signs used to give instructions on each level
    Each one has text that will display in a pop-up window,
    when the signpost is clicked """

    class _Post:
        def __init__(self, grid_positions, text):
            self.grid_positions = grid_positions
            self.text = text
            self.open = False  # true when the text pop-up is displayed
            self.text_panel = None

    def __init__(self, font, fg_color, bg_color):
        self.font = font
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.all_posts = []
        self.add_signpost((10,7),
                          "Puzzle 1:\ntest")
        # TODO if we need extra performance, replace the all_post list
        #  with a dictionary that uses post grid coords as the key

    def add_signpost(self, pos, text):
        # add all the grid squares occupied by the signpost
        # based on the top-left grid square pos
        grid_positions = [pos,
                          (pos[X]+1, pos[Y]),
                          (pos[X], pos[Y]+1),
                          (pos[X]+1, pos[Y]+1)]
        self.all_posts.append(self._Post(grid_positions, text))

    def get_signpost_at(self, screen_coords, scroll):
        # returns the signpost under the mouse cursor, if any
        # or None
        grid_pos = screen_to_grid(screen_coords, scroll)
        for p in self.all_posts:
            if grid_pos in p.grid_positions:
                return p
        return None

    def check_for_signpost_at(self, screen_coords, scroll):
        # opens any signpost at this position
        post = self.get_signpost_at(screen_coords, scroll)
        if post:
            post.open = True
            post.text_panel = TextPanel(post.text,
                                        self.fg_color,
                                        self.bg_color,
                                        self.font)

    def display_open_signs(self, surface, scroll):
        for p in [p for p in self.all_posts if p.open]:
            top_left = grid_to_screen(p.grid_positions[0], scroll)
            text_position = (top_left[X],
                             top_left[Y] - p.text_panel.get_height())
            surface.blit(p.text_panel.rendered(), text_position)


def grid_to_screen(grid_coords, scroll):
    # converts grid coords to pixel coords,
    # taking scroll into account
    x = (grid_coords[X] * BLOCK_SIZE - scroll[X]) * SCALING_FACTOR
    y = (grid_coords[Y] * BLOCK_SIZE - scroll[Y]) * SCALING_FACTOR
    return (x,y)

def screen_to_grid(screen_coords, scroll):
    scaled_mouse_pos = (screen_coords[X] // SCALING_FACTOR,
                        screen_coords[Y] // SCALING_FACTOR)
    return ((scaled_mouse_pos[X] + scroll[X]) // BLOCK_SIZE,
            (scaled_mouse_pos[Y] + scroll[Y]) // BLOCK_SIZE)