import world

''' encapsulates the accessible attributes of the game world'''

class Bit:
    '''attributes of the dog character'''
    def __init__(self):
        self._x = 0

    x = property(get_x, set_x, del_x)

    def get_x(self):
        return world.dog.location['x']

    def set_x(self, new_x):
        world.dog.location['x'] = new_x

    def del_x(self):
        pass
