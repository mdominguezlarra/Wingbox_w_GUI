from parapy.core import *
from kbeutils import avl
from parapy.core.validate import *
from .avl_tools.flight_condition import FlightCondition
from ..format.tk_warn import type_warning


class AvlAnalysis(avl.Interface):

    wing = Input()
    n_loads = Input(validator=And(Positive(), IsInstance(int)))
    case_settings = Input(validator=IsInstance(list))
    weight = Input(validator=And(Positive(), IsInstance((int, float))))  # kg.
    speed = Input(validator=And(Positive(), IsInstance((int, float))))  # m/s.
    height = Input(validator=IsInstance((int, float)))  # ft.

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

    @Attribute
    def case_input(self):

        case_input = []
        cases = self.case_settings

        for i in range(len(cases[2])):

            if cases[1][i] == 'alpha':
                case_input.append((cases[0][i], {'alpha': cases[2][i]}))

            elif cases[1][i] == 'CL':
                case_input.append((cases[0][i], {'alpha': avl.Parameter(name='alpha',
                                                                        value=cases[2][i],
                                                                        setting=cases[1][i])}))
            else:
                print('Wrong alphabetic inputs! Create warning')

        return case_input

    @Attribute
    def configuration(self):
        return avl.Configuration(name='wing',
                                 reference_area=self.wing.planform_area,
                                 reference_span=self.wing.spans[-1] * 2,
                                 reference_chord=self.wing.mac,
                                 reference_point=self.wing.position.point,
                                 surfaces=[self.avl_surface],
                                 mach=self.flight_cond.atmos_calc[9])

    @Attribute
    def flight_cond(self):
        return FlightCondition(weight=self.weight,
                               speed=self.speed,
                               height=self.height)

    @Part
    def cases(self):
        return avl.Case(quantify=len(self.case_input),
                        name=self.case_input[child.index][0],
                        settings=self.case_input[child.index][1])

    @Part
    def avl_sections(self):
        return avl.SectionFromCurve(quantify=len(self.wing.profile_order[0]),
                                    curve_in=self.wing.profile_order[0][child.index])

    @Part
    def avl_surface(self):
        return avl.Surface(name='Wing',
                           n_chordwise=12,
                           chord_spacing=avl.Spacing.cosine,
                           n_spanwise=20,
                           span_spacing=avl.Spacing.cosine,
                           y_duplicate=self.wing.position.point[1],  # Always mirrored. self.is_mirrored does not appear
                           sections=self.avl_sections)               # curvature: self.avl_sections);
                                                                     # flat: sections=self.profile_order[1])

