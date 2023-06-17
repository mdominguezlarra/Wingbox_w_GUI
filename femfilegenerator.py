from parapy.core import *
from parapy.geom import *
from parapy.lib.nastran.entry import *
from generalfuse import GeneralFuse
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
    path = 'inputs/materials.csv'
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

    # Same material is used throughout all elements of a component.
    @Input
    def mat_props(self):
        mat_lst = []
        mat_in = self.mat_2D + self.mat_1D
        for mat in mat_in:
            mat_lst.append(mat_props_finder(mat))

        return mat_lst[0:3], mat_lst[3:]  # 2D props and 1D props lists.

    # 1D elements section selector.
    @Input
    def sec_props(self):
        return 1

    @Part
    def general_shape(self):
        return GeneralFuse(tools=self.wing.STEP_node_list)

    @Attribute
    def FEM_entries(self):
        mat = self.mat_props[0][0]
        mat_FEM = MAT1(E=mat['Et'], NU=mat['nu'])


        # PSHELL
        # EXAMPLE :::

        # CQUAD4 :::
        # EXAMPLE :::

        # CBAR :::

        # FORCE ::: DEFINE POINT LOADS.

        # SPC1 ::: DEFINE RESTRICTION IN ALL SIX DEGREES OF FREEDOM.

        return mat_FEM

    @Attribute
    def FEM_writer(self):

        return 1


if __name__ == '__main__':
    from parapy.gui import display
    display(FEMFileGenerator())