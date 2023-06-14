from parapy.core import *
from parapy.geom import *
from parapy.geom.occ import SewnShell

from wingsec import WingSec
from airfoil import Airfoil
from curvedraw import CurveDraw
import numpy as np
import cst
from kbeutils import avl


def intersection_airfoil(span_distribution, airfoil_distribution):
    frac_span = np.array(span_distribution) / span_distribution[-1]

    diff = np.ones((len(span_distribution), len(airfoil_distribution)))
    inter = np.ones((len(span_distribution), len(airfoil_distribution)+1))

    p = 0
    idx = []
    span_sec = []
    secs = []
    for i in range(len(frac_span)):
        diff[i] = np.ones((1, len(airfoil_distribution))) * frac_span[i] - airfoil_distribution
        if 0 not in diff[i]:
            inter[p, :-1] = diff[i]
            inter[p, -1] = 0
            sorted_indices = np.argsort(inter[p])
            pos = np.where(sorted_indices == len(airfoil_distribution))[0][0]
            idx.append([sorted_indices[pos-1], sorted_indices[pos+1]])
            span_sec.append(frac_span[i])
            secs.append(i-1)
            p = p + 1

    inter = inter[:p, :-1]
    return inter, idx, p, span_sec, secs


class WingGeom(GeomBase):

    # All of the following inputs should be read from a file
    # For 1st section
    root_chord = Input(7)

    # For the rest (I have a doubt, how will we solve if the number of inputs is not coherent??)
    spans = Input([0, 8, 13, 16])           # m. wrt the root position
    tapers = Input([1, 0.6, 0.35, 0.2])     # -. wrt the root chord. Extra element for root chord
    sweeps = Input([30, 40, 50])            # deg. wrt the horizontal
    dihedrals = Input([3, 5, 10])            # deg. wrt the horizontal
    twist = Input([2, 0, -1, -3])           # def. wrt the horizontal (this includes the initial INCIDENCE!!)

    # Airfoils
    airfoil_sections = Input([0, 0.3, 0.7, 1])
    airfoil_names = Input([
        'rae5212',
        '23014',
        '22013',
        'rae5215'
    ])

    @Attribute
    def planform_area(self):

        s = 0
        for i in range(len(self.spans)-1):
            cr = self.root_chord*self.tapers[i]
            tap = self.tapers[i+1]/self.tapers[i]
            b = self.spans[i+1] - self.spans[i]
            s = s + cr*(1+tap)*b

        return s

    @Attribute
    def mac(self):

        s = self.planform_area
        c_int = 0
        for i in range(len(self.spans)-1):
            cr = self.root_chord*self.tapers[i]
            tap = self.tapers[i+1]/self.tapers[i]
            b = self.spans[i+1] - self.spans[i]
            c_int = c_int + b/3*cr**2*(tap**2 + tap + 1)

        mac = 2/s*c_int
        return mac

    # @Attribute
    # def c_4mac(self):
    #
    #     mac_ = self.mac/self.root_chord
    #     for i in range(len(frac_span)):
    #         diff[i] = abs(np.ones((1, len(frac_span))) * frac_span[i] - airfoil_distribution)
    #
    #     return c_4mac

    @Attribute
    def airfoil_guides(self):
        edges = []
        for j in range(len(self.spans)-1):
            for i in range(len(self.airfoil_sections)):
                edg = IntersectedShapes(
                    shape_in=self.airfoil_planes[i],
                    tool=self.wiresec[j].sec_plane)
                edges.append(edg.edges)

        edges = list(filter(None, edges))
        edges_clean = []

        for i in range(len(edges)):
            if edges[i][0].start.x != edges[i-1][0].start.x:
                edges_clean.append(edges[i])

        return edges_clean

    @Attribute
    def airfoil_interp(self):
        coeff_u = np.zeros((len(self.airfoil_sections), 8))
        coeff_l = np.zeros((len(self.airfoil_sections), 8))
        for i in range(len(self.airfoil_sections)):
            coeff_u[i] = self.airfoil_unscaled[i].cst[0]
            coeff_l[i] = self.airfoil_unscaled[i].cst[1]

        inter, idx, p, s_span, secs = intersection_airfoil(self.spans, self.airfoil_sections)

        # Linear interpolation
        airfoils = []
        for i in range(p):
            d_1 = -inter[i, idx[i][0]]
            d_2 = inter[i, idx[i][1]]
            d_t = d_1 + d_2

            cst_u = d_1/d_t * coeff_u[idx[i][0], :] + d_2/d_t * coeff_u[idx[i][1], :]
            cst_l = d_1/d_t * coeff_l[idx[i][0], :] + d_2/d_t * coeff_l[idx[i][1], :]

            x_i = np.linspace(0, 1, 40)
            y_u = cst.cst(x_i, cst_u)
            y_l = cst.cst(x_i, cst_l)

            x = np.concatenate((np.flip(x_i), x_i))
            y = np.concatenate((np.flip(y_l), y_u))

            points = []
            for j in range(len(x)):
                points.append(Point(x[j], 0, y[j]))

            airfoils.append(points)

        return airfoils, secs

    @Attribute
    def profile_order(self):
        inter, idx, p, s_span, secs = intersection_airfoil(self.spans, self.airfoil_sections)
        stations = self.airfoil_sections + s_span
        sorted_indices = sorted(range(len(stations)), key=lambda k: stations[k])

        airfoils = []
        guides = []
        for i in range(len(self.airfoils)):
            airfoils.append(self.airfoils[i])
            guides.append(self.airfoil_chords[i])
        for i in range(len(self.inter_airfoils)):
            airfoils.append(self.inter_airfoils[i])
            guides.append(self.wiresec[i].sec_chords_out)

        unscaled_order = []
        scaled_order = []
        guides_order = []
        for i in range(len(airfoils)):
            unscaled_order.append(airfoils[sorted_indices[i]])
            scaled_order.append(airfoils[sorted_indices[i]].scaled_foil)
            guides_order.append(guides[sorted_indices[i]])

        return scaled_order, guides_order, unscaled_order

    @Part
    def wiresec(self):
        return WingSec(quantify=len(self.spans)-1,        # this is how the quantity is determined
                       span=self.spans[child.index+1]-self.spans[child.index],
                       root_chord=self.root_chord*self.tapers[child.index],
                       taper=self.tapers[child.index+1]/self.tapers[child.index],
                       map_down=['sweeps->sweep', 'dihedrals->dihedral'],
                       incidence=self.twist[child.index],
                       twist=self.twist[child.index+1],
                       position=self.position if child.index == 0 else
                       child.previous.nextorigin()
                       )

    @Part
    def airfoil_planes(self):
        return RectangularSurface(
            quantify=len(self.airfoil_sections),
            width=100*self.root_chord,
            length=100*self.root_chord,
            position=translate(rotate90(self.position, 'x'),
                               'z',
                               -self.spans[-1]*self.airfoil_sections[child.index]),
            hidden=True)

    @Part
    def airfoil_chords(self):
        return ComposedCurve(quantify=len(self.airfoil_guides),
                             built_from=self.airfoil_guides[child.index],
                             line_thickness=2)

    @Part
    def airfoil_unscaled(self):
        return CurveDraw(quantify=len(self.airfoil_sections),
                         airfoil_name=self.airfoil_names[child.index],
                         hidden=False)

    @Part
    def airfoil_interp_unscaled(self):
        return FittedCurve(quantify=len(self.airfoil_interp[1]),
                           points=self.airfoil_interp[0][child.index],
                           hidden=False)

    @Part
    def airfoils(self):
        return Airfoil(quantify=len(self.airfoil_sections),
                       airfoil_curve=self.airfoil_unscaled[child.index].foil_curve,
                       airfoil_start=self.airfoil_chords[child.index].start,
                       airfoil_direction=self.airfoil_chords[child.index].direction_vector,
                       airfoil_chord=self.airfoil_chords[child.index].length)

    @Part
    def inter_airfoils(self):
        return Airfoil(quantify=len(self.airfoil_interp[1]),
                       airfoil_curve=self.airfoil_interp_unscaled[child.index],
                       airfoil_start=self.wiresec[self.airfoil_interp[1][child.index]].sec_chords_out.start.location,
                       airfoil_direction=self.wiresec[self.airfoil_interp[1][child.index]].sec_chords_out.direction_vector,
                       airfoil_chord=self.wiresec[self.airfoil_interp[1][child.index]].sec_chords_out.length)

    @Part
    def surf_section(self):
        return LoftedShell(quantify=len(self.profile_order[0])-1,
                           profiles=self.profile_order[0][child.index:child.index+2],
                           mesh_deflection=1e-4,
                           hidden=False)

    @Part
    def right_wing(self):
        return SewnShell(self.surf_section,
                         mesh_deflection=1e-4,)

    @Part
    def left_wing(self):
        return MirroredShape(shape_in=self.right_wing,
                             reference_point=XOY,
                             vector1=Vector(1, 0, 0),
                             vector2=Vector(0, 0, 1),
                             mesh_deflection=1e-4,)

    @Part
    def avl_sections(self):
        return avl.SectionFromCurve(quantify=len(self.profile_order[0]),            # It looks weird on the display
                                    curve_in=self.profile_order[0][child.index])

    @Part
    def avl_surface(self):
        return avl.Surface(name='Wing',
                           n_chordwise=12,
                           chord_spacing=avl.Spacing.cosine,
                           n_spanwise=20,
                           span_spacing=avl.Spacing.cosine,
                           y_duplicate=self.position.point[1],  # Always mirrored. self.is_mirrored does not appear
                           sections=self.avl_sections)          # curvature: self.avl_sections);
                                                                # flat: sections=self.profile_order[1])

    # TESTS: ERASE WHEN DONE

    @Part
    def test(self):
        return SplitCurve(curve_in=self.airfoils[0].scaled_foil,
                          tool=[0.25, 0.5, 0.75],
                          mesh_deflection=1e-4)

    @Part
    def test2(self):
        return Wire(quantify=len(self.test.curves_in),
                    curves_in=[self.test.curves_in[child.index]])




if __name__ == '__main__':
    from parapy.gui import display
    display(WingGeom())
