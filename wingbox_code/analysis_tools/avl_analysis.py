from parapy.core import *
from kbeutils import avl
from .avl_tools.flight_condition import FlightCondition


class AvlAnalysis(avl.Interface):

    wing = Input()
    case_settings = Input()
    weight = Input()
    speed = Input()
    height = Input()

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
                                 reference_point=self.wing.position.point,  # use quarter chord MAC?
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
        return avl.SectionFromCurve(quantify=len(self.wing.profile_order[0]),            # It looks weird on the display
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

