from parapy.core import *
from parapy.geom import *
from rib import Rib


class WingBox(GeomBase):

    # Geometry
    wing = Input(in_tree=True)

    # Ribs
    rib_pitch = Input(0.2)
    rib_thickness = Input(1)
    rib_index = Input(0)

    @Attribute
    def rib_distribution(self):
        if self.rib_index == 0:
            n_r = int(self.wing.spans[-1]//self.rib_pitch)
            r_span = []
            for i in range(n_r):
                r_span.append(i*self.rib_pitch)

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
