
class GraphicalFamily():
    """
    Class which represents one appearance of a family
    """
    # color = 'rgb(200,200,255)'

    def __init__(self, instances, family_id):
        self.graphical_representations = []
        self.family_id = family_id
        self.__instances = instances
        self.family = self.__instances[('f', self.family_id)]
        self.family.graphical_representations.append(self)
        self.marriage = self.family.marriage

        # Tells which children are visible
        self.visible_children = []

        # Descendant chart: Used to define under which family this family has
        # been placed (e.g. if wife/husband are from different branches of the
        # family)
        self.visual_placement_parent_family = None
        self.g_id = None

    def __repr__(self):
        return 'gr_family "' + self.family.husb_name + '"+"' + self.family.wife_name + '"'

    def __lt__(self, other):
        """
        Sorting by marriage date

        Args:
            other (GraphicalFamily): the other instance

        Returns:
            bool: is less than
        """
        return self.family.marriage['ordinal_value'] < other.family.marriage['ordinal_value']

    def get_spouse(self, individual):
        spouse = self.family.get_spouse(
            individual.individual_id)
        if not spouse or not spouse.graphical_representations:
            return None
        return self.family.get_spouse(individual.individual_id).graphical_representations[0]

    def get_gr_spouse(self, gr_individual):
        if self.gr_husb == gr_individual:
            return self.gr_wife
        elif self.gr_wife == gr_individual:
            return self.gr_husb
        else:
            raise RuntimeError("This individual is not part of the family!")

    def add_visible_children(self, gr_child):
        if gr_child not in self.visible_children and gr_child.birth_date_ov:
            self.visible_children.append(gr_child)
            self.visible_children.sort()
        if gr_child != None:
            if self.g_id not in self.__instances.connection_container['f']:
                self.__instances.connection_container['f'][self.g_id] = {}
            if gr_child.g_id not in self.__instances.connection_container['f'][self.g_id]:
                self.__instances.connection_container['f'][self.g_id][gr_child.g_id] = []
            if "weak_child" not in self.__instances.connection_container['f'][self.g_id][gr_child.g_id]:
                self.__instances.connection_container['f'][self.g_id][gr_child.g_id].append("weak_child")

            if gr_child.g_id not in self.__instances.connection_container['i']:
                self.__instances.connection_container['i'][gr_child.g_id] = {}
            if self.g_id not in self.__instances.connection_container['i'][gr_child.g_id]:
                self.__instances.connection_container['i'][gr_child.g_id][self.g_id] = []
            if "weak_child" not in self.__instances.connection_container['i'][gr_child.g_id][self.g_id]:
                self.__instances.connection_container['i'][gr_child.g_id][self.g_id].append("weak_child")

    @property
    def connected_children(self):
        if self.g_id not in self.__instances.connection_container['f']:
            return None
        connected_children = []
        for g_id, connections in self.__instances.connection_container['f'][self.g_id].items():
            if 'weak_child' in connections:
                connected_children.append(self.__instances[('i', g_id[1])].graphical_representations[g_id[0]])
        if len(connected_children) > 0:
            return connected_children
        return []

    @property
    def strongly_connected_child(self):
        if self.g_id not in self.__instances.connection_container['f']:
            return None
        strongly_connected_children = []
        for g_id, connections in self.__instances.connection_container['f'][self.g_id].items():
            if 'strong_child' in connections:
                strongly_connected_children.append(self.__instances[('i', g_id[1])].graphical_representations[g_id[0]])
        if len(strongly_connected_children) > 1:
            raise RuntimeError("Something went wrong in the placement algorithm")
        elif len(strongly_connected_children) > 0:
            return strongly_connected_children[0]
        return None

    @strongly_connected_child.setter
    def strongly_connected_child(self, gr_child):
        if gr_child != None:
            self.__instances.connection_container['f'][self.g_id][gr_child.g_id].append('strong_child')
            self.__instances.connection_container['i'][gr_child.g_id][self.g_id].append('strong_child')

    @property
    def gr_husb(self):
        if self.g_id not in self.__instances.connection_container['f']:
            return None
        gr_husbs = []
        for g_id, connections in self.__instances.connection_container['f'][self.g_id].items():
            if 'gr_husb' in connections:
                gr_husbs.append(self.__instances[('i', g_id[1])].graphical_representations[g_id[0]])
        if len(gr_husbs) > 1:
            raise RuntimeError("Something went wrong in the placement algorithm")
        elif len(gr_husbs) > 0:
            return gr_husbs[0]
        return None

    @gr_husb.setter
    def gr_husb(self, gr_husb):
        if gr_husb != None:
            self.__instances.connection_container['f'][self.g_id][gr_husb.g_id].append('gr_husb')
            self.__instances.connection_container['i'][gr_husb.g_id][self.g_id].append('gr_husb')

    @property
    def gr_wife(self):
        if self.g_id not in self.__instances.connection_container['f']:
            return None
        gr_wifes = []
        for g_id, connections in self.__instances.connection_container['f'][self.g_id].items():
            if 'gr_wife' in connections:
                gr_wifes.append(self.__instances[('i', g_id[1])].graphical_representations[g_id[0]])
        if len(gr_wifes) > 1:
            raise RuntimeError("Something went wrong in the placement algorithm")
        elif len(gr_wifes) > 0:
            return gr_wifes[0]
        return None

    @gr_wife.setter
    def gr_wife(self, gr_wife):
        if gr_wife != None:
            self.__instances.connection_container['f'][self.g_id][gr_wife.g_id].append('gr_wife')
            self.__instances.connection_container['i'][gr_wife.g_id][self.g_id].append('gr_wife')

    @property
    def husb_name(self):
        return self.family.husb_name

    @property
    def wife_name(self):
        return self.family.wife_name

    @property
    def husb(self):
        return self.family.husb

    @property
    def wife(self):
        return self.family.wife

    @property
    def marriage_label(self):
        return self.family.marriage_label

