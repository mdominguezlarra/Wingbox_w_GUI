from parapy.core import *
from parapy.geom import *
from parapy.mesh import *
from parapy.lib.nastran import *

class FEMFileGenerator(Base):


    @Input
    def material_properties(self):

        # CONVERSION FROM IMPERIAL TO SI. THICKNESSES AND MECHANICAL PROPERTIES.

        return 1

