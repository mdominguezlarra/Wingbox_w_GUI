from parapy.core import *
from parapy.geom import *
from winggeom import WingGeom
from wingbox import WingBox
from flight_cond import FlightCondition
from avl_analysis import AvlAnalysis
from kbeutils import avl


class Wing(GeomBase):

    # ALL INPUTS ARE ESTABLISHED HERE

    # AIRCRAFT GENERAL INPUTS
    weight = Input(5000)    # kg.
    speed = Input(80)       # m/s.
    height = Input(1000)    # ft.

    # LOAD CASES
    case_settings = Input([('fixed_aoa', {'alpha': 3}),
                          ('fixed_cl', {'alpha': avl.Parameter(name='alpha',
                                                               value=0.3,
                                                               setting='CL')})])

    # WING GEOMETRY
    # For 1st section
    root_chord = Input(7)

    # For the rest (I have a doubt, how will we solve if the number of inputs is not coherent??)
    spans = Input([0, 8, 13, 16])  # m. wrt the root position
    tapers = Input([1, 0.6, 0.35, 0.2])  # -. wrt the root chord. Extra element for root chord
    sweeps = Input([30, 40, 50])  # deg. wrt the horizontal
    dihedrals = Input([3, 5, 10])  # deg. wrt the horizontal
    twist = Input([2, 0, -1, -3])  # def. wrt the horizontal (this includes the initial INCIDENCE!!)

    # Airfoils
    airfoil_sections = Input([0, 0.3, 0.7, 1])
    airfoil_names = Input([
        'rae5212',
        'rae5212',
        'rae5215',
        'rae5215'
    ])

    # STRUCTURAL DETAILS
    # Ribs
    rib_pitch = Input(1)
    rib_thickness = Input(3)                # mm

    @Part
    def wing_geom(self):
        return WingGeom(pass_down=['root_chord', 'spans', 'tapers',
                                   'sweeps', 'dihedrals', 'twist',
                                   'airfoil_sections', 'airfoil_names'])

    @Part
    def flight_con(self):
        return FlightCondition(pass_down=['weight', 'speed', 'height'])

    @Part
    def avl_configuration(self):
        return avl.Configuration(name='wing',
                                 reference_area=self.wing_geom.planform_area,
                                 reference_span=self.wing_geom.spans[-1]*2,
                                 reference_chord=self.wing_geom.mac,
                                 reference_point=self.position.point,          # use quarter chord MAC?
                                 surfaces=[self.wing_geom.avl_surface],
                                 mach=self.flight_con.atmos_calc[9])

    @Part
    def analysis(self):
        return AvlAnalysis(wing=self,
                           case_settings=self.case_settings)

    # THIS IS THE WINGBOX ASSEMBLY, ALL COMPONENTS SHOULD GO INSIDE IT
    # ADD INPUTS AS THEY BECOME NECESSARY
    @Part
    def wingbox(self):
        return WingBox(wing=self.wing_geom,
                       rib_pitch=self.rib_pitch,
                       rib_thickness=self.rib_thickness)


if __name__ == '__main__':
    from parapy.gui import display
    display(Wing())
