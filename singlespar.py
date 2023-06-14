from parapy.core import *
from parapy.geom import *

class SingleSpar(GeomBase):
    curves = Input([LineSegment(start=[0.25, 0, -0.1], end=[0.25, 0, 0.1]),
                    LineSegment(start=[0.25, 1, -0.1], end=[0.25, 1, 0.1])])

    @Part
    def SingleSpar(self):
        return FilledSurface(curves=self.curves)


if __name__ == '__main__':
    from parapy.gui import display
    display(SingleSpar())
