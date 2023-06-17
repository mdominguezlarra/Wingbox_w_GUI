from parapy.core import *
from parapy.geom import *
from .cutting_planes import CuttingPlanes
from wingbox_code.geometry.elements.spar import Spar


class Cutter(GeomBase):

    cut_loc = Input()
    wing = Input()
    extend = Input(False)
    hidden = Input(True)

    @Attribute
    def cut_loc_ext(self):

        cut_loc_ext = []
        for i in range(len(self.wing.profile_order[0])):
            cut_loc_ext.append(self.cut_loc)

        return cut_loc_ext

    # Retrieving wing information.
    @Attribute
    def wingInfo(self):

        # Retrieving needed attributes.
        unscaled_airfoils = self.wing.profile_order[2]

        starting_points = []
        chords = []
        for airfoil in unscaled_airfoils:
            starting_points.append(airfoil.airfoil_start)
            chords.append(airfoil.airfoil_chord)

        return starting_points, chords

    # Defining airfoils as surfaces to cut.
    @Part
    def airfoil_planes(self):
        return CuttingPlanes(quantify=len(self.cutter_planes),
                             direction='chordwise',
                             starting_point=self.wingInfo[0][child.index],
                             hidden=True)

    @Part
    def airfoil_wires(self):
        return IntersectedShapes(quantify=len(self.airfoil_planes),
                                 shape_in=self.airfoil_planes[child.index].plane_final_pos,
                                 tool=self.wing.right_wing,
                                 hidden=True)

    @Part
    def airfoils_as_shapes(self):
        return TrimmedSurface(quantify=len(self.airfoil_wires),
                              built_from=self.airfoil_planes[child.index].plane_final_pos,
                              island=self.airfoil_wires[child.index].edges[0],
                              hidden=True)

    @Part
    def cutter_planes(self):
        return CuttingPlanes(quantify=len(self.wingInfo[0]),
                             direction='spanwise',
                             starting_point=self.wingInfo[0][child.index],
                             starting_chord_length=self.wingInfo[1][child.index],
                             chord_percentage=(self.cut_loc[child.index] if isinstance(self.cut_loc, list)
                                               else self.cut_loc_ext[child.index]),
                             hidden=True)

    # Intersections and web definitions.
    @Attribute
    def cutter_intersecs(self):
        intersections = []
        for i in range(len(self.cutter_planes)):
            edg = IntersectedShapes(shape_in=self.cutter_planes[i].plane_final_pos,
                                    tool=self.airfoils_as_shapes[i],
                                    hidden=True)
            intersections.append(edg.edges)

        return intersections

    @Part
    def cutter_intersec_curves(self):
        return ComposedCurve(quantify=len(self.cutter_intersecs),
                             built_from=self.cutter_intersecs[child.index],
                             hidden=True)

    @Part
    def cutter_web(self):
        return Spar(quantify=len(self.cutter_intersecs) - 1,
                    curves=[self.cutter_intersec_curves[child.index],
                            self.cutter_intersec_curves[child.index + 1]],
                    hidden=True)

    @Part
    def extended_web(self):
        return ExtendedSurface(quantify=len(self.cutter_web),
                               surface_in=self.cutter_web[child.index].Spar,
                               distance=5,
                               side='u',
                               hidden=True)

    @Part
    def total_cutter(self):
        return SewnShell([section for section in self.extended_web] if self.extend else
                         [section.Spar for section in self.cutter_web],
                         hidden=self.hidden)


if __name__ == '__main__':
    from parapy.gui import display

    display(Cutter())
