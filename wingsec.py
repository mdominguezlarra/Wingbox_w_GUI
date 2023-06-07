from parapy.core import *
from parapy.geom import *
import numpy as np


class WingSec(GeomBase):

    span = Input(20)         # m
    root_chord = Input(5)    # m
    taper = Input(0.3)       # -
    sweep = Input(30)        # deg
    dihedral = Input(5)      # deg
    incidence = Input(0)     # deg
    twist = Input(-2)        # deg (include type of distribution?, measured at c/4, with respect to incidence)
    position = Input(Point(5,0,0))

    @Attribute
    def get_pts(self):
        """ This function gets the points that define the section planform """
        pt1 = Vector(0,
                     0,
                     0.25*np.sin(np.deg2rad(self.incidence))*self.root_chord)
        pt2 = Vector(self.span*np.tan(np.deg2rad(self.sweep)),
                     self.span,
                     self.span*np.tan(np.deg2rad(self.dihedral))
                     + 0.25*np.sin(np.deg2rad(self.twist))*self.root_chord*self.taper)
        pt3 = Vector(self.span*np.tan(np.deg2rad(self.sweep))
                     + self.root_chord*self.taper,
                     self.span,
                     self.span*np.tan(np.deg2rad(self.dihedral))
                     - 0.75*np.sin(np.deg2rad(self.twist)*self.root_chord*self.taper))
        pt4 = Vector(self.root_chord,
                     0,
                     - 0.75*np.sin(np.deg2rad(self.incidence))*self.root_chord)

        pts = [self.position + pt1,
               self.position + pt2,
               self.position + pt3,
               self.position + pt4]

        return pts

    @Attribute
    def nextorigin(self):
        newor = Vector(self.span*np.tan(np.deg2rad(self.sweep)),
                       self.span,
                       self.span*np.tan(np.deg2rad(self.dihedral)))
        return self.position + newor
    @Part
    def sec_skeleton(self):
        return Polygon(points=self.get_pts)


if __name__ == '__main__':
    from parapy.gui import display
    display(WingSec())



