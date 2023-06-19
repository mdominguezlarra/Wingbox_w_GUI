from parapy.core import *
from parapy.geom import *
from parapy.geom.occ import SewnShell
from parapy.core.validate import *
from ...format.tk_warn import type_warning
from .wingsec import WingSec
from .airfoil import Airfoil
from .curvedraw import CurveDraw
import numpy as np
import cst
import os
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
    # WING GEOMETRY
    # For 1st section
    root_chord = Input(validator=And(Positive(), IsInstance((int, float))))  # m.

    # Following sections
    n_sections = Input(validator=And(Positive(), IsInstance(int)))
    spans = Input(validator=IsInstance(list))
    tapers = Input(validator=IsInstance(list))
    sweeps = Input(validator=IsInstance(list))
    dihedrals = Input(validator=IsInstance(list))
    twist = Input(validator=IsInstance(list))

    # Airfoils
    n_airfoils = Input(validator=And(Positive(), IsInstance(int)))
    airfoil_sections = Input(validator=IsInstance(list))  # percentage wrt to root.
    airfoil_names = Input(validator=IsInstance(list))

    # SPECIAL VALIDATORS #

    @spans.validator
    def spans(self, span):
        """
        Validates whether the span inputs are positive, in ascending order, and not defined at the same position,
        as well as correct type and number of inputs
        :param span:
        :return: bool
        """
        if len(span) != self.n_sections + 1:
            msg = 'The number of section spans must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        if 0 not in span:
            msg = 'The "0" span station must be kept unchanged'
            return False, msg

        for i in range(1, len(span[1:])):
            warn, msg = type_warning(span[i], 'span', (int, float))
            if not warn:
                return False, msg

            if span[i] <= 0:
                msg = 'The section spans cannot be negative or equal to zero. Change section {}'.format(i)
                return False, msg
            if span[i] == span[i - 1]:
                msg = 'Two sections cannot be defined at the same span length. Change section {}'.format(i)
                return False, msg
            if span[i] < span[i - 1]:
                msg = 'The sections must be organized in ascending order. Change section {}'.format(i)
                return False, msg

        return True

    @tapers.validator
    def tapers(self, taper):
        """
        Validates if the taper inputs are positive, and the correct type
        :param taper:
        :return: bool
        """
        if len(taper) != self.n_sections + 1:
            msg = 'The number of section tapers must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(taper)):
            warn, msg = type_warning(taper[i], 'taper', (int, float))
            if not warn:
                return False, msg

            if taper[i] <= 0:
                msg = 'The section taper cannot be negative or equal to zero. Change section {}'.format(i)
                return False, msg

        return True

    @sweeps.validator
    def sweeps(self, sweep):
        """
        Validates if the sweep inputs are within range, and the correct type
        :param sweep:
        :return:
        """
        if len(sweep) != self.n_sections:
            msg = 'The number of section sweeps must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(sweep)):
            warn, msg = type_warning(sweep[i], 'sweep', (int, float))
            if not warn:
                return False, msg

            if sweep[i] < -85 or sweep[i] > 85:
                msg = 'The sweep value must be kept in the range [-85, 85] degrees. Change section {}'.format(i)
                return False, msg

        return True

    @dihedrals.validator
    def dihedrals(self, dihedral):
        """
        Validates if the dihedral inputs are within range, and the correct type
        :param dihedral:
        :return:
        """
        if len(dihedral) != self.n_sections:
            msg = 'The number of section dihedrals must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(dihedral)):
            warn, msg = type_warning(dihedral[i], 'dihedral', (int, float))
            if not warn:
                return False, msg

            if dihedral[i] < -85 or dihedral[i] > 85:
                msg = 'The sweep value must be kept in the range [-85, 85] degrees. Change section {}'.format(i)
                return False, msg

        return True

    @twist.validator
    def twist(self, twists):
        """
        Validates if the twist inputs are within range, and the correct type
        :param twists:
        :return:
        """
        if len(twists) != self.n_sections + 1:
            msg = 'The number of section twists must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(twists)):
            warn, msg = type_warning(twists[i], 'twist', (int, float))
            if not warn:
                return False, msg
            if twists[i] < -85 or twists[i] > 85:
                msg = 'The sweep value must be kept in the range [-85, 85] degrees. Change section {}'.format(i)
                return False, msg

        return True

    @airfoil_sections.validator
    def airfoil_sections(self, sections):
        """
        Validates the airfoil section order, limits, and coherence.
        :param sections:
        :return:
        """
        if len(sections) != self.n_airfoils:
            msg = 'The number of airfoil locations must be coherent with the number of airfoils.' \
                  ' If you want to add/remove sections, change n_airfoils'
            return False, msg

        if (0 or 1) not in sections:
            msg = 'Either no tip or no root airfoil was input'
            return False, msg

        for i in range(1, len(sections[1:])):
            warn, msg = type_warning(sections[i], 'airfoil sections', (int, float))
            if not warn:
                return False, msg
            if sections[i] <= 0:
                msg = 'The airfoil span sections cannot be negative or equal to zero.' \
                      'Change airfoil location {}'.format(i)
                return False, msg
            if sections[i] == sections[i - 1]:
                msg = 'Two airfoils cannot be defined at the same span length. Change airfoil location {}'.format(i)
                return False, msg
            if sections[i] < sections[i - 1]:
                msg = 'The airfoils must be organized in ascending order. Change airfoil location {}'.format(i)
                return False, msg
            if sections[i] > 1 or sections[i] < 0:
                msg = 'The airfoil location cannot be located outside of the span. Change airfoil location {}'.format(i)
                return False, msg

        return True

    @airfoil_names.validator
    def airfoil_names(self, names):
        """
        Validates the airfoil name feasibility, either by searching in the airfoil folder or by using the
        NACA 4/5 digit generator.
        :param names:
        :return:
        """

        name_database_dat = os.listdir('wingbox_code/input_data/airfoils')
        name_database = [name.split('.')[0] for name in name_database_dat]

        if len(names) != self.n_airfoils:
            msg = 'The number of airfoil names must be coherent with the number of airfoils.' \
                  ' If you want to add/remove sections, change n_airfoils'
            return False, msg

        for i in range(len(names)):
            warn, msg = type_warning(names[i], 'airfoil names', str)
            if not warn:
                return False, msg

            if (names[i] not in name_database) and not (len(names[i]) == 4 or len(names[i]) == 5):
                msg = 'Invalid airfoil name. Make sure the name is correctly written or contains either 4 or 5 digits.'
                return False, msg

        return True

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
            if edges[i][0].start.y != edges[i-1][0].start.y:
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

            cst_u = (d_t-d_1)/d_t * coeff_u[idx[i][0], :] + (d_t-d_2)/d_t * coeff_u[idx[i][1], :]
            cst_l = (d_t-d_1)/d_t * coeff_l[idx[i][0], :] + (d_t-d_2)/d_t * coeff_l[idx[i][1], :]

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

        unscaled_order = [airfoils[i] for i in sorted_indices]
        scaled_order = [airfoils[i].scaled_foil for i in sorted_indices]
        guides_order = [guides[i] for i in sorted_indices]

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
                         hidden=True)

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
                           hidden=True)

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



if __name__ == '__main__':
    from parapy.gui import display
    display(WingGeom())
