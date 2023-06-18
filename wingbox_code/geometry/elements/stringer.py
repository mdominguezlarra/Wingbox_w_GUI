from parapy.core import *
from parapy.geom import *


def stringer_finder(edges, up=True):

    edge_start = []
    idx = []

    for i in edges:
        if i.start.y > i.end.y:
            edge_start.append(i.end)
        else:
            edge_start.append(i.start)

    y_sorted = sorted(edge_start, key=lambda ypos: ypos.y)

    for i in range(int(len(edge_start)/2)):
        z_sorted = sorted(y_sorted[2*i:2*i+2], key=lambda zpos: zpos.z)
        if up:
            idx.append(edge_start.index(z_sorted[1]))
        else:
            idx.append(edge_start.index(z_sorted[0]))

    stringer = [edges[i] for i in idx]

    return stringer


class Stringer(GeomBase):

    start = Input()
    end = Input()
    wing = Input()
    up = Input()

    @Part
    def stringer_lines(self):
        return LineSegment(start=self.start,
                           end=self.end,
                           hidden=True)

    @Part
    def stringer_plane(self):
        return RuledSurface(curve1=TranslatedCurve(curve_in=self.stringer_lines,
                                                   displacement=Vector(0, 0, 25)),
                            curve2=TranslatedCurve(curve_in=self.stringer_lines,
                                                   displacement=Vector(0, 0, -25)),
                            hidden=True)

    @Part
    def stringer_intersect(self):
        return IntersectedShapes(shape_in=self.wing.right_wing,
                                 tool=self.stringer_plane,
                                 hidden=True)

    @Part
    def stringers(self):
        return Wire(curves_in=stringer_finder(self.stringer_intersect.edges, self.up))
