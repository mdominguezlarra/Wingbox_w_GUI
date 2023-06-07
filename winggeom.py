from parapy.core import *
from parapy.geom import *
from wingsec import WingSec
import numpy as np


class WingGeom(GeomBase):

    # All of the following inputs should be read from a file
    # For 1st section
    root_chord = Input(5)

    # For the rest (I have a doubt, how will we solve if the number of inputs is not coherent??)
    spans = Input([0, 8, 13, 16])           # m. wrt the root position
    tapers = Input([1, 0.6, 0.35, 0.2])     # -. wrt the root chord. Extra element for root chord
    sweeps = Input([30, 40, 50])            # deg. wrt the horizontal
    dihedrals = Input([3, 3, 3])            # deg. wrt the horizontal
    twist = Input([2, 0, -1, -3])           # def. wrt the horizontal (this includes the initial INCIDENCE!!)


    @Part
    def wiresec(self):
        return WingSec(quantify=len(self.spans)-1,        # this is how the quantity is determined
                       span=self.spans[child.index+1]-self.spans[child.index],
                       root_chord=self.root_chord*self.tapers[child.index],
                       taper=self.tapers[child.index+1]/self.tapers[child.index],
                       map_down=['sweeps->sweep', 'dihedrals->dihedral'],
                       incidence=self.twist[child.index],
                       twist=self.twist[child.index+1],
                       position=self.position if child.index == 0 else
                       child.previous.nextorigin())


if __name__ == '__main__':
    from parapy.gui import display
    display(WingGeom())
