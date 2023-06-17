from parapy.core import *
from kbeutils import avl


class AvlAnalysis(avl.Interface):

    wing = Input(in_tree=True)

    @Attribute
    def configuration(self):
        return self.wing.avl_configuration

    case_settings = Input()

    @Part
    def cases(self):
        return avl.Case(quantify=len(self.case_settings),
                        name=self.case_settings[child.index][0],
                        settings=self.case_settings[child.index][1])
