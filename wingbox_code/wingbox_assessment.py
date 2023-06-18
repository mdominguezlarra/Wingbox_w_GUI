from parapy.core import *
from parapy.geom import *
from parapy.core.validate import *
from .geometry.geometry_tools.winggeom import WingGeom
from .geometry.wingbox import WingBox
from .analysis_tools.avl_analysis import AvlAnalysis
from .analysis_tools.get_forces import GetForces
from .analysis_tools.femfilegenerator import FEMFileGenerator
import csv


def type_warning(value, label, type_i):
    """
    Checks the type of the input and creates a warning if such a type is wrong
    :param value: input in question
    :param label: label for the input
    :param type_i: required type(s)
    :return:
    """
    if not isinstance(value, type_i):
        # error message
        msg = 'Wrong input type for {}, correct type is {}'.format(label, type_i)
        return False, msg

    return True, None


def material_validation():

    # List initialization
    names = []
    temper = []
    basis = []
    partial_name = []
    thicknesses = []

    # Finding the correct mechanical properties.
    path = 'wingbox_code/input_data/materials.csv'
    with open(path, 'r', newline='') as file:
        mat_file = csv.reader(file)

        for idx, row in enumerate(mat_file):
            if idx != 0:
                names.append(row[1])
                temper.append(row[2])
                basis.append(row[5])

                row_str = row[1] + '-' + row[2] + '-' + row[5]
                partial_name.append(row_str)

                t_lims = [float(row[3]), float(row[4])]
                thicknesses.append(t_lims)

    return names, temper, basis, partial_name, thicknesses


class WingBoxAssessment(GeomBase):

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
    TE_ribs_gap = Input(validator=Range(0, 1))  # Must be after the rearmost rear_spar_loc but less than 1
    TE_skin_gap = Input(validator=Range(0, 1))  # Must be after the rearmost rear_spar_loc but less than 1

    # FEM MODEL INPUTS
    # AERODYNAMIC LOADS ARE AUTOMATICALLY CALCULATED USING GET_FORCES.
    # File path for .bdf file.
    bdf_file_path = Input('wingbox_code/bdf_files/wingbox_bulkdata.bdf')
    quad_dominance = Input(False)
    min_elem_size = Input(1)
    max_elem_size = Input(10)

    # Material definitions. Strings combination of 'alloy-temper-thickness-basis'. Thickness in mm.
    mat_2D = Input(validator=IsInstance(list))  # RIBS
    mat_1D = Input(validator=IsInstance(list))  # RIB CAPS

    tc_select = Input('t', validator=IsInstance(str))  # TENSION OR COMPRESSION SELECTOR

    # Cross-sections properties. Inputs are either dimensions of a rectangle, or mechanical properties.
    # e.g. 'dims': [horizontal, vertical] # in mm
    secs = Input([[[1, 1], 'dims'],  # STRINGERS
                  [[1, 1], 'dims'],  # SPAR CAPS
                  [[1, 0.0833, 0.0833, 2.2533], 'moms']])  # RIB CAPS
    # e.g. 'moms': [area,  I1,     I2,      J]

    # BCs
    bcs = Input()

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

        name_database = ['B29_root', 'rae5215',	'B707_root', 'B29_tip',	'rae5212',
                         'B707_tip', 'SC2-0714', 'rae2822', 'B707_54c']

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

            if rs_locs[i] <= self.front_spar_loc[i]:
                msg = 'The rear spar cannot be further front than the front spar'
                return False, msg

        return True

    @stringer_idx.validator
    def stringer_idx(self, stringers):

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

        for i in range(self.n_sections + 1):
            if value < self.rear_spar_loc[i]:
                msg = 'The skin cut location cannot be located further front than the aft spar.'
                return False, msg

        return True

    @TE_ribs_gap.validator
    def TE_ribs_gap(self, value):

        for i in range(self.n_sections + 1):
            if value < self.rear_spar_loc[i]:
                msg = 'The rib cut location cannot be located further front than the aft spar.'
                return False, msg

        return True

    @mat_1D.validator
    def mat_1D(self, materials):

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

    # CHILDREN GENERATION

    @Part
    def wing_geom(self):
        return WingGeom(pass_down=['root_chord', 'spans', 'tapers',
                                   'sweeps', 'dihedrals', 'twist',
                                   'airfoil_sections', 'airfoil_names'])

    @Part
    def analysis(self):
        return AvlAnalysis(wing=self.wing_geom,
                           pass_down=['case_settings', 'weight', 'speed', 'height'])

    @Part
    def wingbox(self):
        return WingBox(wing=self.wing_geom,
                       pass_down=['rib_idx', 'front_spar_loc', 'rear_spar_loc', 'stringer_idx',
                                  'TE_ribs_gap', 'TE_skin_gap'])

    @Part
    def get_forces(self):
        return GetForces(quantify=len(self.case_settings[2]),
                         input_case=self.analysis,
                         num_case=child.index + 1,
                         flight_cond=self.analysis.flight_cond)

    @Part
    def FEMFile(self):
        return FEMFileGenerator(wing=self.wingbox,
                                quad_dominance=self.quad_dominance,
                                min_elem_size=self.min_elem_size,
                                max_elem_size=self.max_elem_size)

    @Attribute
    def FEMWrite(self):
        return self.FEMFile.FEMwriter.write(self.bdf_file_path)


if __name__ == '__main__':
    from parapy.gui import display
    display(WingBoxAssessment())
