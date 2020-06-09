from .BaseFamily import BaseFamily
from .GedcomParsing import get_date_dict_from_tag, _get_relevant_events, estimate_marriage_date
from .Exceptions import LifeLineChartNotEnoughInformationToDisplay


class GedcomFamily(BaseFamily):
    """
    GedcomFamily class for gedcom files
    """

    def __init__(self, instances, database_fam, database_indi, family_id):
        BaseFamily.__init__(self, instances, family_id)
        self._database_fam = database_fam
        self._database_indi = database_indi
        self._initialize()

    def _initialize(self):
        BaseFamily._initialize(self)
        self.marriage = get_date_dict_from_tag(
            self._database_fam[self.family_id], 'MARR')
        if 'MARR' in self._database_fam[self.family_id]:
            if 'PLAC' in self._database_fam[self.family_id]['MARR']:
                self.location = self._database_fam[self.family_id]['MARR']['PLAC']['tag_data']
        estimate_marriage_date(self)
        if self.marriage is None:
            raise LifeLineChartNotEnoughInformationToDisplay(
                "Marriage date is missing "+self.family_id)

    def _get_husband_and_wife_id(self):
        """
        get the individual ids of husband wife

        Returns:
            tuple: husband, wife
        """
        husb = self._database_fam[self.family_id].get('HUSB')
        wife = self._database_fam[self.family_id].get('WIFE')
        if husb:
            husb = husb['tag_data']
        if wife:
            wife = wife['tag_data']
        return husb, wife

    def _get_children_ids(self):
        """
        get the individual ids of the children

        Returns:
            list: list of children individual ids
        """
        try:
            if 'CHIL' not in self._database_fam[self.family_id]:
                return []
            return self._database_fam[self.family_id]['CHIL']['tag_data'].split('\n')
        except KeyError:
            return []

    @property
    def husb_name(self):
        """
        get the husband name

        Returns:
            str: husband name
        """
        try:
            name = self._database_indi[self.husband_individual_id]['NAME']['tag_data']
        except KeyError:
            name = "unknown"
        return name

    @property
    def wife_name(self):
        """
        get the wife name

        Returns:
            str: wife name
        """
        try:
            name = self._database_indi[self.wife_individual_id]['NAME']['tag_data']
        except KeyError:
            name = "unknown"
        return name

