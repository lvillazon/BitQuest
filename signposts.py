import pygame

from constants import *
from text_panel import InfoPanel


class Signposts:
    """ the info signs used to give instructions on each level
    Each one has text that will display in a pop-up window,
    when the signpost is clicked """

    class _Post:
        def __init__(self, grid_positions, title, body):
            self.grid_positions = grid_positions
            self.info_position = None  # only valid when the sign is open
            self.title = title
            self.body = body  # a list of strings
#            self.text = title + '\n' + body
            self.open = False  # true when the text pop-up is displayed
            self.text_panel = None

    def __init__(self, font):
        self.font = font
        self.fg_color = LIGHT_GREY  # TODO get colours from current text preferences used in the editor
        self.bg_color = SKY_BLUE
        self.all_posts = []
        # TODO if we need extra performance, replace the all_post list
        #  with a dictionary that uses post grid coords as the key

    def add_signpost(self, pos, title, body):
        # add all the grid squares occupied by the signpost
        # based on the top-left grid square pos
        grid_positions = [pos,
                          (pos[X]+1, pos[Y]),
                          (pos[X], pos[Y]+1),
                          (pos[X]+1, pos[Y]+1)]
        self.all_posts.append(self._Post(grid_positions, title, body))

    def get_signpost_at(self, screen_coords, scroll):
        # returns the signpost under the mouse cursor, if any
        # for "closed" signposts, the collision rectangle is the blocks of the signpost itself
        # for "open" signposts (ie, those displaying their info panel),
        # the collision rectangle is just the close button on the info panel
        # if neither matches, return None
        grid_pos = screen_to_grid(screen_coords, scroll)
        for p in self.all_posts:
            if p.open:
                button_rect = p.text_panel.get_close_button_rect()
                collision_rect = pygame.Rect((p.info_position[X] + button_rect[X],
                                             p.info_position[Y] + button_rect[Y]),
                                            button_rect.size)
                if collision_rect.collidepoint(screen_coords):
                    return p
            else:
                if grid_pos in p.grid_positions:
                    return p
        return None

    def check_signpost_at(self, screen_coords, scroll):
        # toggles the info panel if there is a signpost at this position
        post = self.get_signpost_at(screen_coords, scroll)
        if post:
            if post.open:
                # close the info panel
                post.open = False
                post.text_panel = None
            else:
                # open the info panel
                post.open = True
                post.text_panel = InfoPanel(post.title,
                                            post.body,
                                            self.fg_color,
                                            self.bg_color,
                                            self.font)

    def update_open_signs(self, surface, scroll, offset):
        # render any open info panels
        # and update their on-screen coords
        for p in [p for p in self.all_posts if p.open]:
            top_left = grid_to_screen(p.grid_positions[0], scroll, offset)
            p.info_position = (top_left[X],
                               top_left[Y] - p.text_panel.get_rendered_text_height())
            surface.blit(p.text_panel.rendered(), p.info_position)

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