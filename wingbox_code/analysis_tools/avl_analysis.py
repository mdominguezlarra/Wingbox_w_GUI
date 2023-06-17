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
                                 surfaces=[self.wing.avl_surface],
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

