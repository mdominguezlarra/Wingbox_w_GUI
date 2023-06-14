from parapy.core import *
from parapy.geom import *
from rib import Rib
from sparsystem import SparSystem


class WingBox(GeomBase):

    # Geometry
    wing = Input()

    # Ribs
    rib_pitch = Input(0.2)
    rib_thickness = Input(1)
    rib_index = Input(0)

    # Spars
    front_spar_loc = Input([0.25, 0.25, 0.25, 0.25, 0.25, 0.25])
    rear_spar_loc = Input([0.75, 0.75, 0.75, 0.75, 0.75, 0.75])

    @Attribute
    def rib_distribution(self):
        if self.rib_index == 0:
            n_r = int(self.wing.spans[-1]//self.rib_pitch)
            r_span = []
            for i in range(n_r):
                r_span.append(i*self.rib_pitch)
            n_r = n_r + 1
            r_span.append(self.wing.spans[-1])

        else:
            print('Place other distribution indices')
            n_r = 0
            r_span = 0

        return n_r, r_span

    @Part
    def ribs(self):
        return Rib(quantify=self.rib_distribution[0],
                   rib_span=self.rib_distribution[1][child.index],
                   rib_thickness=self.rib_thickness,
                   skin_shell=self.wing.right_wing,
                   root_chord=self.wing.root_chord)

    @Part
    def spars(self):
        return SparSystem(front_spar_loc=self.front_spar_loc,
                          rear_spar_loc=self.rear_spar_loc,
                          wing=self.wing)

    @Part
    def skin(self):
        return SewnShell(self.wing.right_wing,
                         mesh_deflection=1e-4,
                         transparency=0.7)


if __name__ == '__main__':
    from parapy.gui import display
    display(WingBox())
