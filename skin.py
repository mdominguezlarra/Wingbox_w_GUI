from parapy.core import *
from parapy.geom import *
from winggeom import WingGeom


class Skin(GeomBase):
    wing = Input(WingGeom())

    @Part
    def skin(self):
        return LoftedShell(quantify=len(self.wing.profile_order[0]) - 1,
                           profiles=self.wing.profile_order[0][child.index:child.index + 2],
                           mesh_deflection=1e-4,
                           hidden=False)


if __name__ == '__main__':
    from parapy.gui import display
    display(Skin())
