from .GedcomIndividual import GedcomIndividual


class ancestor_graph_individual():
    """
    Class which represents one appearance of an individual
    """
    _x_position = None
    visible_parent_family = None
    x_start = None
    x_end = None
    color = [200, 200, 255]

    def __init__(self, instances, individual_id, distance):
        self._distance = distance
        self.items = []
        self.individual_id = individual_id
        self.__instances = instances
        self.individual = self.__instances[('i', self.individual_id)]
        self.__instances[('i', self.individual_id)
                         ].graphical_representations.append(self)
        self.widths = {}
        self.range = {}
        self.visual_placement_child = None
        pass

    def get_marriages(self):
        marriages = self.individual.marriages
        return [m.graphical_representations[0] for m in marriages if m.has_graphical_representation()]

    def get_width(self, family):
        if family or family not in self.widths:
            if family.family_id in self.widths:
                return self.widths[family.family_id]
            else:
                return self._distance
        else:
            return self.widths[family]
            # return max(0, self.x_end - self.x_start)
        width = 0
        for child_of_family in self.__instances[('i', self.individual_id)].get_child_of_family():
            father, mother = child_of_family.get_husband_and_wife()
            if father and father.graphical_representations:
                width += father.graphical_representations[0].get_width(
                    child_of_family)
            if mother and mother.graphical_representations:
                width += mother.graphical_representations[0].get_width(
                    child_of_family)
        if self.visible_parent_family and family.family_id == self.visible_parent_family.family_id:
            width += self._distance * \
                len(self.visible_parent_family.visible_children)
        else:
            width += self._distance
        return width

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
        # self._x_position = x_position
        # return
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

    x_position = property(get_x_position, set_x_position)

    def get_birth_event(self):
        return self.__instances[('i', self.individual_id)].events['birth_or_christening']

    def get_death_event(self):
        return self.__instances[('i', self.individual_id)].events['death_or_burial']

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
