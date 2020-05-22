from .GedcomIndividual import GedcomIndividual


class ancestor_graph_individual():
    """
    Class which represents one appearance of an individual
    """
    # x positions in different family appearances
    _x_position = None
    visible_parent_family = None
    # color of this individual
    color = [200, 200, 255]
    # tuple: child individual where this individual was placed, family where that child individual is child
    visual_placement_child = None
    # ordinal value of the birth date
    __birth_date_ov = None
    # ordinal value of the death date
    __death_date_ov = None

    def __init__(self, instances, individual_id):
        self.items = []
        self.individual_id = individual_id
        self.__instances = instances
        self.individual = self.__instances[('i', self.individual_id)]
        self.individual.graphical_representations.append(self)
        pass

    def __repr__(self):
        return 'gr_individual "' + self.individual.plain_name + '" ' + self.individual.birth_date

    def get_marriages(self):
        marriages = self.individual.marriages
        return [m.graphical_representations[0] for m in marriages if m.has_graphical_representation()]

    def get_width(self, family):
        """
        width of the ancestor individuals which are strongly connected

        Args:
            family (BaseFamily): family which is examined

        Returns:
            int: width
        """
        x_min, x_max = self.get_range(family)
        width = x_max - x_min + 1
        return width

    def get_range(self, family):
        """
        get the x range from min to max

        Args:
            family (BaseFamily): family which is examined

        Returns:
            tuple: x_min, x_max
        """
        family_id = None
        if family is not None:
            family_id = family.family_id
            # at least root node has None
        if (self.individual_id, family_id) in self.__instances.ancestor_width_cache:
            # caching
            return self.__instances.ancestor_width_cache[(self.individual_id, family_id)]
        x_v = [self._x_position[family_id][1]]
        x_min = x_v.copy()
        x_max = x_v.copy()
        # if [3] is true, then that index is the ancestor family
        index_of_first_marriage = 1 if self._x_position[list(self._x_position.keys())[0]][3] else 0

        ancestors_are_visible = self.visible_parent_family is not None
        # ancestors are not placed over first marriage, if the placement of the ancestors has already been done. E.g. siblings are not strongly connected
        ancestors_are_strongly_connected_to_first_marriage = list(self._x_position.values())[0][1]==list(self._x_position.values())[index_of_first_marriage][1]
        # ancestors are usually placed over first marriage, so count ancestors only if the searched family is the first one
        first_marriage_is_what_we_search = list(self._x_position.keys())[index_of_first_marriage] == family_id
        if ancestors_are_visible and ancestors_are_strongly_connected_to_first_marriage and first_marriage_is_what_we_search:
            father, mother = self.visible_parent_family.family.get_husband_and_wife()
            if father and father.has_graphical_representation():
                # only handle if the father is visible
                f_x_positions = father.graphical_representations[0].get_x_position()
                index_of_first_marriage = 1 if f_x_positions[list(f_x_positions.keys())[0]][3] else 0
                if list(f_x_positions.keys())[index_of_first_marriage] == self.visible_parent_family.family_id:
                    # count ancestors only, if the visible parent family is the first marriage (strong graphical connection)
                    f_x_min, f_x_max = father.graphical_representations[0].get_range(
                        self.visible_parent_family)
                    x_min.append(f_x_min)
                    x_max.append(f_x_max)
                else:
                    # ignore ancestors
                    x_pos = father.graphical_representations[0].get_x_position()[self.visible_parent_family.family_id][1]
                    x_min.append(x_pos)
                    x_max.append(x_pos)
            if mother and mother.has_graphical_representation():
                # only handle if the father is visible
                m_x_positions = mother.graphical_representations[0].get_x_position()
                index_of_first_marriage = 1 if m_x_positions[list(m_x_positions.keys())[0]][3] else 0
                if list(m_x_positions.keys())[index_of_first_marriage] == self.visible_parent_family.family_id:
                    # count ancestors only, if the visible parent family is the first marriage (strong graphical connection)
                    m_x_min, m_x_max = mother.graphical_representations[0].get_range(
                        self.visible_parent_family)
                    x_min.append(m_x_min)
                    x_max.append(m_x_max)
                else:
                    # ignore ancestors
                    x_pos = mother.graphical_representations[0].get_x_position()[self.visible_parent_family.family_id][1]
                    x_min.append(x_pos)
                    x_max.append(x_pos)
            # add siblings
            x_v = [c[2].graphical_representations[0].get_x_position()[self.visible_parent_family.family_id][1] for c_id, c in self.visible_parent_family.visible_children.items()
                        if self.visible_parent_family.family_id in c[2].graphical_representations[0].get_x_position()]
            x_min += x_v
            x_max += x_v
        x_min = min(x_min)
        x_max = max(x_max)
        self.__instances.ancestor_width_cache[(self.individual_id, family_id)] = x_min, x_max
        return x_min, x_max


    def get_width2(self, family):
        """
        width of the ancestor individuals which are strongly connected

        Args:
            family (BaseFamily): family which is examined

        Returns:
            int: width
        """
        x_min, x_max = self.get_range2(family)
        width = x_max - x_min + 1
        return width

    def get_range2(self, family):
        """
        get the x range from min to max

        Args:
            family (BaseFamily): family which is examined

        Returns:
            tuple: x_min, x_max
        """
        family_id = None
        if family is not None:
            family_id = family.family_id
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

        marriages = self.individual.marriages
        if len(marriages) > 0:
            for marriage in marriages:
                if not marriage.has_graphical_representation():
                    continue
                gr_marriage = marriage.graphical_representations[0]
                if gr_marriage.visual_placement_parent_family is not None and \
                    gr_marriage.visual_placement_parent_family.family_id == family_id:

                    x_min.append(self._x_position[marriage.family_id][1])
                    x_max.append(self._x_position[marriage.family_id][1])

                    for child in marriage.children:
                        if not child.has_graphical_representation():
                            continue
                        c_x_min, c_x_max = child.graphical_representations[0].get_range2(
                            marriage)
                        x_min.append(c_x_min)
                        x_max.append(c_x_max)

                    spouse = marriage.get_spouse(self.individual.individual_id)
                    if spouse and spouse.has_graphical_representation():
                        x_v = spouse.graphical_representations[0].get_x_position()[marriage.family_id][1]
                        x_min.append(x_v)
                        x_max.append(x_v)

        if len(x_min) == 0 and len(x_max) == 0:
            x_v = [self._x_position[family_id][1]]
            x_min += x_v
            x_max += x_v
        x_min = min(x_min)
        x_max = max(x_max)
        self.__instances.ancestor_width_cache[(self.individual_id, family_id)] = x_min, x_max
        return x_min, x_max

        # if [3] is true, then that index is the ancestor family
        index_of_first_marriage = 1 if self._x_position[list(self._x_position.keys())[0]][3] else 0

        ancestors_are_visible = self.visible_parent_family is not None
        # ancestors are not placed over first marriage, if the placement of the ancestors has already been done. E.g. siblings are not strongly connected
        ancestors_are_strongly_connected_to_first_marriage = list(self._x_position.values())[0][1]==list(self._x_position.values())[index_of_first_marriage][1]
        # ancestors are usually placed over first marriage, so count ancestors only if the searched family is the first one
        first_marriage_is_what_we_search = list(self._x_position.keys())[index_of_first_marriage] == family_id
        if ancestors_are_visible and ancestors_are_strongly_connected_to_first_marriage and first_marriage_is_what_we_search:
            father, mother = self.visible_parent_family.family.get_husband_and_wife()
            if father and father.has_graphical_representation():
                # only handle if the father is visible
                f_x_positions = father.graphical_representations[0].get_x_position()
                index_of_first_marriage = 1 if f_x_positions[list(f_x_positions.keys())[0]][3] else 0
                if list(f_x_positions.keys())[index_of_first_marriage] == self.visible_parent_family.family_id:
                    # count ancestors only, if the visible parent family is the first marriage (strong graphical connection)
                    f_x_min, f_x_max = father.graphical_representations[0].get_range(
                        self.visible_parent_family)
                    x_min.append(f_x_min)
                    x_max.append(f_x_max)
                else:
                    # ignore ancestors
                    x_pos = father.graphical_representations[0].get_x_position()[self.visible_parent_family.family_id][1]
                    x_min.append(x_pos)
                    x_max.append(x_pos)
            if mother and mother.has_graphical_representation():
                # only handle if the father is visible
                m_x_positions = mother.graphical_representations[0].get_x_position()
                index_of_first_marriage = 1 if m_x_positions[list(m_x_positions.keys())[0]][3] else 0
                if list(m_x_positions.keys())[index_of_first_marriage] == self.visible_parent_family.family_id:
                    # count ancestors only, if the visible parent family is the first marriage (strong graphical connection)
                    m_x_min, m_x_max = mother.graphical_representations[0].get_range(
                        self.visible_parent_family)
                    x_min.append(m_x_min)
                    x_max.append(m_x_max)
                else:
                    # ignore ancestors
                    x_pos = mother.graphical_representations[0].get_x_position()[self.visible_parent_family.family_id][1]
                    x_min.append(x_pos)
                    x_max.append(x_pos)
            # add siblings
            x_v = [c[2].graphical_representations[0].get_x_position()[self.visible_parent_family.family_id][1] for c_id, c in self.visible_parent_family.visible_children.items()
                        if self.visible_parent_family.family_id in c[2].graphical_representations[0].get_x_position()]
            x_min += x_v
            x_max += x_v
        x_min = min(x_min)
        x_max = max(x_max)
        self.__instances.ancestor_width_cache[(self.individual_id, family_id)] = x_min, x_max
        return x_min, x_max

    def __get_name(self):
        return self.individual.name
    name = property(__get_name)

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

    def get_x_position(self):
        return self._x_position

    def set_x_position(self, x_position, family, parent_starting_point=False):
        if family:
            family_id = family.family_id
            if family.marriage:
                ov = family.marriage['ordinal_value']
            else:
                ov = 0
        else:
            family_id = None
            ov = 0
        if not self._x_position:
            self._x_position = {}
        if family_id not in self._x_position:
            self._x_position[family_id] = (
                (ov, x_position, family, parent_starting_point))
        _x_position = {}
        if None in self._x_position:
            _x_position[None] = self._x_position[None]
        _x_position.update(dict(sorted([i for i in self._x_position.items() if i[0] is not None], key=lambda t: t[1])))
        self._x_position = _x_position

    x_position = property(get_x_position, set_x_position)

    def get_birth_event(self):
        return self.individual.events['birth_or_christening']

    def get_death_event(self):
        return self.individual.events['death_or_burial']

    def get_birth_date_ov(self):
        """
        get the ordinal value of the birth (or christening or baptism) date

        Returns:
            float: ordinal value of birth date
        """
        if self.__birth_date_ov is None:
            boc = self.individual.events.get('birth_or_christening')
            if boc:
                self.__birth_date_ov = boc['date'].date().toordinal()
                return self.__birth_date_ov
            return None
        else:
            return self.__birth_date_ov

    def get_death_date_ov(self):
        """
        get the ordinal value of the death (or burial) date

        Returns:
            float: ordinal value of death date
        """
        if self.__death_date_ov is None:
            dob = self.individual.events.get('death_or_burial')
            if dob:
                self.__death_date_ov = dob['date'].date().toordinal()
                return self.__death_date_ov
            return None
        else:
            return self.__death_date_ov

    def __get_birth_label(self):
        return self.individual.birth_label
    birth_label = property(__get_birth_label)

    def __get_death_label(self):
        string = self.individual.death_label
        if len(self._x_position) > 2 or len(self._x_position) == 2 and list(self._x_position.values())[0][1] != list(self._x_position.values())[1][1]:
            string += ' ' + " ".join(self.name)
        return string
    death_label = property(__get_death_label)

    def __get_children(self):
        return self.individual.children
    children = property(__get_children)
