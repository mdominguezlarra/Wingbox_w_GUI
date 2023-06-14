from parapy.core import *
from parapy.geom import *
from rib import Rib
from sparsystem import SparSystem
from cutting_planes import CuttingPlanes
from winggeom import WingGeom


class WingBox(GeomBase):
    # Geometry
    wing = Input(WingGeom(), in_tree=True)

    # Ribs
    rib_pitch = Input(0.2)
    rib_thickness = Input(1)
    rib_index = Input(0)

    # Spars
    front_spar_loc = Input([0.25, 0.25, 0.25, 0.25, 0.25, 0.25])  # Must be between 0 and the foremost rear_spar_loc
    rear_spar_loc = Input([0.75, 0.75, 0.75, 0.75, 0.75, 0.75])  # Must be between the rearmost front_spar_loc and 1

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
        cut_plane_lst = []
        disp_accum = 0
        ribs_idx = 0
        num_cutting_planes = len(self.cutting_TE_planes)
        num_ribs = len(self.ribs_list)

        for i in range(num_cutting_planes):
            cut_plane_idx_old = cut_plane_idx
            for j in range(num_ribs):
                if self.ribs_list[j].cog[1] > self.cutting_TE_planes[i].plane_final_transl.displacement[1] * 2 + disp_accum:
                    disp_accum += self.cutting_TE_planes[i].plane_final_transl.displacement[1] * 2
                    cut_plane_idx += 1
                    ribs_idx = j

                if cut_plane_idx == cut_plane_idx_old and j >= ribs_idx:
                    cut_plane_lst.append(cut_plane_idx)

        return cut_plane_lst

    @Attribute
    def rib_distribution(self):
        if self.rib_index == 0:
            n_r = int(self.wing.spans[-1] // self.rib_pitch)
            r_span = []
            for i in range(n_r):
                r_span.append(i * self.rib_pitch)
            n_r = n_r + 1
            r_span.append(self.wing.spans[-1])

        else:
            print('Place other distribution indices')
            n_r = 0
            r_span = 0

        return n_r, r_span

    @Part
    def ribs_basis(self):
        return Rib(quantify=self.rib_distribution[0],
                   rib_span=self.rib_distribution[1][child.index],
                   rib_thickness=self.rib_thickness,
                   skin_shell=self.wing.right_wing,
                   root_chord=self.wing.root_chord)

    @Part
    def spars(self):
        return SparSystem(front_spar_loc=self.front_spar_loc,
                          rear_spar_loc=self.rear_spar_loc,
                          wing=self.wing)

    @Part
    def skin_basis(self):
        return SewnShell(self.wing.right_wing,
                         mesh_deflection=1e-4)

    @Part
    def cutting_TE_planes(self):
        return CuttingPlanes(quantify=len(self.airfoils_TE_cut) - 1,
                             direction='spanwise',
                             starting_point=self.airfoils_TE_cut[child.index].airfoil_start,
                             starting_chord_length=self.airfoils_TE_cut[child.index].airfoil_chord,
                             chord_percentage=self.TE_gap,
                             ending_point=self.airfoils_TE_cut[child.index + 1].airfoil_start,
                             ending_chord_length=self.airfoils_TE_cut[child.index + 1].airfoil_chord,
                             hidden=False)

    @Part
    def skin_cut_basis(self):
        return SplitSurface(quantify=len(self.cutting_TE_planes),
                            built_from=self.skin_basis,
                            tool=self.cutting_TE_planes[child.index].plane_final_transl)

    @Part
    def ribs_cut_basis(self):
        return SplitSurface(quantify=len(self.ribs_list),
                            built_from=self.ribs_list[child.index],
                            tool=self.cutting_TE_planes[self.cut_plane_idx[child.index]].plane_final_transl)


if __name__ == '__main__':
    from parapy.gui import display

    display(WingBox())
