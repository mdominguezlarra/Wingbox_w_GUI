from parapy.core import *
from parapy.geom import *
from parapy.lib.nastran.entry import *
from parapy.lib.nastran.writer import *
from parapy.mesh.salome import Mesh, Tri
from parapy.cae.nastran import read_pch
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
            l, a = values[0] * 1e-3, (values[0]/2) * 1e-3  # conversion to m.
            h, b = values[1] * 1e-3, (values[1]/2) * 1e-3  # conversion to m.

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
    cases = Input()
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

    # CONTROLS
    quad_dominance = Input(False)  # or True
    min_elem_size = Input(0.01)
    max_elem_size = Input(0.1)

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
        STEP_lst = [self.wing.skin.skin, self.wing.spars.spars[0].total_cutter, self.wing.spars.spars[1].total_cutter]
        STEP_lst.extend([rib for rib in self.wing.ribs.ribs])
        STEP_lst.extend([stringer.stringers for stringer in self.wing.stringers.top_stringers])
        STEP_lst.extend([stringer.stringers for stringer in self.wing.stringers.bottom_stringers])
        return STEP_lst

    # TODO: LATER CHANGE TO GET JUST THE LIST FOR THE STEP FILE.
    @Part
    def general_shape(self):
        return GeneralFuse(tools=self.tools_list)

    @Part
    def mesh_seed(self):
        return Tri(shape_to_mesh=self.general_shape,
                   min_size=self.min_elem_size,
                   max_size=self.max_elem_size,
                   only_2d=False,
                   quad_dominant=self.quad_dominance)

    @Part
    def mesh(self):
        return Mesh(shape_to_mesh=self.general_shape,
                    controls=[self.mesh_seed])

    # NASTRAN file writing.
    @Attribute
    def FEMentries(self):
        entries = []

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


        # Appending the finite elements to be used in the model.
        # THERE IS SOME ERROR IN WHICH THE NUMBER OF FINITE ELEMENTS IN WAY HIGHER THAN THE NUMBER OF GRID POINTS.
        elms = []
        for idx, face in enumerate(self.mesh.grid.faces):
            nodes = [mesh_id_to_GRID[node.mesh_id] for node in face.nodes]
            if len(nodes) == 3:
                elm = CTRIA3(PID=props_2d[0], G1=nodes[0], G2=nodes[1], G3=nodes[2])
                elms.append(elm)
            elif len(nodes) == 4:
                elm = CQUAD4(PID=props_2d[0], G1=nodes[0], G2=nodes[1], G3=nodes[2], G4=nodes[3])
                elms.append(elm)
        entries.extend(elms)


        # Defining forces and their locations for each case.
        pload = []
        load_cases = self.cases
        for idx_SID, load_case in enumerate(load_cases):
            p_lst = []
            forces_moms = load_case.forces_moms
            pos = load_case.forces_moms_pos

            for idx_load, point in enumerate(pos):

                # Find closest grid point
                valid_pts = self.mesh.grid.find_nodes_near(point, radius=1)
                norms = [np.sqrt((point[0] - valid_pt[0]) ** 2 + (point[1] - valid_pt[1]) ** 2 +
                                 (point[2] - valid_pt[2]) ** 2) for valid_pt in valid_pts]
                force_pt = valid_pts[norms.index(min(norms))]
                force_id = force_pt.mesh_id

                # Calculate force and append it to list.
                L_load = FORCE(SID=idx_SID+1, G=force_id, F=forces_moms[idx_load][0], N1=0, N2=0, N3=1)
                D_load = FORCE(SID=idx_SID+1, G=force_id, F=forces_moms[idx_load][1], N1=1, N2=0, N3=0)
                M_load = Moment(SID=idx_SID+1, G=force_id, M=forces_moms[idx_load][2], N1=0, N2=1, N3=0)
                load_lst = [L_load, D_load, M_load]
                p_lst.extend(load_lst)

            pload.extend(p_lst)

        entries.extend(pload)


        # Defining displacement boundary conditions.
        fix_top = self.wing.spars.spars[0].cutter_intersec_curves[0].control_points[0]
        fix_bottom = self.wing.spars.spars[0].cutter_intersec_curves[0].control_points[1]

        top_restr = self.mesh.grid.find_nodes_near(fix_top, radius=1)
        top_norms = [np.sqrt((point[0] - fix_top[0]) ** 2 + (point[1] - fix_top[1]) ** 2 +
                             (point[2] - fix_top[2]) ** 2) for point in top_restr]
        top_pt = top_restr[top_norms.index(min(top_norms))]
        top_id = top_pt.mesh_id

        bottom_restr = self.mesh.grid.find_nodes_near(fix_bottom, radius=1)
        bottom_norms = [np.sqrt((point[0] - fix_bottom[0]) ** 2 + (point[1] - fix_bottom[1]) ** 2 +
                             (point[2] - fix_bottom[2]) ** 2) for point in top_restr]
        bottom_pt = bottom_restr[bottom_norms.index(min(bottom_norms))]
        bottom_id = bottom_pt.mesh_id

        spc1 = [SPC1(SID=idx+1, C=123456, Gi=[top_id, bottom_id]) for idx in range(len(self.cases))]
        entries.extend(spc1)

        with open('output.txt', 'w') as file:
            # Write each element of the list as a separate line in the text file
            for item in entries:
                file.write(str(item) + '\n')

        return entries

    @Attribute
    def FEMwriter(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, '..', 'bdf_files', 'bdf_templates', 'wingbox_template.bdf')
        return Writer(self.FEMentries,
                      template_path=template_path,
                      template_values={'SID': 1})
