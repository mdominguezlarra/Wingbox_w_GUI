from parapy.core import *
from parapy.geom import *
from singlespar import SingleSpar
from winggeom import WingGeom
import numpy as np


class SparSystem(GeomBase):
    front_spar_loc = Input([0.25, 0.25, 0.25, 0.25, 0.25, 0.25])
    rear_spar_loc = Input([0.75, 0.75, 0.75, 0.75, 0.75, 0.75])

    # Retrieving wing information.
    @Attribute
    def wingInfo(self):

        # Retrieving needed attributes.
        wing = WingGeom()
        unscaled_airfoils = wing.profile_order[2]
        scaled_airfoils = wing.profile_order[0]

        starting_points = []
        chords = []
        for airfoil in unscaled_airfoils:
            starting_points.append(airfoil.airfoil_start)
            chords.append(airfoil.airfoil_chord)

        return starting_points, chords, scaled_airfoils, wing

    # Defining airfoils as surfaces to cut.
    @Part
    def airfoil_planes(self):
        return RectangularSurface(quantify=len(self.front_spar_planes),
                                  width=100,
                                  length=100,
                                  position=rotate90(self.position, 'x'),
                                  hidden=True)

    @Part
    def airfoil_planes_translated(self):
        return TranslatedSurface(quantify=len(self.airfoil_planes),
                                 surface_in=self.airfoil_planes[child.index],
                                 displacement=self.wingInfo[0][child.index].vector,
                                 hidden=True)

    @Part
    def airfoil_wires(self):
        return IntersectedShapes(quantify=len(self.airfoil_planes_translated),
                                 shape_in=self.airfoil_planes_translated[child.index],
                                 tool=self.wingInfo[3].right_wing,
                                 hidden=True)

    @Part
    def airfoils_as_shapes(self):
        return TrimmedSurface(quantify=len(self.airfoil_wires),
                              built_from=self.airfoil_planes_translated[child.index],
                              island=self.airfoil_wires[child.index].edges[0],
                              hidden=False)

    # Front spar web definition.
    # Defining planes perpendicular to airfoils.
    @Part
    def front_spar_planes_rotated(self):
        return RectangularSurface(quantify=len(self.wingInfo[0]),
                                  width=10,
                                  length=10,
                                  position=rotate(self.position, 'y', 90 * np.pi/180),
                                  hidden=True)

    @Part
    def front_spar_planes_1st_translation(self):
        return TranslatedSurface(quantify=len(self.front_spar_planes_rotated),
                                 surface_in=self.front_spar_planes_rotated[child.index],
                                 displacement=self.wingInfo[0][child.index].vector,
                                 hidden=True)

    @Part
    def front_spar_planes(self):
        return TranslatedSurface(quantify=len(self.front_spar_planes_1st_translation),
                                 surface_in=self.front_spar_planes_1st_translation[child.index],
                                 displacement=Vector(self.front_spar_loc[child.index] * self.wingInfo[1][child.index],
                                                     0, 0),
                                 hidden=True)

    # Intersections and web definitions.
    @Attribute
    def front_spar_intersecs(self):
        intersections = []
        for i in range(len(self.front_spar_planes)):
            edg = IntersectedShapes(shape_in=self.front_spar_planes[i],
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
        return SingleSpar(quantify=len(self.front_spar_intersecs)-1,
                          curves=[self.front_spar_intersec_curves[child.index],
                                  self.front_spar_intersec_curves[child.index+1]])


    # Same process is made for the rear spar.
    @Part
    def rear_spar_planes(self):
        return TranslatedSurface(quantify=len(self.front_spar_planes_1st_translation),
                                 surface_in=self.front_spar_planes_1st_translation[child.index],
                                 displacement=Vector(self.rear_spar_loc[child.index] * self.wingInfo[1][child.index],
                                                     0, 0),
                                 hidden=True)

    @Attribute
    def rear_spar_intersecs(self):
        intersections = []
        for i in range(len(self.rear_spar_planes)):
            edg = IntersectedShapes(shape_in=self.rear_spar_planes[i],
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