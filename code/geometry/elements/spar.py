from parapy.core import *
from parapy.geom import *


class Spar(GeomBase):
    curves = Input()

    @Part
    def Spar(self):
        return FilledSurface(curves=self.curves,
                             mesh_deflection=1e-4)
