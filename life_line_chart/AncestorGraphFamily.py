
class GraphicalFamily():
    """
    Class which represents one appearance of a family
    """
    _x_position = None
    # color = 'rgb(200,200,255)'

    def __init__(self, instances, family_id):
        self.graphical_representations = []
        self.family_id = family_id
        self.__instances = instances
        self.family = self.__instances[('f', self.family_id)]
        self.family.graphical_representations.append(self)
        self.marriage = self.family.marriage

        # Tells which children are visible
        self.visible_children = {}

        # Ancestor chart: Tells which child was used to place this family (this
        # is a strong connection)
        self.visual_placement_child = None

        # Descendant chart: Used to define under which family this family has
        # been placed (e.g. if wife/husband are from different branches of the
        # family)
        self.visual_placement_parent_family = None
        self.children_width = None

    def __repr__(self):
        return 'gr_family "' + self.family.husb_name + '"+"' + self.family.wife_name + '"'

    def get_spouse(self, individual):
        spouse = self.family.get_spouse(
            individual.individual_id)
        if not spouse or not spouse.graphical_representations:
            return None
        return self.family.get_spouse(individual.individual_id).graphical_representations[0]

    def add_visible_children(self, individual):
        if individual.individual_id not in self.visible_children and individual.graphical_representations[0].get_birth_date_ov():
            self.visible_children[individual.individual_id] = (
                individual.graphical_representations[0].get_birth_date_ov(),
                len(self.visible_children),
                individual
            )

    def __get_husb_name(self):
        return self.family.husb_name
    husb_name = property(__get_husb_name)

    def __get_wife_name(self):
        return self.family.wife_name
    wife_name = property(__get_wife_name)

    def __get_husb(self):
        return self.family.husb
    husb = property(__get_husb)

    def __get_wife(self):
        return self.family.wife
    wife = property(__get_wife)

    def __get_label(self):
        return self.family.label
    label = property(__get_label)
