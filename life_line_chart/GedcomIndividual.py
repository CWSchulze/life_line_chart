from .BaseIndividual import BaseIndividual, estimate_birth_date, estimate_death_date
from .GedcomParsing import _get_relevant_events


class GedcomIndividual(BaseIndividual):
    """
    GedcomIndividual class for gedcom files
    """

    def __init__(self, instances, database_fam, database_indi, individual_id):
        BaseIndividual.__init__(self, instances, individual_id)
        self._database_fam = database_fam
        self._database_indi = database_indi
        self._initialize()

    def _initialize(self):
        BaseIndividual._initialize(self)
        if 'FAMC' in self._database_indi[self.individual_id]:
            self.child_of_family_id = self._database_indi[self.individual_id]['FAMC']['tag_data'].split(
                '\n')
        _get_relevant_events(self._database_indi,
                             self.individual_id, self.events)
        estimate_birth_date(self, self._instances)
        estimate_death_date(self)

    def _get_name(self):
        if 'NAME' in self._database_indi[self.individual_id]:
            return self._database_indi[self.individual_id]['NAME']['tag_data'].split('/')
        else:
            return [""]

    name = property(_get_name)

    def _get_father_and_mother(self):
        family_id = self._database_indi[self.individual_id]['FAMC']['tag_data']
        husb = self._database_fam[family_id].get('HUSB')
        wife = self._database_fam[family_id].get('WIFE')
        if husb:
            husb = husb['tag_data']
        if wife:
            wife = wife['tag_data']
        return husb, wife

    def _get_marriage_family_ids(self):
        try:
            if 'FAMS' not in self._database_indi[self.individual_id]:
                return []
            return self._database_indi[self.individual_id]['FAMS']['tag_data'].split('\n')
        except:
            pass
        return []
