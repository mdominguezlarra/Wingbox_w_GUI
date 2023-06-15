from parapy.core import *
from parapy.geom import *
import cst
import numpy as np
from kbeutils.geom.curve import Naca4AirfoilCurve, Naca5AirfoilCurve


class CurveDraw(GeomBase):

    airfoil_name = Input('23014')

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

        if (self.airfoil_name.isnumeric()
                and (len(self.airfoil_name) == 5 or
                     len(self.airfoil_name) == 4)):

            x_lst = [1.1]
            y_lst = []
            i = 1

            for j in self.naca_airfoil.points:
                if j.x >= 0:
                    x_lst.append(j.x)
                    y_lst.append(j.z)
                    if x_lst[-1] < x_lst[-2]:
                        i = i+1

            x_lst = x_lst[1:]

        else:

            i = int(len(self.pts[1])/2-0.5)
            x_lst = self.pts[1]
            y_lst = self.pts[2]

        coeff_u = list(cst.fit(x_lst[0:i],
                               y_lst[0:i],
                               8)[0])

        coeff_l = list(cst.fit(x_lst[i:-1],
                               y_lst[i:-1],
                               8)[0])
        return coeff_u, coeff_l

    @Part
    def naca_airfoil(self):
        return DynamicType(type=Naca5AirfoilCurve if len(self.airfoil_name) == 5
        else Naca4AirfoilCurve,
                           designation=self.airfoil_name,
                           mesh_deflection=0.00001,
                           hidden=True)

    @Part
    def non_naca(self):
        return FittedCurve(points=self.pts[0],
                           hidden=True)

    @Part
    def foil_curve(self):
        return ScaledCurve(curve_in=self.naca_airfoil if (self.airfoil_name.isnumeric() and
                                                          (len(self.airfoil_name) == 5 or
                                                          len(self.airfoil_name) == 4)) else self.non_naca,
                           reference_point=self.position.point,
                           factor=1,
                           mesh_deflection=0.00001)


if __name__ == '__main__':
    from parapy.gui import display
    eyo = '12312'
    print(eyo.isnumeric() and (len(eyo) == 5 or len(eyo) == 4))
    display(CurveDraw(airfoil_name=eyo))

