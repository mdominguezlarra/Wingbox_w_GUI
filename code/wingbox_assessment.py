from parapy.core import *
from parapy.geom import *
from kbeutils import avl
from .geometry.geometry_tools.winggeom import WingGeom
from .geometry.wingbox import WingBox
from .analysis_tools.flight_cond import FlightCondition
from .analysis_tools.avl_analysis import AvlAnalysis
from .analysis_tools.get_forces import GetForces
from .analysis_tools.femfilegenerator import FEMFileGenerator


class WingBoxAssessment(GeomBase):
    # ALL INPUTS ARE ESTABLISHED HERE
    # INPUTS MUST BE ON SI UNITS, UNLESS STATED OTHERWISE IN COMMENTS.
    # AIRCRAFT GENERAL INPUTS
    weight = Input(5000)  # kg.
    speed = Input(80)  # m/s.
    height = Input(1000)  # ft.

    # LOAD CASES
    case_settings = Input([('fixed_aoa', {'alpha': 3}),
                           ('fixed_cl', {'alpha': avl.Parameter(name='alpha',
                                                                value=0.3,
                                                                setting='CL')})])

    # WING GEOMETRY
    # For 1st section
    root_chord = Input(7)  # m.

    # For the rest (I have a doubt, how will we solve if the number of inputs is not coherent??)
    spans = Input([0, 8, 13, 20])  # m. wrt the root position
    tapers = Input([1, 0.6, 0.35, 0.2])  # -. wrt the root chord. Extra element for root chord
    sweeps = Input([30, 40, 50])  # deg. wrt the horizontal
    dihedrals = Input([3, 5, 10])  # deg. wrt the horizontal
    twist = Input([2, 0, -1, -3])  # def. wrt the horizontal (this includes the initial INCIDENCE!!)

    # Airfoils
    airfoil_sections = Input([0, 0.3, 0.7, 1])  # percentage wrt to root.
    airfoil_names = Input([
        'rae5212',
        'rae5212',
        'rae5212',
        'rae5212'
    ])

    # STRUCTURAL DETAILS
    # Ribs
    rib_idx = Input([7, 5, 3])

    # Spars
    front_spar_loc = Input([0.25, 0.25, 0.25, 0.25])
    rear_spar_loc = Input([0.75, 0.75, 0.75, 0.75])

    # Stringers
    stringer_idx = Input([[7, 5],
                          [5, 3],
                          [3, 2]])

    # Trailing edge gaps for skin and ribs
    TE_ribs_gap = Input(0.8)  # Must be after the rearmost rear_spar_loc but less than 1
    TE_skin_gap = Input(0.85)  # Must be after the rearmost rear_spar_loc but less than 1

    # FEM MODEL INPUTS
    # AERODYNAMIC LOADS ARE AUTOMATICALLY CALCULATED USING GET_FORCES.
    # Number of elements
    num_elem_FEM = Input()

    # Material definitions. Strings combination of 'alloy-temper-thickness-basis'. Thickness in mm.
    mat_2D = Input([
        'Al2024-T3-1.27-A',   # SKIN
        'Al2024-T3-1.27-A',   # SPAR WEB
        'Al2024-T3-1.27-A'])  # RIBS
    mat_1D = Input([
        'Al7475-T61-1.524-S',  # STRINGERS
        'Al7475-T61-1.524-S',  # SPAR CAPS
        'Al7475-T61-1.524-S'])  # RIB CAPS

    # Stringers cross-sections
    str_cs = Input()

    # BCs
    bcs = Input()

    @Part
    def wing_geom(self):
        return WingGeom(pass_down=['root_chord', 'spans', 'tapers',
                                   'sweeps', 'dihedrals', 'twist',
                                   'airfoil_sections', 'airfoil_names'])

    @Part
    def flight_cond(self):
        return FlightCondition(pass_down=['weight', 'speed', 'height'])

    @Part
    def avl_configuration(self):
        return avl.Configuration(name='wing',
                                 reference_area=self.wing_geom.planform_area,
                                 reference_span=self.wing_geom.spans[-1] * 2,
                                 reference_chord=self.wing_geom.mac,
                                 reference_point=self.position.point,  # use quarter chord MAC?
                                 surfaces=[self.wing_geom.avl_surface],
                                 mach=self.flight_cond.atmos_calc[9])

    @Part
    def analysis(self):
        return AvlAnalysis(wing=self,
                           case_settings=self.case_settings)

    # THIS IS THE WINGBOX ASSEMBLY, ALL COMPONENTS SHOULD GO INSIDE IT
    # ADD INPUTS AS THEY BECOME NECESSARY
    @Part
    def wingbox(self):
        return WingBox(wing=self.wing_geom,
                       pass_down=['rib_idx', 'front_spar_loc', 'rear_spar_loc', 'stringer_idx',
                                  'TE_ribs_gap', 'TE_skin_gap'])

    @Part
    def get_forces(self):
        return GetForces(quantify=len(self.case_settings[0]),
                         input_case=self.analysis,
                         num_case=child.index + 1,
                         flight_cond=self.flight_cond)

    @Part
    def FEMFile(self):
        return FEMFileGenerator(wing=self.wingbox)


if __name__ == '__main__':
    from parapy.gui import display

    display(WingBoxAssessment())
