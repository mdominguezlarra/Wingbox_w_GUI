from parapy.core import *
from parapy.geom import *


class Rib(GeomBase):

    rib_span = Input()
    skin_shell = Input()
    rib_thickness = Input()
    root_chord = Input()

    @Part
    def cut_tool(self):
        return RectangularSurface(width=100*self.root_chord,
                                  length=100*self.root_chord,
                                  position=translate(rotate90(self.position, 'x'),
                                                     'z',
                                                     -self.rib_span),
                                  hidden=True)

    @Part
    def rib_wire(self):
        return IntersectedShapes(shape_in=self.skin_shell,
                                 tool=self.cut_tool,
                                 hidden=True)

    # @Part
    # def rib_surf(self):
    #     return TrimmedSurface(built_from=self.cut_tool,
    #                           island=self.rib_wire.edges[0],
    #                           hidden=False)

    @Part
    def rib_sol_r(self):
        return ExtrudedSolid(island=self.rib_wire.edges[0],
                             distance=self.rib_thickness / 2 / 1000,
                             direction='y',
                             hidden=False)

    @Part
    def rib_sol_l(self):
        return ExtrudedSolid(island=self.rib_wire.edges[0],
                             distance=self.rib_thickness / 2 / 1000,
                             direction='y_',
                             hidden=False)


    @Part
    def rib_fin(self):
        return FusedSolid(shape_in=self.rib_sol_l,
                          tool=self.rib_sol_r)
