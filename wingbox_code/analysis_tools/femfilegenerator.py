from parapy.core import *
from parapy.geom import *
from parapy.lib.nastran.entry import *
from parapy.lib.nastran.writer import *
from parapy.mesh.salome import Mesh
from parapy.mesh.salome.controls import TriMefisto
from .generalfuse import GeneralFuse
from parapy.mesh import *
from parapy.lib.nastran import *
import numpy as np
import csv


def mat_props_finder(mat_str: str):
    cvs_units = [6.894757e6, 6.894757e6, 6.894757e6, 1, 515.378818, 6.894757e6, 6.894757e6, 6.894757e6]

    # Finding characteristic parameters of input material.
    split_mat_str = mat_str.split('-')
    t = float(split_mat_str[2]) / 25.4  # Conversion to imperial units
    split_mat_str.pop(2)
    id = '-'.join(split_mat_str)

    # Finding the correct mechanical properties.
    path = 'code/input_data/materials.csv'
    with open(path, 'r', newline='') as file:
        mat_file = csv.reader(file)
        for idx, row in enumerate(mat_file):
            if idx == 0:
                header = row[6:len(row) - 1]
                header.append('t')
            else:
                row_str = row[1] + '-' + row[2] + '-' + row[5]
                t_m, t_p = float(row[3]), float(row[4])
                if id == row_str and t_m < t < t_p:
                    prop_lst = [float(row[k]) * cvs_units[k - 6] for k in range(6, len(row) - 1)]
                    prop_lst.append(t)
                    prop_dict = {key: value for (key, value) in zip(header, prop_lst)}

                    return prop_dict


class FEMFileGenerator(GeomBase):
    wing = Input()

    mat_2D = Input([
        'Al2024-T3-1.27-A',  # SKIN
        'Al2024-T3-1.27-A',  # SPAR WEB
        'Al2024-T3-1.27-A'])  # RIBS
    mat_1D = Input([
        'Al7475-T61-1.524-S',  # STRINGERS
        'Al7475-T61-1.524-S',  # SPAR CAPS
        'Al7475-T61-1.524-S'])  # RIB CAPS

    tc_select = Input('t')  # TENSIOR OR COMPRESSION SELECTOR

    # Same material is used throughout all elements of a component.
    @Input
    def mat_props(self):
        mat_lst = []
        mat_in = self.mat_2D + self.mat_1D
        for mat in mat_in:
            mat_lst.append(mat_props_finder(mat))

        return mat_lst  # 2D props and 1D props lists.

    # 1D elements section selector.
    @Input
    def sec_props(self):
        return 1

    @Attribute
    def FEM_entries(self):
        # Defining materials to be used.
        mat_2d = [[MAT1(E=mat['E' + self.tc_select], NU=mat['nu'], RHO=mat['rho']), mat['t']] for idx, mat in
                  enumerate(self.mat_props) if idx <= 2]
        mat_1d = [MAT1(E=mat['E' + self.tc_select], NU=mat['nu']) for idx, mat in enumerate(self.mat_props) if idx > 2]

        # Defining element properties.
        props_2d = [PSHELL(MID1=mat[0], T=mat[1], MID2=mat[0], MID3=mat[0]) for mat in mat_2d]
        props_1d = [PBAR()]

        # Creating grid for the FEM model.
        mesh_id_to_GRID = {}
        for node in self.mesh.grid.nodes:
            grid = GRID(ID=node.mesh_id, X1=node.x, X2=node.y, X3=node.z)
            mesh_id_to_GRID[node.mesh_id] = grid

        # CQUAD4 :::
        # USE CTRIA3 FOR TRIANGULAR ELEMENTS?

        # PBARL

        # CBAR :::

        # FORCE ::: DEFINE POINT LOADS.

        # SPC1 ::: DEFINE RESTRICTION IN ALL SIX DEGREES OF FREEDOM.

        return props_2d

    # @Attribute
    # def FEM_writer(self):
    #     return Writer(self.primitives,
    #                   template_path="bdf_templates/rectangular_plate_template.bdf",
    #                   template_values={"SID": SID})

    @Attribute
    def tools_list(self):
        lst = [rib for rib in self.wing.ribs.ribs]
        lst.extend([self.wing.skin.skin, self.wing.spars.spars[0].total_cutter, self.wing.spars.spars[1].total_cutter])
        return lst

    @Part
    def general_shape(self):
        return GeneralFuse(tools=self.tools_list)

    @Part
    def mesh_seed(self):
        return TriMefisto(shape_to_mesh=self.general_shape,
                          max_area=0.1)

    @Part
    def general_mesh(self):
        return Mesh(shape_to_mesh=self.general_shape,
                    controls=[self.mesh_seed])


if __name__ == '__main__':
    from parapy.gui import display
    display(FEMFileGenerator())