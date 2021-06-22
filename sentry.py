from characters import Robot
from constants import ROBOT_SPRITE_FILE


class Sentry(Robot):
    # robot sentries used to present more complex puzzles
    def __init__(self,
                 world,
                 name = "sentry",
                 sprite_file = ROBOT_SPRITE_FILE,
                 size = (16, 20)):
        super().__init__(self, world, name, sprite_file, size)

    def set_puzzle(self, instructions, ):
        pass
