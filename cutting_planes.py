from parapy.core import *
from parapy.geom import *
import numpy as np


class CuttingPlanes(GeomBase):
    direction = Input('chordwise')  # or 'chordwise'
    starting_point = Input(Point(2, 0, 0))
    chord_length = Input(1)
    chord_percentage = Input(0.25)

    @Input
    def base_plane_rotate(self):
        angle = 0
        if self.direction == 'spanwise':
            angle = 90 * np.pi / 180
        elif self.direction == 'chordwise':
            angle = 0
        return angle

    @Part
    def base_plane(self):
        return RectangularSurface(width=100,
                                  length=100,
                                  position=rotate(rotate90(self.position, 'x'), 'y', self.base_plane_rotate),
                                  hidden=True)

    @Part
    def to_starting_point(self):
        return TranslatedSurface(surface_in=self.base_plane,
                                 displacement=self.starting_point.vector,
                                 hidden=True)

    @Part
    def plane_final_pos(self):
        return TranslatedSurface(surface_in=self.to_starting_point,
                                 displacement=Vector(self.chord_length * self.chord_percentage, 0, 0),
                                 hidden=False)


if __name__ == '__main__':
    from parapy.gui import display

    display(CuttingPlanes())
