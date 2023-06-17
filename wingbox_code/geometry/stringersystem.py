from parapy.core import *
from parapy.geom import *
import numpy as np
from .geometry_tools.cutter import Cutter


def division_lst(nested_arr):

    div_lst = []

    for airfoil in range(np.size(nested_arr, 0)):
        div_lst_pos = []
        for position in range(np.size(nested_arr, 1)):
            n = nested_arr[airfoil, position]
            div = np.zeros(n)
            for i in range(len(div)):
                div[i] = 1/(n+1)*(i+1)

            div_lst_pos.append(list(div))
        div_lst.append(div_lst_pos)

    return div_lst


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


class StringerSystem(GeomBase):

    ribs = Input()
    spars = Input()
    wing = Input()
    stringer_idx = Input()

    @Attribute
    def wire_stringer(self):

        curves = []
        for i in range(len(self.split_foils)):
            airfoil = [self.split_foils[i].curves_in[1], self.split_foils[i].curves_in[3]]
            curves.append(airfoil)

        return curves

    @Attribute
    def stringer_hooks(self):

        hooks_up = []
        hooks_down = []
        curves = self.wire_stringer
        div_lst = division_lst(np.array(self.stringer_idx))

        for i in range(len(self.split_foils)-1):
            c1up = SplitCurve(curve_in=curves[i][0],
                              tool=[x*(curves[i][0].u2-curves[i][0].u1) + curves[i][0].u1 for x in div_lst[i][0]])
            c1do = SplitCurve(curve_in=curves[i][1],
                              tool=[x*(curves[i][1].u2-curves[i][1].u1) + curves[i][1].u1 for x in div_lst[i][1]])
            c2up = SplitCurve(curve_in=curves[i+1][0],
                              tool=[x*(curves[i+1][0].u2-curves[i+1][0].u1) + curves[i+1][0].u1 for x in div_lst[i][0]])
            c2do = SplitCurve(curve_in=curves[i+1][1],
                              tool=[x*(curves[i+1][1].u2-curves[i+1][1].u1) + curves[i+1][1].u1 for x in div_lst[i][1]])

            for j in range(len(div_lst[i][0])):
                stringer = [c1up.curves_in[j].end, c2up.curves_in[j].end]
                hooks_up.append(stringer)

            for j in range(len(div_lst[i][1])):
                stringer = [c1do.curves_in[j].end, c2do.curves_in[j].end]
                hooks_down.append(stringer)

        return hooks_up, hooks_down

    @Part
    def airfoil_cut_front(self):
        return Cutter(cut_loc=self.spars.spar_stations[0],
                      wing=self.wing,
                      extend=True)

    @Part
    def airfoil_cut_rear(self):
        return Cutter(cut_loc=self.spars.spar_stations[1],
                      wing=self.wing,
                      extend=True)

    @Part
    def intersect_front(self):
        return IntersectedShapes(quantify=len(self.ribs.essential_ribs),
                                 shape_in=self.ribs.essential_ribs[child.index],
                                 tool=self.airfoil_cut_front.total_cutter,
                                 hidden=True)

    @Part
    def intersect_rear(self):
        return IntersectedShapes(quantify=len(self.ribs.essential_ribs),
                                 shape_in=self.ribs.essential_ribs[child.index],
                                 tool=self.airfoil_cut_rear.total_cutter,
                                 hidden=True)

    @Part
    def split_foils(self):
        return SplitCurve(quantify=len(self.ribs.essential_ribs),
                          curve_in=self.ribs.rib_sections[child.index],
                          tool=[self.intersect_front[child.index].edges[0].start,
                                self.intersect_rear[child.index].edges[0].start,
                                self.intersect_rear[child.index].edges[0].end,
                                self.intersect_front[child.index].edges[0].end],
                          hidden=True)

    @Part
    def stringer_lines_up(self):
        return LineSegment(quantify=len(self.stringer_hooks[0]),
                           start=self.stringer_hooks[0][child.index][0],
                           end=self.stringer_hooks[0][child.index][1],
                           hidden=True)

    @Part
    def stringer_lines_down(self):
        return LineSegment(quantify=len(self.stringer_hooks[1]),
                           start=self.stringer_hooks[1][child.index][0],
                           end=self.stringer_hooks[1][child.index][1],
                           hidden=True)

    @Part
    def stringer_plane_up(self):
        return RuledSurface(quantify=len(self.stringer_lines_up),
                            curve1=TranslatedCurve(curve_in=self.stringer_lines_up[child.index],
                                                   displacement=Vector(0, 0, 25)),
                            curve2=TranslatedCurve(curve_in=self.stringer_lines_up[child.index],
                                                   displacement=Vector(0, 0, -25)),
                            hidden=True)

    @Part
    def stringer_intersect_up(self):
        return IntersectedShapes(quantify=len(self.stringer_plane_up),
                                 shape_in=self.wing.right_wing,
                                 tool=self.stringer_plane_up[child.index],
                                 hidden=True)

    @Part
    def stringers_up(self):
        return Wire(quantify=len(self.stringer_intersect_up),
                    curves_in=stringer_finder(self.stringer_intersect_up[child.index].edges, True))

    @Part
    def stringer_plane_down(self):
        return RuledSurface(quantify=len(self.stringer_lines_down),
                            curve1=TranslatedCurve(curve_in=self.stringer_lines_down[child.index],
                                                   displacement=Vector(0, 0, 25)),
                            curve2=TranslatedCurve(curve_in=self.stringer_lines_down[child.index],
                                                   displacement=Vector(0, 0, -25)),
                            hidden=True)

    @Part
    def stringer_intersect_down(self):
        return IntersectedShapes(quantify=len(self.stringer_plane_down),
                                 shape_in=self.wing.right_wing,
                                 tool=self.stringer_plane_down[child.index],
                                 hidden=True)

    @Part
    def stringers_down(self):
        return Wire(quantify=len(self.stringer_intersect_down),
                    curves_in=stringer_finder(self.stringer_intersect_down[child.index].edges, False))

