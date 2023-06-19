from parapy.core import *
from parapy.geom import *
from parapy.exchange import *
from parapy.core.validate import *
from ..format.tk_warn import type_warning
from .ribssystem import RibsSystem
from .sparsystem import SparSystem
from .skinsystem import SkinSystem
from .stringersystem import StringerSystem


class WingBox(GeomBase):

    # Geometry
    wing = Input()
    n_sections = Input(validator=And(Positive(), IsInstance(int)))

    # STRUCTURAL DETAILS
    # Ribs
    rib_idx = Input(validator=IsInstance(list))

    # Spars
    front_spar_loc = Input(validator=IsInstance(list))
    rear_spar_loc = Input(validator=IsInstance(list))

    # Stringers
    stringer_idx = Input(validator=IsInstance(list))

    # Trailing edge gaps for skin and ribs
    TE_ribs_gap = Input(validator=Range(0, 0.98))  # Must be after the rearmost rear_spar_loc but less than 0.98
    TE_skin_gap = Input(validator=Range(0, 0.98))  # Must be after the rearmost rear_spar_loc but less than 1

    @rib_idx.validator
    def rib_idx(self, ribs):
        """
        Validates list coherence as well as that the elements are positive and integers
        :param ribs:
        :return:
        """
        if len(ribs) != self.n_sections:
            msg = 'The number of section ribs must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for rib in ribs:
            warn, msg = type_warning(rib, 'rib number', int)
            if not warn:
                return False, msg

            if rib <= 0:
                msg = 'The amount of ribs must at least be 1 for every section'
                return False, msg

        return True

    @front_spar_loc.validator
    def front_spar_loc(self, fs_locs):
        """
        It validates the location of the spars, its coherence, and makes sure that it stays within the chord
        and does not cross over the rear spar.
        :param fs_locs:
        :return:
        """

        if len(fs_locs) != self.n_sections + 1:
            msg = 'The number of section front spar locations must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(fs_locs)):
            warn, msg = type_warning(fs_locs[i], 'front spar location', float)
            if not warn:
                return False, msg

            if fs_locs[i] <= 0 or fs_locs[i] >= 1:
                msg = 'Front spar locations must be limited between 0 and 1 to stay within the chord'
                return False, msg

            if fs_locs[i] >= self.rear_spar_loc[i]:
                msg = 'The front spar cannot be further aft than the rear spar'
                return False, msg

        return True

    @rear_spar_loc.validator
    def rear_spar_loc(self, rs_locs):
        """
        It validates the location of the spars, its coherence, and makes sure that it stays within the chord
        and does not cross over the front spar.
        :param rs_locs:
        :return:
        """

        if len(rs_locs) != self.n_sections + 1:
            msg = 'The number of section rear spar locations must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for i in range(len(rs_locs)):
            warn, msg = type_warning(rs_locs[i], 'rear spar location', float)
            if not warn:
                return False, msg

            if rs_locs[i] <= 0 or rs_locs[i] >= 1:
                msg = 'Rear spar locations must be limited between 0 and 1 to stay within the chord'
                return False, msg

        return True

    @stringer_idx.validator
    def stringer_idx(self, stringers):
        '''
        Validates list coherence as well as that the elements are positive and integers
        :param stringers:
        :return:
        '''
        if len(stringers) != self.n_sections:
            msg = 'The number of section stringers must be coherent with the number of sections.' \
                  ' If you want to add/remove sections, change n_sections.'
            return False, msg

        for section in stringers:
            for num_stringer in section:
                warn, msg = type_warning(num_stringer, 'stringer', int)
                if not warn:
                    return False, msg
            if len(section) != 2:
                msg = 'Wrong number of inputs. The list must have two inputs per section: top and bottom stringers.'
                return False, msg

        return True

    @TE_skin_gap.validator
    def TE_skin_gap(self, value):
        """
        Verifies that the gap is kept further back than the rear spar
        :param value:
        :return:
        """
        for i in range(self.n_sections + 1):
            if value < self.rear_spar_loc[i]:
                msg = 'The skin cut location cannot be located further front than the aft spar.'
                return False, msg
            if value > 0.98:
                msg = 'The skin cut location cannot be located more than 98% of the chord'
                return False, msg

        return True

    @TE_ribs_gap.validator
    def TE_ribs_gap(self, value):
        """
        Verifies that the gap is kept further back than the rear spar
        :param value:
        :return:
        """
        for i in range(self.n_sections + 1):
            if value < self.rear_spar_loc[i]:
                msg = 'The rib cut location cannot be located further front than the aft spar.'
                return False, msg
            if value > 0.98:
                msg = 'The rib cut location cannot be located more than 98% of the chord'
                return False, msg

        return True

    @Attribute
    def STEP_node_list(self):
        STEP_lst = [self.skin.skin, self.spars.spars[0].total_cutter, self.spars.spars[1].total_cutter]
        STEP_lst.extend([rib for rib in self.ribs.ribs])
        STEP_lst.extend([stringer.stringers for stringer in self.stringers.top_stringers])
        STEP_lst.extend([stringer.stringers for stringer in self.stringers.bottom_stringers])
        return STEP_lst

    @Part
    def skin(self):
        return SkinSystem(TE_gap=self.TE_skin_gap,
                          ribs=self.ribs,
                          wing=self.wing)

    @Part
    def spars(self):
        return SparSystem(front_spar_loc=self.front_spar_loc,
                          rear_spar_loc=self.rear_spar_loc,
                          wing=self.wing)

    @Part
    def ribs(self):
        return RibsSystem(rib_idx=self.rib_idx,
                          TE_gap=self.TE_ribs_gap,
                          wing=self.wing)

    @Part
    def stringers(self):
        return StringerSystem(pass_down=['spars', 'ribs', 'wing', 'stringer_idx'])

    @Attribute
    def STEP_file(self):
        return STEPWriter(nodes=self.STEP_node_list, schema='AP203')


if __name__ == '__main__':
    from parapy.gui import display

    display(WingBox())
