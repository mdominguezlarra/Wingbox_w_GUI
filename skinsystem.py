from parapy.core import *
from parapy.geom import *
from cutting_planes import CuttingPlanes


class SkinSystem(GeomBase):
    wing = Input()
    ribs = Input()
    TE_gap = Input(0.94)  # Must be after the rearmost rear_spar_loc but less than 1

    @Attribute
    def skin_faces(self):
        skin_faces = []
        cut_accum = 0
        for skin_cut in self.skin_cut_basis:
            for k in range(len(skin_cut.faces)):
                if k != range(len(skin_cut.faces)):
                    skin_faces.extend(skin_cut.faces[2 + cut_accum:cut_accum + 6:3])
                    cut_accum += 2
                    break
                else:
                    skin_faces.append(skin_cut.faces[-1])

        return skin_faces

    @Part
    def skin_basis(self):
        return SewnShell(built_from=self.wing.right_wing,
                         mesh_deflection=1e-4,
                         hidden=True)

    @Part
    def cutting_TE_planes(self):
        return CuttingPlanes(quantify=len(self.ribs.airfoils_TE_cut) - 1,
                             direction='spanwise',
                             starting_point=self.ribs.airfoils_TE_cut[child.index].airfoil_start,
                             starting_chord_length=self.ribs.airfoils_TE_cut[child.index].airfoil_chord,
                             chord_percentage=self.TE_gap,
                             ending_point=self.ribs.airfoils_TE_cut[child.index + 1].airfoil_start,
                             ending_chord_length=self.ribs.airfoils_TE_cut[child.index + 1].airfoil_chord,
                             hidden=True)

    @Part
    def skin_cut_basis(self):
        return SplitSurface(quantify=len(self.cutting_TE_planes),
                            built_from=self.skin_basis,
                            tool=self.cutting_TE_planes[child.index].plane_final_transl,
                            hidden=True)

    @Part
    def partitioned_skins(self):
        return Common(quantify=len(self.skin_faces),
                      shape_in=self.wing.right_wing,
                      tool=self.skin_faces[child.index],
                      mesh_deflection=1e-4,
                      hidden=True)

    @Part
    def skin(self):
        return SewnShell([section for section in self.partitioned_skins],
                         mesh_deflection=1e-4)

if __name__ == '__main__':
    from parapy.gui import display

    display(SkinSystem())
