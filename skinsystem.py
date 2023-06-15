from parapy.core import *
from parapy.geom import *
from cutter import Cutter
from cutting_planes import CuttingPlanes


class SkinSystem(GeomBase):
    wing = Input()
    ribs = Input()
    TE_gap = Input(0.94)  # Must be after the rearmost rear_spar_loc but less than 1

    @Part
    def te_cutter(self):
        return Cutter(wing=self.wing,
                      cut_loc=self.TE_gap,
                      extend=True,
                      hidden=True)

    @Part
    def skin_cut_basis(self):
        return SplitSurface(built_from=self.wing.right_wing,
                            tool=self.te_cutter.total_cutter,
                            hidden=True)

    @Attribute
    def skin_lst(self):

        skin_lst = []
        for i in range(int(len(self.skin_cut_basis.faces)/3)):
            skin_lst.append(self.skin_cut_basis.faces[i*3+2])

        return skin_lst

    @Part
    def skin(self):
        return SewnShell([section for section in self.skin_lst],
                         mesh_deflection=1e-4)

if __name__ == '__main__':
    from parapy.gui import display

    display(SkinSystem())
