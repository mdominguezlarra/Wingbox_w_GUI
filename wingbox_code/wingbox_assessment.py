from parapy.core import *
from parapy.geom import *
from parapy.core.validate import *
from .geometry.geometry_tools.winggeom import WingGeom
from .geometry.wingbox import WingBox
from .analysis_tools.avl_analysis import AvlAnalysis
from .format.tk_warn import type_warning, material_validation
from .analysis_tools.femfilegenerator import FEMFileGenerator
import os
import shutil
import matplotlib.pyplot as plt
import subprocess
import time
import psutil


def check_nastran_running():
    for proc in psutil.process_iter(['pid', 'name']):
        if "nastran" in proc.info['name'].lower():
            return True
    return False


def bdf_file_cases(file_path, case_settings):
    """ Adds the subcases to be run by NASTRAN in the BDF file. """

    search_line = 'ECHO = NONE'
    commands = ["SUBCASE ",
                "    LOAD = ",
                "    SPC = ",
                "    DISP = ALL",
                "    DISPLACEMENT(SORT1,REAL)=ALL",
                "    SPCFORCES(SORT1,REAL)=ALL",
                "    STRESS(SORT1,REAL,VONMISES,BILIN)=ALL"]

    with open(file_path, 'r+') as file:
        content = file.read()  # Read the entire content into a variable
        file.seek(0)  # Move the file pointer to the beginning
        file.truncate()  # Clear the file content

        for line in content.splitlines():
            file.write(line + '\n')  # Write the original line back

            if search_line in line:
                for k in range(len(case_settings)):
                    var = ''
                    if 0 <= k < 3:
                        var = str(k + 1)
                    for i, command in enumerate(commands):
                        if i < 3:
                            file.write(command + var + '\n')
                        else:
                            file.write(command + '\n')


def get_plots_reacts(load_cases):
    for idx, case in enumerate(load_cases):
        ids = ['L', 'D', 'M']
        L_vec = [load[0] for load in case.forces_moms]
        D_vec = [load[1] for load in case.forces_moms]
        M_vec = [load[2] for load in case.forces_moms]
        F_vec = [L_vec, D_vec, M_vec]
        y_vec = [pos[1] for pos in case.forces_moms_pos]

        # Plotting and saving.
        px = 1 / plt.rcParams['figure.dpi']
        for id, vec in enumerate(F_vec):
            plt.figure(figsize=(800 * px, 600 * px))
            plot_handle = plt.plot(y_vec, vec)
            plt.grid(True)
            plt.xlabel('y [m]')
            plt.ylabel(ids[id] + ' [N]')
            path_to_save = os.path.join(os.path.dirname(__file__),
                                        r'output_data\avl_plots\ ' + ids[id] + '_case_' + str(idx + 1))
            plt.savefig(path_to_save)

    # Getting general forces and reactions for each case.
    f06_loc = os.path.join(os.path.dirname(__file__), r'output_data\wingbox_bulkdata.f06')
    react_loc = r'output_data\react_forces_moms\ '
    totals_lst = []

    with open(f06_loc, 'r') as file:
        for line in file:
            if '             TOTALS' in line:
                totals_lst.append(line)

    totals_lst = totals_lst[0:3]

    for idx, react in enumerate(totals_lst):
        values = react.split()
        label = values[0].strip()
        values = [float(val) for val in values[1:]]
        write_path = os.path.join(os.path.dirname(__file__), react_loc + 'react_SUBCASE' + str(idx + 1) + '.txt')

        with open(write_path, 'w') as file:
            file.write('THE TOTAL REACTION FORCES OF THE STRUCTURE OF THE WING ARE:\n')
            file.write('FX=' + str(round(values[0], 3)) + ' N \n')
            file.write('FY=' + str(round(values[1], 3)) + ' N \n')
            file.write('FZ=' + str(round(values[2], 3)) + ' N \n')
            file.write('MX=' + str(round(values[3], 3)) + ' Nm \n')
            file.write('MY=' + str(round(values[4], 3)) + ' Nm \n')
            file.write('MZ=' + str(round(values[5], 3)) + ' Nm \n')


