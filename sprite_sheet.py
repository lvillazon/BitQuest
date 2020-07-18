import pygame

class SpriteSheet(object):
    """
    converts a sprite sheet into individual sprites
    taken from http://www.pygame.org/wiki/Spritesheet?parent=CookBook
    """

    def __init__(self, filename, scale=1):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error:
            print("Failed to load spritesheet", filename)
            raise SystemExit
        self.scale = scale  # scaling multiplier for the sprites

    def image_at(self, rectangle, colorkey=None):
        """ grab a specific rectangle from the sheet into an image """
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        final_size = (rect.width * self.scale, rect.height * self.scale)
        return pygame.transform.scale(image, final_size)

    def images_at(self, rects, colorkey=None):
        """ grab multiple images and return as a list """
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(self, rect, image_count, colorkey=None):
        """ grab multiple images from an image strip and return as a list """
        image_rects = [(rect[0] + rect[2] * x, rect[1], rect[2], rect[3])
                       for x in range(image_count)]
        return self.images_at(image_rects, colorkey)

    def load_block_of_8(self, x, y, colorkey=None):
        """
        loads 8 frames, assuming the precise layout
        used by the infinite runner art pack
        the sprites are 32 x 32 but with a 4 pixel gap between them
        """
        return [self.image_at((x, y + 32, 32, 32), colorkey),
                self.image_at((x + 36, y + 32, 32, 32), colorkey),
                self.image_at((x + 72, y + 32, 32, 32), colorkey),
                self.image_at((x, y + 68, 32, 32), colorkey),
                self.image_at((x + 36, y + 68, 32, 32), colorkey),
                self.image_at((x + 72, y + 68, 32, 32), colorkey),
                self.image_at((x, y + 104, 32, 32), colorkey),
                self.image_at((x + 36, y + 104, 32, 32), colorkey),
                ]
