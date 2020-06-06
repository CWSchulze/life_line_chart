
class BaseFamily():
    """
    Base class for families. This class is used as interface to the database.
    """

    def __init__(self, instances, family_id):
        self._instances = instances
        self.family_id = family_id
        self.husband_individual_id = None
        self.wife_individual_id = None
        self.children_individual_ids = []
        self.graphical_representations = []
        self.marriage = None
        self.location = None

    def __repr__(self):
        return 'family "' + self.husb_name + '"+"' + self.wife_name + '"'

    def __lt__(self, other):
        """
        Sorting by marriage date

        Args:
            other (BaseFamily): the other instance

        Returns:
            bool: is less than
        """
        return self.marriage['ordinal_value'] < other.marriage['ordinal_value']

    def _initialize(self):
        self.husband_individual_id, self.wife_individual_id = self._get_husband_and_wife_id()
        self.children_individual_ids = self._get_children_ids()

    def has_graphical_representation(self):
        """
        this family has a graphical representation

        Returns:
            bool: has a gaphical representation
        """
        return len(self.graphical_representations) > 0

    def has_graphical_representation_of_spouse(self):
        """
        true if at least one spouse has a graphical representation

        Returns:
            bool: has graphical representation of spouse
        """
        return (self.husb is not None and self.husb.has_graphical_representation()) or \
                    (self.wife is not None and self.wife.has_graphical_representation())

    def has_children(self):
        """
        this family has children

        Returns:
            bool: has children
        """
        return len(self.children_individual_ids) > 0

    def get_husband_and_wife(self):
        """
        get the husband and wife BaseIndividual

        Returns:
            tuple: husband, wife
        """
        return self._instances[('i', self.husband_individual_id)], self._instances[('i', self.wife_individual_id)]

    def get_spouse(self, individual_id):
        """
        get the spouse of the individual

        Args:
            individual_id (str): individual id

        Raises:
            RuntimeError: This individual is not part of the family!

        Returns:
            BaseIndividual: spouse
        """
        if individual_id == self.husband_individual_id:
            return self._instances[('i', self.wife_individual_id)]
        elif individual_id == self.wife_individual_id:
            return self._instances[('i', self.husband_individual_id)]
        else:
            raise RuntimeError("This individual is not part of the family!")

    def get_children(self):
        """
        get the children BaseIndividual instances

        Returns:
            list: list of children instances
        """
        children = []
        for id in self.children_individual_ids:
            child = self._instances[('i', id)]
            if child:
                children.append(child)
        return children
    """
    children BaseIndividual instances
    """
    children = property(get_children)

    def get_sorted_children(self):
        """
        get the list of children BaseIndividuals sorted by birth date

        Returns:
            list: sorted list of children instances
        """
        def get_date_ov(child):
            if child.events['birth_or_christening']:
                return child.events['birth_or_christening']['ordinal_value']
            else:
                return 0
        return [child for ov, index, child in [(get_date_ov(child), index, child) for index, child in enumerate(self.children)]]

    def _get_husband_and_wife_id(self):
        if True:
            raise NotImplementedError()
        return ()

    def _get_children_ids(self):
        if True:
            raise NotImplementedError()
        return []

    @property
    def husb_name(self):
        if True:
            raise NotImplementedError()
        return ""

    @property
    def wife_name(self):
        if True:
            raise NotImplementedError()
        return ""

    @property
    def husb(self):
        return self._instances[('i', self.husband_individual_id)]

    @property
    def wife(self):
        return self._instances[('i', self.wife_individual_id)]

    @property
    def marriage_date(self):
        return self._instances.display_marriage_date(self)

    @property
    def marriage_label(self):
        event = self.marriage
        date_str = self.marriage_date
        if event['comment']:
            string = self._instances.date_label_translation[event['comment']].format(
                symbol='', date=date_str)
        else:
            string = date_str
        marriage_location = self._instances.display_marriage_location(self)
        if marriage_location:
            string += '\nin ' + marriage_location
        return string
