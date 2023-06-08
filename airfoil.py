from parapy.core import *
from parapy.geom import *
import numpy as np


class Airfoil(GeomBase, Base):

    # The KBEutils could be used for an alternative way to produce airfoils

    airfoil_curve = Input()   # The airfoils must be checked
    airfoil_start = Input(Point(1, 5, 0.5))
    airfoil_direction = Input(Vector(0.95, 0, -0.3))
    airfoil_chord = Input(2)

    @Attribute
    def airfoil_angle(self):
        angle = -np.arctan2(self.airfoil_direction.z, self.airfoil_direction.x)
        return angle

    @Part
    def transformed_foil(self):
        return TranslatedCurve(curve_in=self.airfoil_curve,
                               displacement=self.airfoil_start - Point(0, 0, 0),
                               hidden=True)

    @Part
    def rotated_foil(self):
        return RotatedCurve(curve_in=self.transformed_foil,
                            rotation_point=self.airfoil_start,
                            vector=Vector(0, 1, 0),
                            angle=self.airfoil_angle,
                            hidden=True)

    @Part
    def scaled_foil(self):
        return ScaledCurve(curve_in=self.rotated_foil,
                           reference_point=self.airfoil_start,
                           factor=self.airfoil_chord,
                           mesh_deflection=1e-4)


if __name__ == '__main__':
    from parapy.gui import display
    display(Airfoil())
