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

        front_loop = front_loc
        rear_loop = rear_loc

        for i in air_sec:
            if i not in frac_span:
                frac_span = np.append(frac_span, i)
                span_order = np.sort(frac_span)
                order = np.argsort(frac_span)
                pos = np.where(span_order == i)[0][0]

                front_loc.append(0)
                rear_loc.append(0)

                front_loop = list([front_loc[k] for k in order])
                rear_loop = list([rear_loc[k] for k in order])

                # distances
                dt = span_order[pos+1] - span_order[pos-1]
                d1 = i - span_order[pos-1]
                d2 = span_order[pos+1] - i

                front_loop[pos] = 1/dt * ((dt - d1) * front_loop[pos - 1] + (dt - d2) * front_loop[pos + 1])
                rear_loop[pos] = 1/dt * ((dt - d1) * rear_loop[pos - 1] + (dt - d2) * rear_loop[pos + 1])

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
