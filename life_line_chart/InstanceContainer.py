import logging
import hashlib
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

    def color_generator(self, individual):
        """
        generate color for an individual

        Args:
            individual (BaseIndividual): individual to generate a color for
        """
        i = int(hashlib.sha1(individual.plain_name.encode(
            'utf8')).hexdigest(), 16) % (10 ** 8)
        c = (i*23 % 255, i*41 % 255, (i*79 % 245) + 10)
        f = 255/max(c)
        c = [int(x*f) for x in c]
        f = min(1, 500/sum(c))
        return [int(x*f) for x in c]

    def display_plain_name(self, individual):
        return ' '.join([n.strip() for n in individual.get_name() if n.strip() != ''])

    def display_short_info_text(self, individual):
        content = [
            " ".join([n.strip() for n in individual.get_name() if n != '']).strip(),
            individual.birth_label,
            individual.death_label,
        ]
        return '\n'.join(content)

    def display_info_text(self, individual):
        content = [
            individual.plain_name,
            individual.birth_label,
            individual.death_label,
            '',
        ]
        for cof in individual.child_of_families:
            if cof.husb:
                content.append('Vater: {} ({})'.format(cof.wife.plain_name,
                    cof.wife.birth_label))
            if cof.wife:
                content.append('Mutter: {} ({})'.format(cof.wife.plain_name,
                    cof.wife.birth_label))

        content.append('')
        for marriage in individual.marriages:
            spouse = marriage.get_spouse(individual.individual_id)
            content.append('Partner: {} ({}), Heirat: {}'.format(
                spouse.plain_name, spouse.birth_label, marriage.marriage_label))
            for index, child in enumerate(marriage.get_sorted_children()):
                content.append(' {}. Kind: {} ({})'.format(
                    index + 1, child.plain_name, child.birth_label))

        return '\n'.join(content)

    def display_birth_date(self, individual):
        """
        get the birth (or christening or baptism) date str

        Returns:
            str: birth date str
        """

        event = individual.events['birth_or_christening']
        if event:
            if event['comment']:
                return str(event['date'].date().year)
            else:
                return event['date'].date().strftime('%d.%m.%Y')
        return None

    def display_death_date(self, individual):
        """
        get the death (or burial) date

        Returns:
            str: death date
        """

        event = individual.events['death_or_burial']
        if event:
            if event['comment']:
                return str(event['date'].date().year)
            else:
                return event['date'].date().strftime('%d.%m.%Y')
        return None

    def display_marriage_date(self, family):
        """
        get the marriage date str

        Returns:
            str: marriage date str
        """

        event = family.marriage
        if event['comment']:
            return str(event['date'].date().year)
        else:
            return event['date'].date().strftime('%d.%m.%Y')

    def display_marriage_location(self, family):
        """
        get the marriage location str

        Returns:
            str: marriage location str
        """

        if family.location:
            return family.location
        return None

