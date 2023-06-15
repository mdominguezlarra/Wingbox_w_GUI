from parapy.core import *
from parapy.geom import *
import numpy as np


class CuttingPlanes(GeomBase):
    direction = Input('chordwise')  # or 'spanwise'
    starting_point = Input(Point(2, 0, 0))
    starting_chord_length = Input(1)  # Only used if plane is spanwise or if it follows TE.

    chord_percentage = Input(0.25)  # Only used if plane is spanwise or if it follows TE.

    ending_point = Input(Point(3, 0, 0))  # Only used if plane follows TE.
    ending_chord_length = Input(1)

    rot_direction = Input(Vector(0, 0, 1))  # Only used if plane follows TE.

    @Input
    def base_plane_rotate(self):
        angle = 0
        if self.direction == 'spanwise':
            angle = 90 * np.pi / 180
        elif self.direction == 'chordwise':
            angle = 0
        return angle

    # This input is only used if the user wants to rotate the plane to follow the trailing edge.
    @Input
    def spanwise_rot(self):

        x0 = self.starting_point[0]
        y0 = self.starting_point[1]
        x1 = self.ending_point[0]
        y1 = self.ending_point[1]

        x0 += self.starting_chord_length * self.chord_percentage
        x1 += self.ending_chord_length * self.chord_percentage

        x_line = x1 - x0
        y_line = y1 - y0
        rot_angle = np.arctan(x_line/y_line)
        rot_point = Point(x0, y0, 0)
        rot_len = np.hypot(x_line, y_line)

        return rot_angle, rot_point, rot_len

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
                                 displacement=Vector(self.starting_chord_length * self.chord_percentage, 0, 0),
                                 hidden=True)

    @Part
    def plane_final_rot(self):
        return RotatedSurface(angle=-self.spanwise_rot[0],
                              rotation_point=self.spanwise_rot[1],
                              surface_in=self.plane_final_pos,
                              vector=self.rot_direction,
                              hidden=True)

    @Part
    def plane_final_scale(self):
        return ScaledSurface(factor=self.spanwise_rot[2]/100,
                             reference_point=self.spanwise_rot[1],
                             surface_in=self.plane_final_rot)

    @Part
    def plane_final_transl(self):
        return TranslatedSurface(surface_in=self.plane_final_scale,
                                 displacement=Vector(self.spanwise_rot[2]/2 * np.sin(self.spanwise_rot[0]),
                                                     self.spanwise_rot[2]/2 * np.cos(self.spanwise_rot[0]),
                                                     0))

if __name__ == '__main__':
    from parapy.gui import display
    display(CuttingPlanes(direction='spanwise'))
