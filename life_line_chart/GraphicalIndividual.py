from .GedcomIndividual import GedcomIndividual
from .Exceptions import LifeLineChartUnknownPlacementError

class GraphicalIndividual():
    """
    Class which represents one appearance of an individual

    If a parent family is strongly connected to a child, then the family will
    be moved if the child is moved. Weak connections are ignored.

    There are two degrees of freedom when placing the parent family.
    1. If several siblings are visible, then one sibling needs to be selected
    for the strong connection.
    2. If the selected sibling was married several times, then the marriage
    needs to be selected.
    """

    # x positions in different family appearances
    _x_position = None
    # color of this individual
    color = [200, 200, 255]
    # ordinal value of the birth date
    __birth_date_ov = None
    # ordinal value of the death date
    __death_date_ov = None
    weight = 1

    def __init__(self, instances, individual_id):
        self.items = []
        self.individual_id = individual_id
        self.__instances = instances
        self.individual = self.__instances[('i', self.individual_id)]
        self.individual.graphical_representations.append(self)
        self.debug_label = ""
        self.g_id = None

        # in ancestor charts children can be added, which are strongly connected, but
        # since they are a dead end, not a root, they cannot be used for placement
        self.qualified_for_placement = True

        self.special_properties = {}

        self.ancestor_chart_parent_family_placement = None, None

    def __repr__(self):
        return 'gr_individual "' + self.individual.plain_name + '" ' + self.individual.birth_date

    def __lt__(self, other):
        """
        Sorting by birth date

        Args:
            other (GraphicalIndividual): the other instance

        Returns:
            bool: is less than
        """
        return self.birth_date_ov < other.birth_date_ov

    def __eq__(self, other):
        """
        == operator

        Args:
            other (GraphicalIndividual): other instance

        Returns:
            bool: is equal
        """
        if type(other) != GraphicalIndividual:
            return False
        return self.g_id == other.g_id

    def get_marriages(self):
        marriages = self.individual.marriages
        return [m.graphical_representations[0] for m in marriages if m.has_graphical_representation()]

    def get_ancestor_width(self, gr_family):
        """
        Width of the ancestor individuals which are strongly connected.
        (only tested with ancestor chart)

        Args:
            gr_family (GraphicalFamily): gr_family which is examined

        Returns:
            int: width
        """
        x_min, x_max = self.get_ancestor_range(gr_family)
        width = x_max - x_min + 1
        return width

    def get_ancestor_range(self, gr_family):
        """
        Get the x range from min to max.
        (only tested with ancestor chart)

        Args:
            gr_family (GraphicalFamily): family which is examined

        Returns:
            tuple: x_min, x_max
        """
        gr_family_g_id = None
        if gr_family is not None:
            gr_family_g_id = gr_family.g_id
            # at least root node has None
        if (self.g_id, gr_family_g_id) in self.__instances.ancestor_width_cache:
            # caching
            return self.__instances.ancestor_width_cache[(self.g_id, gr_family_g_id)]
        x_v = [self._x_position[gr_family_g_id][1]]
        x_min = x_v.copy()
        x_max = x_v.copy()
        # if [3] is true, then that index is the ancestor family

        strongly_connected_parent_family, strongly_connected_spouse_family = self.ancestor_chart_parent_family_placement

        if strongly_connected_parent_family and strongly_connected_spouse_family == gr_family:
            gr_father = strongly_connected_parent_family.gr_husb
            if gr_father:
                # only handle if the father is visible
                f_x_min, f_x_max = gr_father.get_ancestor_range(
                    strongly_connected_parent_family)
                x_min.append(f_x_min)
                x_max.append(f_x_max)
            gr_mother = strongly_connected_parent_family.gr_wife
            if gr_mother:
                # only handle if the mother is visible
                m_x_min, m_x_max = gr_mother.get_ancestor_range(
                    strongly_connected_parent_family)
                x_min.append(m_x_min)
                x_max.append(m_x_max)
            # add siblings
            x_v = [gr_c.get_x_index(strongly_connected_parent_family.g_id) for gr_c in strongly_connected_parent_family.visible_children
                        if strongly_connected_parent_family.g_id in gr_c.get_position_dict()]
            x_min += x_v
            x_max += x_v

        x_min = min(x_min)
        x_max = max(x_max)
        self.__instances.ancestor_width_cache[(self.g_id, gr_family_g_id)] = x_min, x_max
        return x_min, x_max

    def get_descendant_width(self, gr_family):
        """
        Width of the descendant individuals which are strongly connected.
        (only tested with descendant chart)

        Args:
            gr_family (GraphicalFamily): family which is examined

        Returns:
            int: width
        """
        x_min, x_max = self.get_descendant_range(gr_family)
        width = x_max - x_min + 1
        return width

    def get_descendant_range(self, gr_family):
        """
        Get the x range from min to max.
        (only tested with descendant chart)

        Args:
            gr_family (GraphicalFamily): family which is examined

        Returns:
            tuple: x_min, x_max
        """
        family_id = None
        family = None
        family_g_id = None
        if gr_family is not None:
            family_id = gr_family.family_id
            family = gr_family.family
            family_g_id = gr_family.g_id
            # at least root node has None
        if (self.individual_id, family_id) in self.__instances.ancestor_width_cache:
            # caching
            #return self.__instances.ancestor_width_cache[(self.individual_id, family_id)]
            pass

        x_min = []
        x_max = []

        parent_family = self.__instances[('f', family_id)]
        if parent_family is None or not parent_family.has_graphical_representation():
            #return 1
            pass

        # marriages which have been placed over this parent family
        visible_local_marriages = \
            [marriage for marriage in self.visible_marriages \
                if gr_family is None or \
                    marriage.descendant_chart_parent_family_placement == gr_family]

        marriages = self.individual.marriages
        for vm in visible_local_marriages:
                marriage = vm.family
                gr_marriage = vm
                if family_id is None or gr_marriage.visual_placement_parent_family is not None and \
                    gr_marriage.visual_placement_parent_family.family_id == family_id:

                    x_min.append(self._x_position[gr_marriage.g_id][1])
                    x_max.append(self._x_position[gr_marriage.g_id][1])

                    for gr_child in gr_marriage.visible_children:
                        c_x_min, c_x_max = gr_child.get_descendant_range(
                            gr_marriage)
                        x_min.append(c_x_min)
                        x_max.append(c_x_max)

                    gr_spouse = gr_marriage.get_gr_spouse(self)
                    if gr_spouse:
                        x_v = gr_spouse.get_x_index(gr_marriage.g_id)
                        x_min.append(x_v)
                        x_max.append(x_v)

        if len(x_min) == 0 and len(x_max) == 0:
            x_v = [self._x_position[family_g_id][1]]
            x_min += x_v
            x_max += x_v
        x_min = min(x_min)
        x_max = max(x_max)
        self.__instances.ancestor_width_cache[(self.individual_id, family_id)] = x_min, x_max
        return x_min, x_max

    @property
    def visible_marriages(self):
        """
        List of marriages which have a graphical representation.

        Returns:
            list: list of visible marriages
        """
        if self.g_id not in self.__instances.connection_container['i']:
            return []
        connected_parent_families = []
        for g_id, connections in self.__instances.connection_container['i'][self.g_id].items():
            if 'gr_husb' in connections or 'gr_wife' in connections:
                connected_parent_families.append(self.__instances[('f', g_id[1])].graphical_representations[g_id[0]])
        if len(connected_parent_families) > 0:
            connected_parent_families.sort()
            return connected_parent_families
        return []

    @property
    def connected_parent_families(self):
        """
        Child of families where this individual appears.

        Returns:
            list: list of parent families
        """
        if self.g_id not in self.__instances.connection_container['i']:
            return []
        connected_parent_families = []
        for g_id, connections in self.__instances.connection_container['i'][self.g_id].items():
            if 'weak_child' in connections:
                connected_parent_families.append(self.__instances[('f', g_id[1])].graphical_representations[g_id[0]])
        if len(connected_parent_families) > 0:
            return connected_parent_families
        return []

    @property
    def ancestor_chart_parent_family_placement(self):
        """
        This is the tuple with parent family and spouse/marriage family which are strongly connected.
        The parent family is placed above the individual at the marriage family position.

        Raises:
            LifeLineChartUnknownPlacementError: placing error

        Returns:
            tuple: strongly connected parent family and spouse family
        """
        if self.g_id not in self.__instances.connection_container['i']:
            return None
        strongly_connected_parent_families = []
        strongly_connected_spouse_families = []
        for g_id, connections in self.__instances.connection_container['i'][self.g_id].items():
            if 'strong_child' in connections:
                strongly_connected_parent_families.append(self.__instances[('f', g_id[1])].graphical_representations[g_id[0]])
            if 'strong_marriage' in connections:
                strongly_connected_spouse_families.append(self.__instances[('f', g_id[1])].graphical_representations[g_id[0]])
        if len(strongly_connected_parent_families) > 1:
            raise LifeLineChartUnknownPlacementError("Something went wrong in the placement algorithm")
        elif len(strongly_connected_spouse_families) > 1:
            raise LifeLineChartUnknownPlacementError("Something went wrong in the placement algorithm")
        strongly_connected_parent_family = None
        strongly_connected_spouse_family = None
        if len(strongly_connected_parent_families) > 0:
            strongly_connected_parent_family = strongly_connected_parent_families[0]
        if len(strongly_connected_spouse_families) > 0:
            strongly_connected_spouse_family = strongly_connected_spouse_families[0]
        return strongly_connected_parent_family, strongly_connected_spouse_family

    @ancestor_chart_parent_family_placement.setter
    def ancestor_chart_parent_family_placement(self, gr_families):
        gr_parent_family, gr_spouse_family = gr_families
        if gr_parent_family != None:
            self.__instances.connection_container['i'][self.g_id][gr_parent_family.g_id].append('strong_child')
            self.__instances.connection_container['f'][gr_parent_family.g_id][self.g_id].append('strong_child')
        if gr_spouse_family != None:
            self.__instances.connection_container['i'][self.g_id][gr_spouse_family.g_id].append('strong_marriage')
            self.__instances.connection_container['f'][gr_spouse_family.g_id][self.g_id].append('strong_marriage')

    def get_name(self):
        return self.individual.get_name()

    def __get_birth_date(self):
        if self.individual.events['birth_or_christening']:
            return self.individual.events['birth_or_christening']['date'].date().strftime('%d.%m.%Y')
        else:
            return None
    birth_date = property(__get_birth_date)

    def __get_death_date(self):
        if self.individual.events['death_or_burial']:
            return self.individual.events['death_or_burial']['date'].date().strftime('%d.%m.%Y')
        else:
            return None
    death_date = property(__get_death_date)

    def get_position_dict(self, gr_family = None):
        if gr_family is None:
            return self._x_position
        else:
            return self._x_position.get(gr_family.g_id)

    def get_parent_positions(self):
        return dict([(k, v) for k, v in self._x_position.items() if v[3]])

    def get_spouse_positions(self):
        return dict([(k, v) for k, v in self._x_position.items() if not v[3]])

    def get_x_index(self, g_id):
        return self._x_position.get(g_id)[1]

    def get_other_family_connected_to_birth_position(self, gr_family):
        if gr_family is not None:
            g_id = gr_family.g_id
        else:
            g_id = None

        scpf, scsf = self.ancestor_chart_parent_family_placement

        # ancestor_placement_family = self.ancestor_placement_marriage

        # if scsf is None and scpf is None and ancestor_placement_family is not None:
        #     scsf = ancestor_placement_family

        other_g_id = "there is no connected family"
        scsf_g_id = scsf.g_id if scsf else None
        scpf_g_id = scpf.g_id if scpf else None
        if scsf or scpf:
            if g_id == scsf_g_id:
                # g_id is the strongyl connected spouse family
                other_g_id = scpf_g_id
            elif g_id == scpf_g_id:
                # g_id is the strongly connected parent family
                other_g_id = scsf_g_id

        return other_g_id

    def has_position_vector(self, family):
        if self._x_position is None:
            return False
        g_id = None
        if family is not None:
            g_id = family.g_id
        if g_id in self._x_position:
            return True
        return False

    def set_position_vector(self, x_position, gr_family, this_is_the_parent_family=False, overrule_ov=None):
        if gr_family:
            g_id = gr_family.g_id
            if gr_family.marriage:
                ov = gr_family.marriage['ordinal_value']
            else:
                ov = self.birth_date_ov
        else:
            g_id = None
            ov = self.birth_date_ov
        if overrule_ov:
            ov = overrule_ov
        if not self._x_position:
            self._x_position = {}
        if g_id not in self._x_position:
            self._x_position[g_id] = (
                (ov, x_position, gr_family, this_is_the_parent_family))
        _x_position = {}
        _x_position.update(dict(sorted(self._x_position.items(), key=lambda t: t[1][0])))
        self._x_position = _x_position

    x_position = property(get_position_dict, set_position_vector)

    @property
    def ancestor_placement_marriage(self):
        """
        The birth x position can be linked to a specific marriage. Ancestors will be placed above
        the birth x position.
        """
        if self.g_id not in self.__instances.connection_container['i']:
            return []
        gr_marriage_families = []
        for g_id, connections in self.__instances.connection_container['i'][self.g_id].items():
            if 'strong_marriage' in connections:
                gr_marriage_families.append(self.__instances[('f', g_id[1])].graphical_representations[g_id[0]])
        if len(gr_marriage_families) == 1:
            return gr_marriage_families[0]
        elif len(gr_marriage_families) > 1:
            raise LifeLineChartUnknownPlacementError("too many ancestor placement marriages " + str(gr_marriage_families) + " " + str(self))
        return None

    @ancestor_placement_marriage.setter
    def ancestor_placement_marriage(self, gr_marriage_family):
        """
        The birth x position can be linked to a specific marriage. Ancestors will be placed above
        the birth x position.

        Args:
            gr_marriage_family (GraphicalFamily): marriage where to place the ancestors
        """
        if gr_marriage_family:
            g_id = gr_marriage_family.g_id
        else:
            return
            g_id = None
        self.__instances.connection_container['i'][self.g_id][g_id].append('strong_marriage')
        self.__instances.connection_container['f'][g_id][self.g_id].append('strong_marriage')

    def is_cross_connection(self, gr_family_a, gr_family_b):
        """
        Returns true, if the two families do not share the same x position.

        Args:
            gr_family_a (GraphicalFamily): family a
            gr_family_b (GraphicalFamily): family b

        Returns:
            bool: is cross-connection
        """
        gr_family_g_id_a = gr_family_a.g_id if gr_family_a else None
        gr_family_g_id_b = gr_family_b.g_id if gr_family_b else None
        gr_family_pos_a = self._x_position.get(gr_family_g_id_a)
        gr_family_pos_b = self._x_position.get(gr_family_g_id_b)
        if gr_family_pos_a and gr_family_pos_b:
            if gr_family_pos_a[1] != gr_family_pos_b[1]:
                return True
            return False
        # this happens in descendant charts. spouses dont have a visible parent family.
        #raise LifeLineChartUnknownPlacementError("individual was not placed in requested family")
        return False

    def get_birth_event(self):
        return self.individual.events['birth_or_christening']

    def get_death_event(self):
        return self.individual.events['death_or_burial']

    @property
    def birth_date_ov(self):
        """
        Get the ordinal value of the birth (or christening or baptism) date.

        Returns:
            float: ordinal value of birth date
        """
        if self.__birth_date_ov is None:
            self.__birth_date_ov = self.individual.birth_date_ov
            return self.__birth_date_ov
        else:
            return self.__birth_date_ov

    @property
    def death_date_ov(self):
        """
        Get the ordinal value of the death (or burial) date.

        Returns:
            float: ordinal value of death date
        """
        if self.__death_date_ov is None:
            self.__death_date_ov = self.individual.death_date_ov
            return self.__death_date_ov
        else:
            return self.__death_date_ov

    @property
    def birth_label(self):
        return self.individual.birth_label# + self.debug_label

    @property
    def death_label(self):
        string = self.individual.death_label
        if len(self._x_position) > 2 or len(self._x_position) == 2 and list(self._x_position.values())[0][1] != list(self._x_position.values())[1][1]:
            string += ' ' + self.individual.plain_name
        return string

    @property
    def children(self):
        return self.individual.children

    @property
    def visible_children(self):
        """
        Get the all visible children of this individual (all visible marriages).

        Returns:
            list: list of children individuals
        """
        gr_children = []
        for vm in self.visible_marriages:
            gr_children += vm.visible_children
        return gr_children

    def get_all_ancestors(self):
        """
        get all ancestors places over this individual

        Returns:
            list: list of ancestors
        """
        gr_ancestors = []
        strongly_connected_parent_family, strongly_connected_spouse_family = self.ancestor_chart_parent_family_placement
        if strongly_connected_parent_family:
            if strongly_connected_parent_family.gr_husb:
                gr_ancestors += [(strongly_connected_parent_family, strongly_connected_parent_family.gr_husb)]
                gr_ancestors += strongly_connected_parent_family.gr_husb.get_all_ancestors()
            gr_ancestors += [(strongly_connected_parent_family, c) for c in strongly_connected_parent_family.visible_children]
            if strongly_connected_parent_family.gr_wife:
                gr_ancestors += [(strongly_connected_parent_family, strongly_connected_parent_family.gr_wife)]
                gr_ancestors += strongly_connected_parent_family.gr_wife.get_all_ancestors()
        return gr_ancestors

    def get_all_descendants(self):
        gr_descendants = []
        for vm in self.visible_marriages:
            for vc in vm.visible_children:
                if not self.connected_parent_families or vm.descendant_chart_parent_family_placement == self.connected_parent_families[0]:
                    gr_descendants += [(vm, vc)]
                    gr_descendants += vc.get_all_descendants()
        return gr_descendants
