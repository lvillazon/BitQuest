import pygame

class MouseHandler(object):

    def __init__(self):
        pass


#                                 mouse_pos = (pygame.mouse.get_pos()[X]
#                                              / SCALING_FACTOR
#                                              + self.scroll[X],
#                                              pygame.mouse.get_pos()[Y]
#                                              / SCALING_FACTOR
#                                              + self.scroll[Y]
#                                              )
#                                        )
#                                 if event.button == 1:  # left click
#                                     if shift:
#                                         self.blocks.select_block(mouse_pos,
#                                                                  'add')
#                                     else:
#                                         # just select a single block
#                                         self.blocks.select_block(mouse_pos,
#                                                                  'set')
#                                 elif event.button == 3:  # right click
#                                     self.blocks.select_block(mouse_pos, 'pick')
#                                 # 2: middle button
#                                 # 4: scroll up
#                                 # 5: scroll down