class WingBoxAssessment(GeomBase):
    """
    Create a wing model with multiple sections and airfoils. Further, create its corresponding wingbox. These
    geometries can then be analyzed aerodynamically (through AVL) and structurally (through NASTRAN). All
    of these analyses are integrated through this class.
    """

    # ALL INPUTS ARE ESTABLISHED HERE
    # INPUTS MUST BE ON SI UNITS, UNLESS STATED OTHERWISE IN COMMENTS.

    # WING GEOMETRY
    # For 1st section
    root_chord = Input(validator=And(Positive(), IsInstance((int, float))))  # m.

    # Following sections
    n_sections = Input(validator=And(Positive(), IsInstance(int)))
    spans = Input(validator=IsInstance(list))
    tapers = Input(validator=IsInstance(list))
    sweeps = Input(validator=IsInstance(list))
    dihedrals = Input(validator=IsInstance(list))
    twist = Input(validator=IsInstance(list))

    # Airfoils
    n_airfoils = Input(validator=And(Positive(), IsInstance(int)))
    airfoil_sections = Input(validator=IsInstance(list))  # percentage wrt to root.
    airfoil_names = Input(validator=IsInstance(list))

    # AIRCRAFT GENERAL INPUTS
    weight = Input(validator=And(Positive(), IsInstance((int, float))))  # kg.
    speed = Input(validator=And(Positive(), IsInstance((int, float))))  # m/s.
    height = Input(validator=IsInstance((int, float)))  # ft.

    # LOAD CASES
    n_loads = Input(validator=And(Positive(), IsInstance(int)))
    case_settings = Input(validator=IsInstance(list))

    # STRUCTURAL DETAILS
    # Ribs
    rib_idx = Input(validator=IsInstance(list))

    # Spars
    front_spar_loc = Input(validator=IsInstance(list))
    rear_spar_loc = Input(validator=IsInstance(list))

    # Stringers
    stringer_idx = Input(validator=IsInstance(list))

    # Trailing edge gaps for skin and ribs
    TE_ribs_gap = Input(validator=Range(0, 0.98))  # Must be after the rearmost rear_spar_loc but less than 0.98
    TE_skin_gap = Input(validator=Range(0, 0.98))  # Must be after the rearmost rear_spar_loc but less than 1

    # FEM MODEL INPUTS
    # AERODYNAMIC LOADS ARE AUTOMATICALLY CALCULATED USING GET_FORCES.
    # File paths for .bdf file and NASTRAN executable.
    bdf_file_folder = Input(r"wingbox_code\bdf_files", validator=Optional(IsInstance(str)))
    nastran_path = Input(r'"C:\Program Files\MSC.Software\NaPa_SE\20231\Nastran\bin\nastranw.exe"',
                         validator=IsInstance(str))

    # Mesh definition.
    quad_dominance = Input(False, validator=IsInstance(bool))
    min_elem_size = Input(validator=And(IsInstance((float, int)), Positive()))
    max_elem_size = Input(validator=And(IsInstance((float, int)), Positive()))

    # Material definitions. Strings combination of 'alloy-temper-thickness-basis'. Thickness in mm.
    mat_2D = Input(validator=IsInstance(list))  # RIBS
    mat_1D = Input(validator=IsInstance(list))  # RIB CAPS

    tc_select = Input(validator=And(IsInstance(str), OneOf(['t', 'c'])))  # TENSION OR COMPRESSION SELECTOR

    # Cross-sections properties. Inputs are either dimensions of a rectangle, or mechanical properties.
    # e.g. 'dims': [horizontal, vertical] # in mm
    # e.g. 'moms': [area,  I1,     I2,      J]
    secs = Input(validator=IsInstance(list))

    # BCs
    bcs = Input(validator=IsInstance(list))

    # SPECIAL VALIDATORS #

    @spans.validator
    def spans(self, span):
        """
        Validates whether the span inputs are positive, in ascending order, and not defined at the same position,
        as well as correct type and number of inputs
        :param span:
        :return: bool
        """
        if len(span) != self.n_sections + 1:
            msg = 'The number of section spans must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        if 0 not in span:
            msg = 'The "0" span station must be kept unchanged'
            return False, msg

        for i in range(1, len(span[1:])):
            warn, msg = type_warning(span[i], 'span', (int, float))
            if not warn:
                return False, msg

            if span[i] <= 0:
                msg = 'The section spans cannot be negative or equal to zero. Change section {}'.format(i)
                return False, msg
            if span[i] == span[i-1]:
                msg = 'Two sections cannot be defined at the same span length. Change section {}'.format(i)
                return False, msg
            if span[i] < span[i-1]:
                msg = 'The sections must be organized in ascending order. Change section {}'.format(i)
                return False, msg

        return True

    @tapers.validator
    def tapers(self, taper):
        """
        Validates if the taper inputs are positive, and the correct type
        :param taper:
        :return: bool
        """
        if len(taper) != self.n_sections + 1:
            msg = 'The number of section tapers must be coherent with the number of sections.'\
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(taper)):
            warn, msg = type_warning(taper[i], 'taper', (int, float))
            if not warn:
                return False, msg

            if taper[i] <= 0:
                msg = 'The section taper cannot be negative or equal to zero. Change section {}'.format(i)
                return False, msg

        return True

    @sweeps.validator
    def sweeps(self, sweep):
        """
        Validates if the sweep inputs are within range, and the correct type
        :param sweep:
        :return:
        """
        if len(sweep) != self.n_sections:
            msg = 'The number of section sweeps must be coherent with the number of sections.'\
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(sweep)):
            warn, msg = type_warning(sweep[i], 'sweep', (int, float))
            if not warn:
                return False, msg

            if sweep[i] < -85 or sweep[i] > 85:
                msg = 'The sweep value must be kept in the range [-85, 85] degrees. Change section {}'.format(i)
                return False, msg

        return True

    @dihedrals.validator
    def dihedrals(self, dihedral):
        """
        Validates if the dihedral inputs are within range, and the correct type
        :param dihedral:
        :return:
        """
        if len(dihedral) != self.n_sections:
            msg = 'The number of section dihedrals must be coherent with the number of sections.'\
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(dihedral)):
            warn, msg = type_warning(dihedral[i], 'dihedral', (int, float))
            if not warn:
                return False, msg

            if dihedral[i] < -85 or dihedral[i] > 85:
                msg = 'The sweep value must be kept in the range [-85, 85] degrees. Change section {}'.format(i)
                return False, msg

        return True

    @twist.validator
    def twist(self, twists):
        """
        Validates if the twist inputs are within range, and the correct type
        :param twists:
        :return:
        """
        if len(twists) != self.n_sections + 1:
            msg = 'The number of section twists must be coherent with the number of sections.'\
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(twists)):
            warn, msg = type_warning(twists[i], 'twist', (int, float))
            if not warn:
                return False, msg
            if twists[i] < -85 or twists[i] > 85:
                msg = 'The sweep value must be kept in the range [-85, 85] degrees. Change section {}'.format(i)
                return False, msg

        return True

    @airfoil_sections.validator
    def airfoil_sections(self, sections):
        """
        Validates the airfoil section order, limits, and coherence.
        :param sections:
        :return:
        """
        if len(sections) != self.n_airfoils:
            msg = 'The number of airfoil locations must be coherent with the number of airfoils.'\
                  ' If you want to add/remove sections, change n_airfoils'
            return False, msg

        if (0 or 1) not in sections:
            msg = 'Either no tip or no root airfoil was input'
            return False, msg

        for i in range(1, len(sections[1:])):
            warn, msg = type_warning(sections[i], 'airfoil sections', (int, float))
            if not warn:
                return False, msg
            if sections[i] <= 0:
                msg = 'The airfoil span sections cannot be negative or equal to zero.' \
                      'Change airfoil location {}'.format(i)
                return False, msg
            if sections[i] == sections[i - 1]:
                msg = 'Two airfoils cannot be defined at the same span length. Change airfoil location {}'.format(i)
                return False, msg
            if sections[i] < sections[i - 1]:
                msg = 'The airfoils must be organized in ascending order. Change airfoil location {}'.format(i)
                return False, msg
            if sections[i] > 1 or sections[i] < 0:
                msg = 'The airfoil location cannot be located outside of the span. Change airfoil location {}'.format(i)
                return False, msg

        return True

    @airfoil_names.validator
    def airfoil_names(self, names):
        """
        Validates the airfoil name feasibility, either by searching in the airfoil folder or by using the
        NACA 4/5 digit generator.
        :param names:
        :return:
        """

        name_database_dat = os.listdir(r'wingbox_code\input_data\airfoils')
        name_database = [name.split('.')[0] for name in name_database_dat]

        if len(names) != self.n_airfoils:
            msg = 'The number of airfoil names must be coherent with the number of airfoils.'\
                  ' If you want to add/remove sections, change n_airfoils'
            return False, msg

        for i in range(len(names)):
            warn, msg = type_warning(names[i], 'airfoil names', str)
            if not warn:
                return False, msg

            if (names[i] not in name_database) and not (len(names[i]) == 4 or len(names[i]) == 5):
                msg = 'Invalid airfoil name. Make sure the name is correctly written or contains either 4 or 5 digits.'
                return False, msg

        return True

    @case_settings.validator
    def case_settings(self, cases):
        """
        Validates the strict naming convention of the case_settings input, as well as its coherence.
        :param cases:
        :return:
        """

        for i in cases:
            if len(i) != self.n_loads:
                msg = 'The number of load cases must be coherent.' \
                      ' If you want to add/remove load cases, change n_loads'
                return False, msg

        for i in cases[0]:
            warn, msg = type_warning(i, 'load case names', str)
            if not warn:
                return False, msg

        for i in cases[1]:
            if i != 'alpha' and i != 'CL':
                msg = 'Invalid load case variable name. Please use either "alpha" or "CL"'
                return False, msg

        for i in cases[2]:
            warn, msg = type_warning(i, 'load case variable value', (float, int))
            if not warn:
                return False, msg

        return True

    @rib_idx.validator
    def rib_idx(self, ribs):
        """
        Validates list coherence as well as that the elements are positive and integers
        :param ribs:
        :return:
        """
        if len(ribs) != self.n_sections:
            msg = 'The number of section ribs must be coherent with the number of sections.'\
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for rib in ribs:
            warn, msg = type_warning(rib, 'rib number', int)
            if not warn:
                return False, msg

            if rib <= 0:
                msg = 'The amount of ribs must at least be 1 for every section'
                return False, msg

        return True

    @front_spar_loc.validator
    def front_spar_loc(self, fs_locs):
        """
        It validates the location of the spars, its coherence, and makes sure that it stays within the chord
        and does not cross over the rear spar.
        :param fs_locs:
        :return:
        """

        if len(fs_locs) != self.n_sections + 1:
            msg = 'The number of section front spar locations must be coherent with the number of sections.'\
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(fs_locs)):
            warn, msg = type_warning(fs_locs[i], 'front spar location', float)
            if not warn:
                return False, msg

            if fs_locs[i] <= 0 or fs_locs[i] >= 1:
                msg = 'Front spar locations must be limited between 0 and 1 to stay within the chord'
                return False, msg

            if fs_locs[i] >= self.rear_spar_loc[i]:
                msg = 'The front spar cannot be further aft than the rear spar'
                return False, msg

        return True

    @rear_spar_loc.validator
    def rear_spar_loc(self, rs_locs):
        """
        It validates the location of the spars, its coherence, and makes sure that it stays within the chord
        and does not cross over the front spar.
        :param rs_locs:
        :return:
        """

        if len(rs_locs) != self.n_sections + 1:
            msg = 'The number of section rear spar locations must be coherent with the number of sections.'\
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(rs_locs)):
            warn, msg = type_warning(rs_locs[i], 'rear spar location', float)
            if not warn:
                return False, msg

            if rs_locs[i] <= 0 or rs_locs[i] >= 1:
                msg = 'Rear spar locations must be limited between 0 and 1 to stay within the chord'
                return False, msg

            # if rs_locs[i] <= self.front_spar_loc[i]:
            #     msg = 'The rear spar cannot be further front than the front spar'
            #     return False, msg

        return True

    @stringer_idx.validator
    def stringer_idx(self, stringers):
        """
        Validates list coherence as well as that the elements are positive and integers
        :param stringers:
        :return:
        """
        if len(stringers) != self.n_sections:
            msg = 'The number of section stringers must be coherent with the number of sections.'\
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for section in stringers:
            for num_stringer in section:
                warn, msg = type_warning(num_stringer, 'stringer', int)
                if not warn:
                    return False, msg
            if len(section) != 2:
                msg = 'Wrong number of inputs. The list must have two inputs per section: top and bottom stringers.'
                return False, msg

        return True

    @TE_skin_gap.validator
    def TE_skin_gap(self, value):
        """
        Verifies that the gap is kept further back than the rear spar
        :param value:
        :return:
        """
        for i in range(self.n_sections + 1):
            if value < self.rear_spar_loc[i]:
                msg = 'The skin cut location cannot be located further front than the aft spar.'
                return False, msg
            if value > 0.98:
                msg = 'The skin cut location cannot be located more than 98% of the chord'
                return False, msg

        return True

    @TE_ribs_gap.validator
    def TE_ribs_gap(self, value):
        """
        Verifies that the gap is kept further back than the rear spar
        :param value:
        :return:
        """
        for i in range(self.n_sections + 1):
            if value < self.rear_spar_loc[i]:
                msg = 'The rib cut location cannot be located further front than the aft spar.'
                return False, msg
            if value > 0.98:
                msg = 'The rib cut location cannot be located more than 98% of the chord'
                return False, msg

        return True

    @mat_1D.validator
    def mat_1D(self, materials):
        """
        Validates that the name of the material will be accepted by the NASTRAN interface later on
        :param materials:
        :return:
        """
        for material in materials:
            warn, msg = type_warning(material, 'material', str)
            if not warn:
                return False, msg

            names, temper, basis, partial_names, thicknesses = material_validation()
            txt = material.split('-')
            t = float(txt[2]) / 25.4  # Conversion to imperial units
            txt.pop(2)
            material_partial = '-'.join(txt)

            if txt[0] not in names:
                msg = 'Material Input A: Invalid material name. Choose one between {}.'.format(set(names))
                return False, msg

            if txt[1] not in temper:
                msg = 'Material Input B:Invalid material temper. Choose one between {}.'.format(set(temper))
                return False, msg

            if txt[2] not in basis:
                msg = 'Material Input D: Invalid material basis. Choose one between {}.'.format(set(basis))
                return False, msg

            if material_partial not in partial_names:
                msg = 'Material input has not been found. Make sure that the combination of A-B-C-D inputs' \
                      ' is feasible.'
                return False, msg

            for i in range(len(partial_names)):
                if material_partial == partial_names[i] and thicknesses[i][0] < t < thicknesses[i][1]:
                    return True

            msg = 'Material Input C: Invalid material thickness. Make sure it is between the specified limits.'
            return False, msg

        return

    @mat_2D.validator
    def mat_2D(self, materials):
        """
        Validates that the name of the material will be accepted by the NASTRAN interface later on
        :param materials:
        :return:
        """
        for material in materials:
            warn, msg = type_warning(material, 'material', str)
            if not warn:
                return False, msg

            names, temper, basis, partial_names, thicknesses = material_validation()
            txt = material.split('-')
            t = float(txt[2]) / 25.4  # Conversion to imperial units
            txt.pop(2)
            material_partial = '-'.join(txt)

            if txt[0] not in names:
                msg = 'Material Input A: Invalid material name. Choose one between {}.'.format(set(names))
                return False, msg

            if txt[1] not in temper:
                msg = 'Material Input B:Invalid material temper. Choose one between {}.'.format(set(temper))
                return False, msg

            if txt[2] not in basis:
                msg = 'Material Input D: Invalid material basis. Choose one between {}.'.format(set(basis))
                return False, msg

            if material_partial not in partial_names:
                msg = 'Material input has not been found. Make sure that the combination of A-B-C-D inputs' \
                      ' is feasible.'
                return False, msg

            for i in range(len(partial_names)):
                if material_partial == partial_names[i] and thicknesses[i][0] < t < thicknesses[i][1]:
                    return True

            msg = 'Material Input C: Invalid material thickness. Make sure it is between the specified limits.'
            return False, msg

        return

    @nastran_path.validator
    def nastran_path(self, path):
        """ Verifies if the NASTRAN path exists """

        if not os.path.exists(path):
            msg = 'NASTRAN folder/executable does not exist. Please install NASTRAN, or correct the folder path.'
            return False, msg

        return True

    @bdf_file_folder.validator
    def bdf_file_folder(self, path):
        """
        Verifies that the bdf file path exists
        :param path:
        :return:
        """
        if not os.path.isdir(path):
            msg = 'Folder to save .bdf file does not exist. Please create this folder or correct the folder path.'
            return False, msg

        return True

    @min_elem_size.validator
    def min_elem_size(self, value):
        """
        Verifies that the minimum element size is not larger than the maximum element size
        :param value:
        :return:
        """
        if value > self.max_elem_size:
            msg = 'Minimum element size cannot be greater than the maximum element size.'
            return False, msg

        return True

    @secs.validator
    def secs(self, cs_lst):
        """
        Verifies that the tight naming scheme of the cross-section input is respected
        :param cs_lst:
        :return:
        """
        if len(cs_lst) != 3:
            msg = 'The number of cross-section descriptions cannot be changed.'
            return False, msg

        for i in range(len(cs_lst)):

            if (cs_lst[i][1] != 'moms') and (cs_lst[i][1] != 'dims'):
                msg = 'Cross-section descriptor must be "moms" or "dims".'
                return False, msg

            if (cs_lst[i][1] == 'moms') and len(cs_lst[i][0]) != 4:
                msg = 'Cross-section defined on moments of inertia must have four inputs:' \
                      ' cross-sectional area, moment of inertia in the vertical axes, in the horizontal' \
                      ' axes, and polar moment of inertia.'
                return False, msg

            if (cs_lst[i][1] == 'dims') and len(cs_lst[i][0]) != 2:
                msg = 'Cross-section defined on dimensions must have two inputs:' \
                      ' vertical and horizontal lengths.'
                return False, msg

            for j in range(len(cs_lst[i][0])):
                warn, msg = type_warning(cs_lst[i][0][j], 'cross-sectional dimensions', (float, int))
                if not warn:
                    return False, msg

        return True

    @bcs.validator
    def bcs(self, bcs_lst):
        """
        Verifies that the boundary condition input is correctly implemented: no repetition, limits, naming
        scheme, etc.
        :param bcs_lst:
        :return:
        """
        if len(bcs_lst) != 3:
            msg = 'The number of boundary condition descriptions cannot be changed.'
            return False, msg

        for i in range(3):
            warn, msg = type_warning(bcs_lst[i][1], 'constricted DOFs', str)
            if not warn:
                return False, msg

            if bcs_lst[i][0] != ['root_rib', 'front_spar', 'rear_spar'][i]:
                msg = 'Boundary condition descriptors cannot be changed.'
                return False, msg

            decompose = [*bcs_lst[i][1]]

            if len(decompose) != len(set(decompose)):
                msg = 'DOF indexes cannot be repeated'
                return False, msg

            for j in range(len(decompose)):
                if decompose[j] not in ['1', '2', '3', '4', '5', '6']:
                    msg = 'DOF index must be comprised between 1 and 6.'
                    return False, msg
                if j > 0 and (decompose[j] < decompose[j-1]):
                    msg = 'DOF indexes must be ordered in ascending order.'
                    return False, msg

        return True

    # CHILDREN GENERATION

    @Part
    def wing_geom(self):
        """
        Creates the geometry of the wing
        :return: WingGeom
        """
        return WingGeom(pass_down=['root_chord', 'spans', 'tapers',
                                   'sweeps', 'dihedrals', 'twist',
                                   'airfoil_sections', 'airfoil_names',
                                   'n_sections', 'n_airfoils'])

    @Part
    def analysis(self):
        """
        Creates the setup for AVL analysis
        :return: AvlAnalysis
        """
        return AvlAnalysis(wing=self.wing_geom,
                           pass_down=['case_settings', 'weight', 'speed', 'height, n_loads'])

    @Part
    def wingbox(self):
        """
        Creates the wingbox structure
            :return: WingBox
        """
        return WingBox(wing=self.wing_geom,
                       pass_down=['rib_idx', 'front_spar_loc', 'rear_spar_loc', 'stringer_idx',
                                  'TE_ribs_gap', 'TE_skin_gap', 'n_sections'])

    @Part
    def FEMFile(self):
        """ Creates the complete NASTRAN file that must be run independently. """
        return FEMFileGenerator(wing=self.wingbox,
                                analysis=self.analysis,
                                quad_dominance=self.quad_dominance,
                                min_elem_size=self.min_elem_size,
                                max_elem_size=self.max_elem_size,
                                bcs=self.bcs)

    @Attribute
    def FEMAnalysis(self):
        """ Defines the .bdf file, run it using NASTRAN and sort output data. """

        # Writing .bdf file.
        file_name = r'\wingbox_bulkdata.bdf'
        local_file_path = self.bdf_file_folder + file_name
        base_file = self.FEMFile.FEMWriter.write(local_file_path)
        global_file_path = os.path.join(os.path.dirname(__file__), r'bdf_files\wingbox_bulkdata.bdf')

        # Adding subcases to the .bdf file.
        case_settings = self.analysis.case_settings[2]
        bdf_file_cases(global_file_path, case_settings)

        # Running NASTRAN.
        nastran_command = '"' + self.nastran_path + '" "' + global_file_path + '"'
        try:
            subprocess.run(nastran_command, check=True)
            print(f"Input file successfully processed by NASTRAN. Wait for the software to run the FEM analysis.")
        except subprocess.CalledProcessError as e:
            print(f"Error running NASTRAN: {e}")

        while check_nastran_running():
            time.sleep(5)  # Wait for 1 second before checking again

        # Define source paths for NASTRAN files.
        source_files = {
            'f04': 'wingbox_bulkdata.f04',
            'f06': 'wingbox_bulkdata.f06',
            'log': 'wingbox_bulkdata.log'
        }

        # Define destination directories for NASTRAN files
        bdf_files_path = os.path.join(os.path.dirname(__file__), 'bdf_files')
        output_data_path = os.path.join(os.path.dirname(__file__), 'output_data')

        # Copying NASTRAN files to respective directories.
        for file_key, file_name in source_files.items():
            source_file_path = os.path.join(os.getcwd(), file_name)

            if file_key == 'f06':
                shutil.copy2(source_file_path, os.path.join(bdf_files_path, os.path.basename(source_file_path)))
                shutil.copy2(source_file_path, os.path.join(output_data_path, os.path.basename(source_file_path)))
            else:
                dest_file_path = os.path.join(bdf_files_path, os.path.basename(source_file_path))
                shutil.copy2(source_file_path, dest_file_path)

            os.remove(source_file_path)

        # Creating STEP file of the geometry in the folder.
        self.wingbox.STEP_file.write(os.path.join(output_data_path, 'wingbox_STEP.stp'))

        # Getting plots and reactions, and saving in the appropriate output folder.
        load_cases = self.FEMFile.cases
        get_plots_reacts(load_cases)

        print(f"FEM Analysis has finished running. Check output in the 'output_data' folder.")

        return None


if __name__ == '__main__':
    from parapy.gui import display
    display(WingBoxAssessment())
