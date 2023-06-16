from parapy.core import *
from parapy.geom import *
from rib import Rib
from cutting_planes import CuttingPlanes
from cutter import Cutter
import numpy as np
from winggeom import WingGeom


class RibsSystem(GeomBase):
    wing = Input()
    rib_idx = Input()

    # Trailing edge gap
    TE_gap = Input(0.8)  # Must be after the rearmost rear_spar_loc but less than 1

    @Input
    def airfoils_TE_cut(self):
        airfoil_lst = [self.wing.airfoils[0]]
        for airfoil in self.wing.inter_airfoils:
            airfoil_lst.append(airfoil)
        airfoil_lst.append(self.wing.airfoils[-1])
        return airfoil_lst

    # Get all the ribs in a list to separate the trailing edge.
    @Input
    def ribs_list(self):
        rib_lst = []
        for rib in self.ribs_basis:
            rib_lst.append(rib.rib_surf)

        return rib_lst

        # Check which cutting plane to use in each rib.

    @Attribute
    def cut_plane_idx(self):
        cut_plane_idx = 0
        disp_accum = 0
        ribs_idx = 0
        cut_plane_lst = []

        for i in range(len(self.cutting_TE_planes)):
            cut_plane_idx_old = cut_plane_idx
            for j in range(len(self.ribs_list)):
                if self.ribs_list[j].cog[1] > \
                        round(self.cutting_TE_planes[i].plane_final_transl.displacement[1], 2) * 2 + disp_accum:
                    disp_accum += self.cutting_TE_planes[i].plane_final_transl.displacement[1] * 2
                    cut_plane_idx += 1
                    ribs_idx = j

                if cut_plane_idx == cut_plane_idx_old and j >= ribs_idx:
                    cut_plane_lst.append(cut_plane_idx)

        return cut_plane_lst

    @Attribute
    def rib_distribution(self):

        n_r = self.rib_idx
        r_span = []
        for section in range(len(n_r)):
            for i in range(n_r[section]):
                r_span.append(i * (self.wing.spans[section+1] - self.wing.spans[section])/n_r[section]
                              + self.wing.spans[section])

        r_span.append(self.wing.spans[-1])
        return r_span

    @Attribute
    def rib_sections(self):

        ribs = [self.wing.airfoils[0].scaled_foil]

        for i in self.wing.inter_airfoils:
            ribs.append(i.scaled_foil)

        ribs.append(self.wing.airfoils[-1].scaled_foil)
        return ribs

    @Part
    def essential_rib_cutter(self):
        return CuttingPlanes(quantify=len(self.rib_sections),
                             direction='chordwise',
                             starting_point=self.rib_sections[child.index].start,
                             hidden=True)

    @Part
    def essential_ribs(self):
        return TrimmedSurface(quantify=len(self.rib_sections),
                              built_from=self.essential_rib_cutter[child.index].plane_final_pos,
                              island=self.rib_sections[child.index],
                              hidden=True)

    @Part
    def ribs_uncut(self):
        return Rib(quantify=len(self.rib_distribution),
                   rib_span=self.rib_distribution[child.index],
                   skin_shell=self.wing.right_wing,
                   root_chord=self.wing.root_chord,
                   hidden=True)

    @Part
    def te_cutter(self):
        return Cutter(wing=self.wing,
                      cut_loc=self.TE_gap,
                      extend=True)

    @Part
    def ribs_cut_basis(self):
        return SplitSurface(quantify=len(self.rib_distribution),
                            built_from=self.ribs_uncut[child.index].rib_surf,
                            tool=self.te_cutter.total_cutter,
                            hidden=True)

    @Part
    def rib_cut_wires(self):
        return IntersectedShapes(quantify=len(self.ribs_cut_basis),
                                 shape_in=self.ribs_cut_basis[child.index].faces[1],
                                 tool=self.ribs_uncut[child.index].cut_tool,
                                 hidden=True)

    @Part
    def ribs(self):
        return TrimmedSurface(quantify=len(self.rib_distribution),
                              built_from=self.ribs_uncut[child.index].cut_tool,
                              island=self.rib_cut_wires[child.index].edges,
                              mesh_deflection=1e-4)


if __name__ == '__main__':
    from parapy.gui import display

    display(RibsSystem())