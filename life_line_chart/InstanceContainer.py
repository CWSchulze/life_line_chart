import logging
from .ReadGedcom import read_data
import os
import json
from .GedcomIndividual import GedcomIndividual
from .GedcomFamily import GedcomFamily
from .Exceptions import LifeLineChartNotEnoughInformationToDisplay

logging.basicConfig()  # level=20)
logger = logging.getLogger("life_line_chart")


class InstanceContainer():
    """
    Container class for all kinds of instances. This class reads the database.
    """

    date_label_translation = {
        'Calculated': '{symbol}\xa0berechnet\xa0{date}',
        'Estimated': '{symbol}\xa0geschätzt\xa0{date}',
        'Estimated (min 25 at marriage)': '{symbol}\xa0geschätzt\xa0{date}',
        'Estimated (max age 75)': '{symbol}\xa0geschätzt\xa0{date}',
        'Estimated (max age 100)': '{symbol}\xa0geschätzt\xa0{date}',
        'Estimated (min 1 after parents marriage)': '{symbol}\xa0geschätzt\xa0{date}',
        'Still alive': '',
        'About': '{symbol}\xa0etwa\xa0{date}',
        'Before': '{symbol}\xa0vor\xa0{date}',
        'After': '{symbol}\xa0nach\xa0{date}',
        'YearPrecision': '{symbol}\xa0{date}',
        'Between': '{symbol}\xa0{date}'
    }

    def __init__(self, family_constructor, individual_constructor, instantiate_all):
        self._data = {('i', None): None, ('f', None): None}
        self._family_constructor = family_constructor
        self._individual_constructor = individual_constructor
        self.instantiate_all = instantiate_all
        self.ancestor_width_cache = {}

    def __iter__(self):  # iterate over all keys
        for type_id, instance in self._data.keys():
            if instance is not None:
                yield (type_id, instance)

    def items(self):  # iterate over all keys
        for key, value in self._data.items():
            if not key[1] is None:
                yield (key, value)

    def __contains__(self, key):
        if key[1] is None:
            return False
        elif key[0] == 'i':
            item = self._data.get(key)
            if item is not None:
                return True
            return False
        elif key[0] == 'f':
            item = self._data.get(key)
            if item is not None:
                return True
            return False
        return False

    def __getitem__(self, key):
        if key[1] is None:
            return self._data[key]
        elif key[0] == 'i':
            item = self._data.get(key)
            if item is None:
                try:
                    item = self._individual_constructor(self, key)
                    self._data[key] = item
                except LifeLineChartNotEnoughInformationToDisplay:
                    item = None
            return item
        elif key[0] == 'f':
            item = self._data.get(key)
            if item is None:
                try:
                    item = self._family_constructor(self, key)
                    self._data[key] = item
                except LifeLineChartNotEnoughInformationToDisplay:
                    item = None
            return item
        return None

    def __setitem__(self, key, value):
        self._data[key] = value

    def clear(self):
        """
        clear all data
        """
        self._data.clear()
        self._data.update({('i', None): None, ('f', None): None})


def get_gedcom_instance_container(filename='gramps_testdata.ged'):
    """
    instance container for families and individuals from gedcom file

    Args:
        filename (str, optional): gedcom file. Defaults to 'gramps_testdata.ged'.

    Returns:
        InstanceContainer: instance container
    """
    logger.debug('start reading data')
    if True:
        if filename:
            # read gedcom and write json
            database_indi, database_fam = read_data(filename)
            # self.database_indi, self.database_fam = read_data('--- febr. 2015.ged')
            # open(os.path.join('..', os.path.dirname(__file__), 'indi.json'),'w').write(json.dumps(database_indi))
            # open(os.path.join('..', os.path.dirname(__file__), 'fam.json'),'w').write(json.dumps(database_fam))
        else:
            database_indi = {}
            database_fam = {}
    else:
        # read json
        database_indi = json.loads(
            open(os.path.join('..', os.path.dirname(__file__), 'indi.json'), 'r').read())
        database_fam = json.loads(
            open(os.path.join('..', os.path.dirname(__file__), 'fam.json'), 'r').read())

    def instantiate_all(self, database_fam, database_indi):
        for family_id in list(database_fam.keys()):
            if not ('f', family_id) in self:
                self[('f', family_id)] = GedcomFamily(
                    self, database_fam, database_indi, family_id)
        for individual_id in list(database_indi.keys()):
            if not ('i', individual_id) in self:
                self[('i', individual_id)] = GedcomIndividual(
                    self, database_fam, database_indi, individual_id)

    logger.debug('start creating instances')
    return InstanceContainer(
        lambda self, key: GedcomFamily(
            self, database_fam, database_indi, key[1]),
        lambda self, key: GedcomIndividual(
            self, database_fam, database_indi, key[1]),
        lambda self: instantiate_all(self, database_fam, database_indi))
