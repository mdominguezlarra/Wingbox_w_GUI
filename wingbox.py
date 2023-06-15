from parapy.core import *
from parapy.geom import *
from ribssystem import RibsSystem
from sparsystem import SparSystem
import numpy as np
from skinsystem import SkinSystem
from winggeom import WingGeom


class WingBox(GeomBase):

    # Geometry
    wing = Input(WingGeom())

    # Ribs
    rib_pitch = Input(0.2)
    rib_thickness = Input(1)
    rib_index = Input(0)

    # Spars
    front_spar_loc = Input([0.25, 0.25, 0.25, 0.25])  # Must be between 0 and the foremost rear_spar_loc
    rear_spar_loc = Input([0.75, 0.75, 0.75, 0.75])  # Must be between the rearmost front_spar_loc and 1

    # Trailing edge gaps
    TE_ribs_gap = Input(0.8)  # Must be after the rearmost rear_spar_loc but less than 1
    TE_skin_gap = Input(0.85)  # Must be after the rearmost rear_spar_loc but less than 1

    @Attribute
    def spar_stations(self):

        frac_span = np.array(self.wing.spans) / self.wing.spans[-1]
        air_sec = self.wing.airfoil_sections
        air_sec = air_sec[1:-1]

        front_loc = self.front_spar_loc
        rear_loc = self.rear_spar_loc
        front_loop = []
        rear_loop = []

        for i in air_sec:
            frac_span = np.append(frac_span, i)
            order_sp = np.sort(frac_span)
            order = np.argsort(frac_span)
            pos = np.where(order_sp == i)[0][0]
            front_loc.append(0)
            rear_loc.append(0)
            front_loop = list([front_loc[k] for k in order])
            rear_loop = list([rear_loc[k] for k in order])
            front_loop[pos] = front_loop[pos - 1] + (i-order_sp[pos-1]) \
                              * (front_loop[pos+1] - front_loop[pos-1])/(order_sp[pos+1] - order_sp[pos-1])
            rear_loop[pos] = rear_loop[pos - 1] + (i-order_sp[pos-1]) \
                             * (rear_loop[pos+1] - rear_loop[pos-1])/(order_sp[pos+1] - order_sp[pos-1])
            front_loc[-1] = front_loop[pos]
            rear_loc[-1] = rear_loop[pos]

        return front_loop, rear_loop

    @Part
    def skin(self):
        return SkinSystem(TE_gap=self.TE_skin_gap)

    @Part
    def spars(self):
        return SparSystem(front_spar_loc=self.spar_stations[0],
                          rear_spar_loc=self.spar_stations[1])

    @Part
    def ribs(self):
        return RibsSystem(rib_pitch=self.rib_pitch,
                          rib_thickness=self.rib_thickness,
                          rib_index=self.rib_index,
                          TE_gap=self.TE_ribs_gap)


if __name__ == '__main__':
    from parapy.gui import display

    display(WingBox())
