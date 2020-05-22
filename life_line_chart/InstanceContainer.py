import logging
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

