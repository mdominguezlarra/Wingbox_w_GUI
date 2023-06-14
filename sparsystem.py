from parapy.core import *
from parapy.geom import *
from singlespar import SingleSpar
from cutting_planes import CuttingPlanes
from winggeom import WingGeom


class SparSystem(GeomBase):
    front_spar_loc = Input([0.25, 0.25, 0.25, 0.25, 0.25, 0.25])
    rear_spar_loc = Input([0.75, 0.75, 0.75, 0.75, 0.75, 0.75])
    wing = Input(WingGeom())

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
        return CuttingPlanes(quantify=len(self.front_spar_planes),
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

    # Front spar web definition.
    @Part
    def front_spar_planes(self):
        return CuttingPlanes(quantify=len(self.wingInfo[0]),
                             direction='spanwise',
                             starting_point=self.wingInfo[0][child.index],
                             starting_chord_length=self.wingInfo[1][child.index],
                             chord_percentage=self.front_spar_loc[child.index],
                             hidden=True)

    # Intersections and web definitions.
    @Attribute
    def front_spar_intersecs(self):
        intersections = []
        for i in range(len(self.front_spar_planes)):
            edg = IntersectedShapes(shape_in=self.front_spar_planes[i].plane_final_pos,
                                    tool=self.airfoils_as_shapes[i],
                                    hidden=True)
            intersections.append(edg.edges)

        return intersections

    @Part
    def front_spar_intersec_curves(self):
        return ComposedCurve(quantify=len(self.front_spar_intersecs),
                             built_from=self.front_spar_intersecs[child.index],
                             hidden=True)

    @Part
    def front_spar_web(self):
        return SingleSpar(quantify=len(self.front_spar_intersecs) - 1,
                          curves=[self.front_spar_intersec_curves[child.index],
                                  self.front_spar_intersec_curves[child.index + 1]])

    # Same process is made for the rear spar.
    @Part
    def rear_spar_planes(self):
        return CuttingPlanes(quantify=len(self.wingInfo[0]),
                             direction='spanwise',
                             starting_point=self.wingInfo[0][child.index],
                             starting_chord_length=self.wingInfo[1][child.index],
                             chord_percentage=self.rear_spar_loc[child.index],
                             hidden=True)

    @Attribute
    def rear_spar_intersecs(self):
        intersections = []
        for i in range(len(self.rear_spar_planes)):
            edg = IntersectedShapes(shape_in=self.rear_spar_planes[i].plane_final_pos,
                                    tool=self.airfoils_as_shapes[i])
            intersections.append(edg.edges)

        return intersections

    @Part
    def rear_spar_intersec_curves(self):
        return ComposedCurve(quantify=len(self.rear_spar_intersecs),
                             built_from=self.rear_spar_intersecs[child.index],
                             hidden=True)

    @Part
    def rear_spar_web(self):
        return SingleSpar(quantify=len(self.rear_spar_intersecs) - 1,
                          curves=[self.rear_spar_intersec_curves[child.index],
                                  self.rear_spar_intersec_curves[child.index + 1]])


if __name__ == '__main__':
    from parapy.gui import display

    display(SparSystem())
