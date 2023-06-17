from parapy.core import *
from parapy.geom import *


class Spar(GeomBase):
    curves = Input([LineSegment(start=[0.25, 0, -0.1], end=[0.25, 0, 0.1]),
                    LineSegment(start=[0.25, 1, -0.1], end=[0.25, 1, 0.1])])

    @Part
    def Spar(self):
        return FilledSurface(curves=self.curves,
                             mesh_deflection=1e-4)


if __name__ == '__main__':
    from parapy.gui import display
    display(Spar())
