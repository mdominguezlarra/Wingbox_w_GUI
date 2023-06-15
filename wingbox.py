from parapy.core import *
from parapy.geom import *
from ribssystem import RibsSystem
from sparsystem import SparSystem
from skinsystem import SkinSystem
from stringersystem import StringerSystem
from winggeom import WingGeom


class WingBox(GeomBase):

    # Geometry
    wing = Input()

    # Ribs
    rib_idx = Input([7, 5, 3])

    # Spars
    front_spar_loc = Input([0.25, 0.25, 0.25, 0.25])  # Must be between 0 and the foremost rear_spar_loc
    rear_spar_loc = Input([0.75, 0.75, 0.75, 0.75])  # Must be between the rearmost front_spar_loc and 1

    # Trailing edge gaps
    TE_ribs_gap = Input(0.8)  # Must be after the rearmost rear_spar_loc but less than 1
    TE_skin_gap = Input(0.85)  # Must be after the rearmost rear_spar_loc but less than 1

    # Stringers
    stringer_idx= Input([[7, 5],
                        [5, 3],
                        [3, 2]])

    @Part
    def skin(self):
        return SkinSystem(TE_gap=self.TE_skin_gap,
                          ribs=self.ribs,
                          wing=self.wing)

    @Part
    def spars(self):
        return SparSystem(front_spar_loc=self.front_spar_loc,
                          rear_spar_loc=self.rear_spar_loc,
                          wing=self.wing)

    @Part
    def ribs(self):
        return RibsSystem(rib_idx=self.rib_idx,
                          TE_gap=self.TE_ribs_gap,
                          wing=self.wing)

    @Part
    def stringers(self):
        return StringerSystem(pass_down=['spars', 'ribs', 'stringer_idx'])


if __name__ == '__main__':
    from parapy.gui import display

    display(WingBox())
