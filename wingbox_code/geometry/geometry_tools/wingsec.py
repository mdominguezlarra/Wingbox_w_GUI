from parapy.core import *
from parapy.geom import *
from parapy.core.validate import *
import numpy as np


class WingSec(GeomBase):

    span = Input(20, validator=Positive(incl_zero=True))         # m
    root_chord = Input(5)    # m
    taper = Input(0.3)       # -
    sweep = Input(30)        # deg
    dihedral = Input(5)      # deg
    incidence = Input(0)     # deg
    twist = Input(-2)        # deg (include type of distribution?, measured at c/4, with respect to the horizontal)

    @Attribute
    def get_pts(self):
        """ This function gets the points and lines that define the section planform """
        pt1 = Vector(0.25*self.root_chord*(1-np.cos(np.deg2rad(self.incidence))),
                     0,
                     0.25*self.root_chord*np.sin(np.deg2rad(self.incidence)))
        pt2 = Vector(self.span*np.tan(np.deg2rad(self.sweep))
                     + 0.25*self.root_chord*self.taper*(1-np.cos(np.deg2rad(self.twist))),
                     self.span,
                     self.span*np.tan(np.deg2rad(self.dihedral))
                     + 0.25*self.root_chord*self.taper*np.sin(np.deg2rad(self.twist)))
        pt3 = Vector(self.span*np.tan(np.deg2rad(self.sweep))
                     + self.root_chord*self.taper
                     - 0.75*self.root_chord*self.taper*(1-np.cos(np.deg2rad(self.twist))),
                     self.span,
                     self.span*np.tan(np.deg2rad(self.dihedral))
                     - 0.75*self.root_chord*self.taper*np.sin(np.deg2rad(self.twist)))
        pt4 = Vector(self.root_chord
                     - 0.75*self.root_chord*(1-np.cos(np.deg2rad(self.incidence))),
                     0,
                     - 0.75*self.root_chord*np.sin(np.deg2rad(self.incidence)))

        pts = [self.position + pt1,
               self.position + pt2,
               self.position + pt3,
               self.position + pt4]

        lns = [LineSegment(pts[0], pts[1]),
               LineSegment(pts[1], pts[2]),
               LineSegment(pts[2], pts[3]),
               LineSegment(pts[3], pts[0])]

        return pts, lns

    @Attribute
    def nextorigin(self):
        newor = Vector(self.span*np.tan(np.deg2rad(self.sweep)),
                       self.span,
                       self.span*np.tan(np.deg2rad(self.dihedral)))
        return self.position + newor

    # @Part # DO NOT DELETE UNTIL SUBMISSION
    # def sec_chords_in(self):
    #     return LineSegment(self.get_pts[0][0], self.get_pts[0][3])

    @Part
    def sec_chords_out(self):
        return LineSegment(start=self.get_pts[0][1],
                           end=self.get_pts[0][2],
                           line_thickness=2)

    @Part
    def sec_plane(self):
        return FilledSurface(self.get_pts[1])


if __name__ == '__main__':
    from parapy.gui import display
    display(WingSec())
