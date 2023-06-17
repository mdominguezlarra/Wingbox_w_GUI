from parapy.core import *
from parapy.geom import *
import numpy as np
from .geometry_tools.cutter import Cutter


class SparSystem(GeomBase):

    front_spar_loc = Input([0.25, 0.25, 0.25, 0.25])
    rear_spar_loc = Input([0.75, 0.75, 0.75, 0.75])
    wing = Input()

    # Retrieving spar stations locations.
    @Attribute
    def spar_stations(self):

        frac_span = np.array(self.wing.spans) / self.wing.spans[-1]
        air_sec = self.wing.airfoil_sections
        air_sec = air_sec[1:-1]

        #Inputs
        front_loc_copy = self.front_spar_loc
        rear_loc_copy = self.rear_spar_loc

        front_loc = [i for i in front_loc_copy]
        rear_loc = [i for i in rear_loc_copy]

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

            front_loop[pos] = front_loop[pos - 1] + (i - order_sp[pos - 1]) \
                              * (front_loop[pos + 1] - front_loop[pos - 1]) / (order_sp[pos + 1] - order_sp[pos - 1])
            rear_loop[pos] = rear_loop[pos - 1] + (i - order_sp[pos - 1]) \
                             * (rear_loop[pos + 1] - rear_loop[pos - 1]) / (order_sp[pos + 1] - order_sp[pos - 1])

            front_loc[-1] = front_loop[pos]
            rear_loc[-1] = rear_loop[pos]

        return front_loop, rear_loop

    @Part
    def spars(self):
        return Cutter(quantify=len(self.spar_stations),
                      cut_loc=self.spar_stations[child.index],
                      wing=self.wing,
                      hidden=False)





if __name__ == '__main__':
    from parapy.gui import display

    display(SparSystem())
