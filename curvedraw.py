from parapy.core import *
from parapy.geom import *
import cst
import numpy as np


class CurveDraw(GeomBase):
    # The KBEutils could be used for an alternative way to produce airfoils

    airfoil_name = Input('NACA23012')

    @Attribute
    def pts(self):
        """ Extract airfoil coordinates from a data file and create a list of 3D points.
        This function is based on the example of Ex.17 from tutorial 5"""

        # A warning of "airfoil not found" could be used here?/wrong order/format
        # SELIG FORMAT AIRFOILS NEED TO BE USED
        name = 'airfoils/' + self.airfoil_name + '.dat'
        file = np.loadtxt(name)
        points = []
        x_lst = []
        y_lst = []
        for line in file:
            x, y = line[0], line[1]
            points.append(Point(float(x), 0, float(y)))
            x_lst.append(x)
            y_lst.append(y)

        return points, x_lst, y_lst

    @Attribute
    def cst(self):

        i = int(len(self.pts[1])/2-0.5)

        coeff_u = cst.fit(self.pts[1][0:i],
                          self.pts[2][0:i],
                          5)

        coeff_l = cst.fit(self.pts[1][i:-1],
                          self.pts[2][i:-1],
                          5)
        return coeff_u, coeff_l

    @Part
    def foil_curve(self):
        return FittedCurve(points=self.pts[0])


if __name__ == '__main__':
    from parapy.gui import display
    display(CurveDraw())
