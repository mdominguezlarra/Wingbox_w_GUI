from parapy.core import *
from parapy.geom import *
from parapy.lib.nastran.entry import *
from parapy.lib.nastran.writer import *
from parapy.mesh.salome import Mesh, Tri
from .generalfuse import GeneralFuse
import numpy as np
import csv
import os


# Function to find the mechanical properties of a material given a characteristic string.
def mat_props_finder(mat_str: str):
    cvs_units = [6.894757e6, 6.894757e6, 6.894757e6, 1, 515.378818, 6.894757e6, 6.894757e6, 6.894757e6]

    # Finding characteristic parameters of input material.
    split_mat_str = mat_str.split('-')
    t = float(split_mat_str[2]) / 25.4  # Conversion to imperial units
    split_mat_str.pop(2)
    id = '-'.join(split_mat_str)

    # Finding the correct mechanical properties.
    path = 'wingbox_code/input_data/materials.csv'
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


# Function to find cross-section properties for 1D elements.
def sec_props_finder(arg):
    props_lst = []
    for lst in arg:
        values, typ = lst
        if typ == 'dims':
            l, a = values[0], values[0] / 2
            h, b = values[1], values[1] / 2

            # Properties calculation.
            A = l * h  # Area.
            I1 = l ** 3 * (h / 12)  # Moment of inertia aligned with y direction.
            I2 = h ** 3 * (l / 12)  # Moment of inertia aligned with z direction.
            J = a * b ** 3 * ((16 / 3) - 3.36 * (b / a) * (1 - (b ** 4 / (12 * a ** 4))))  # Polar moment of inertia.

            props_lst.append([A, I1, I2, J])

        elif typ == 'moms':
            props_lst.append(values)

    return props_lst


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
    tc_select = Input('t')  # TENSION OR COMPRESSION SELECTOR
    secs = Input([[[1, 1], 'dims'],  # STRINGERS
                  [[1, 1], 'dims'],  # SPAR CAPS
                  [[1, 0.0833, 0.0833, 2.2533], 'moms']])  # RIB CAPS

    # Same material is used throughout all elements of a component.
    @Input
    def mat_props(self):
        mat_lst = []
        mat_in = self.mat_2D + self.mat_1D
        for mat in mat_in:
            mat_lst.append(mat_props_finder(mat))

        return mat_lst  # 2D props and 1D props lists.

    # Creation of parts for FEM mesh.
    @Attribute
    def tools_list(self):
        lst = [rib for rib in self.wing.ribs.ribs]
        lst.extend([self.wing.skin.skin, self.wing.spars.spars[0].total_cutter, self.wing.spars.spars[1].total_cutter])
        lst = self.wing.skin.skin
        return lst

    # @Part
    # def general_shape(self):
    #     return GeneralFuse(tools=self.tools_list)

    @Part
    def mesh_seed(self):
        return Tri(shape_to_mesh=self.tools_list,
                   min_size=0.01,
                   max_size=0.1,
                   only_2d=False,
                   quad_dominant=False)

    @Part
    def mesh(self):
        return Mesh(shape_to_mesh=self.tools_list,
                    controls=[self.mesh_seed])

    # NASTRAN file writing.
    @Attribute
    def FEM_entries(self):
        entries = []
        SID1 = 1

        # Defining materials to be used.
        mat_2d = [[MAT1(E=mat['E' + self.tc_select], NU=mat['nu'], RHO=mat['rho']), mat['t']] for idx, mat in
                  enumerate(self.mat_props) if idx <= 2]
        mat_1d = [MAT1(E=mat['E' + self.tc_select], NU=mat['nu']) for idx, mat in enumerate(self.mat_props) if idx > 2]

        # Defining element properties.
        props_1d = [PBAR(MID=mat, A=props[0], I1=props[1], I2=props[2], J=props[3]) for
                    mat, props in zip(mat_1d, sec_props_finder(self.secs))]
        props_2d = [PSHELL(MID1=mat[0], T=mat[1], MID2=mat[0], MID3=mat[0]) for mat in mat_2d]

        # Creating grid for the FEM model.
        mesh_id_to_GRID = {}
        for node in self.mesh.grid.nodes:
            grid = GRID(ID=node.mesh_id, X1=node.x, X2=node.y, X3=node.z)
            mesh_id_to_GRID[node.mesh_id] = grid
            entries.append(grid)

        tris = []
        for idx, face in enumerate(self.mesh.grid.faces):
            nodes = [mesh_id_to_GRID[node.mesh_id] for node in face.nodes]
            tri = CTRIA3(PID=props_2d[0], G1=nodes[0], G2=nodes[1], G3=nodes[2])
            tris.append(tri)

        pload = PLOAD2(SID=SID1, P=1000.0, EIDi=tris[300:302])
        entries.append(pload)

        # Placing displacement boundary conditions.
        fix_top = self.wing.spars.spars[0].cutter_intersec_curves[0].control_points[0]
        fix_bottom = self.wing.spars.spars[0].cutter_intersec_curves[0].control_points[1]

        top_restr = self.mesh.grid.find_nodes_near(fix_top, radius=1e-1)
        top_norms = [np.sqrt((point[0] - fix_top[0]) ** 2 + (point[1] - fix_top[1]) ** 2 +
                             (point[2] - fix_top[2]) ** 2) for point in top_restr]
        top_pt = top_restr[top_norms.index(min(top_norms))]
        top_id = top_pt.mesh_id

        bottom_restr = self.mesh.grid.find_nodes_near(fix_bottom, radius=1e-1)
        bottom_norms = [np.sqrt((point[0] - fix_bottom[0]) ** 2 + (point[1] - fix_bottom[1]) ** 2 +
                             (point[2] - fix_bottom[2]) ** 2) for point in top_restr]
        bottom_pt = bottom_restr[bottom_norms.index(min(bottom_norms))]
        bottom_id = bottom_pt.mesh_id

        spc1 = SPC1(SID = 2, C=123456, Gi=[top_id, bottom_id])
        entries.append(spc1)

        return entries, SID1

    @Attribute
    def FEM_writer(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, '..', 'bdf_files', 'bdf_templates', 'wingbox_template.bdf')
        return Writer(self.FEM_entries[0],
                      template_path=template_path,
                      template_values={"SID": self.FEM_entries[1]})
