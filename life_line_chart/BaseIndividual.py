from copy import deepcopy
import datetime


def estimate_death_date(individual):
    """
    if the death is unknown, then guess the death date by assuming the maximum age of 75 years or after 1900 100 years.

    Args:
        individual (BaseIndividual): individual instance
    """
    if individual.events['death_or_burial'] is None and not individual.events['birth_or_christening'] is None:
        date = individual.events['birth_or_christening']['date']
        max_age = 75
        if date.year > 1900:
            max_age = 100
        date = datetime.datetime(date.year+max_age, 12, 31)
        individual.events['death_or_burial'] = {
            'tag_name': 'None',
            'date': date,
            'ordinal_value': date.toordinal(),
            'comment': f'Estimated (max age {max_age})'
        }
        if date > datetime.datetime.now():
            individual.events['death_or_burial']['date'] = datetime.datetime.now()
            individual.events['death_or_burial']['ordinal_value'] = datetime.datetime.now(
            ).toordinal()
            individual.events['death_or_burial']['comment'] = 'Still alive'


def estimate_birth_date(individual, instances):
    """
    if the birth date is unknown, then estimate the birth date by assuming:
        - the birth took place at one year after the marriage
        - the individual was 25 on his/hers first marriage
        - the individual died with the maximum age of 75

    Args:
        individual (BaseIndividual): individual instance
        instances (InstanceContainer): instance container to get family information
    """
    if individual.events['birth_or_christening'] is None:
        # parents marriage
        for family_id in individual.child_of_family_id:
            parents_marriage = instances[('f', family_id)]
            if parents_marriage.marriage:
                if not individual.events['birth_or_christening'] or individual.events['birth_or_christening']['ordinal_value'] < parents_marriage.marriage['ordinal_value']:
                    if individual.events['birth_or_christening'] and individual.events['birth_or_christening']['ordinal_value'] < parents_marriage.marriage['ordinal_value']:
                        date = deepcopy(parents_marriage.marriage['date'])
                    else:
                        date = deepcopy(parents_marriage.marriage['date'])
                    date = datetime.datetime(
                        date.year, date.month, date.day, 0, 0, 0)
                    individual.events['birth_or_christening'] = {
                        'tag_name': 'MARR',
                        'comment': 'Estimated (min 1 after parents marriage)',
                        'date': date,
                        'ordinal_value': date.toordinal()
                    }
        if individual.events['birth_or_christening']:
            date = individual.events['birth_or_christening']['date']
            individual.events['birth_or_christening']['date'] = datetime.datetime(
                date.year+1, date.month, date.day, 0, 0, 0)
            individual.events['birth_or_christening']['ordinal_value'] = date.toordinal(
            )
    if individual.events['birth_or_christening'] is None:
        # at least 15 at marriage
        for marriage in individual.marriages:
            if marriage.marriage:
                if not individual.events['birth_or_christening'] or individual.events['birth_or_christening']['ordinal_value'] < marriage.marriage['ordinal_value']:
                    if individual.events['birth_or_christening'] and individual.events['birth_or_christening']['ordinal_value'] < marriage.marriage['ordinal_value']:
                        date = deepcopy(marriage.marriage['date'])
                    else:
                        date = deepcopy(marriage.marriage['date'])
                    date = datetime.datetime(
                        date.year, date.month, date.day, 0, 0, 0)
                    individual.events['birth_or_christening'] = {
                        'tag_name': 'MARR',
                        'comment': 'Estimated (min 25 at marriage)',
                        'date': date,
                        'ordinal_value': date.toordinal()
                    }
        if individual.events['birth_or_christening'] and individual.events['birth_or_christening']['date'].year > 25:
            date = individual.events['birth_or_christening']['date']
            individual.events['birth_or_christening']['date'] = datetime.datetime(
                date.year-25, 1, 1, 0, 0, 0)
            individual.events['birth_or_christening']['ordinal_value'] = individual.events['birth_or_christening']['date'].toordinal()
    if individual.events['birth_or_christening'] is None and not individual.events['death_or_burial'] is None:
        # max 75 years, so in birth can be estimated
        if 'death_or_burial' in individual.events:
            date = individual.events['death_or_burial']['date']
            date = datetime.datetime(date.year-75, 1, 1)
            individual.events['birth_or_christening'] = {
                'tag_name': 'None',
                'date': date,
                'ordinal_value': date.toordinal(),
                'comment': 'Estimated (max age 75)'
            }


class BaseIndividual():
    """
    Base class for individuals. This class is used as interface to the database.
    """

    def __init__(self, instances, individual_id):
        self._instances = instances
        self.individual_id = individual_id
        self._marriage_family_ids = []
        self.marriages = []
        self.child_of_family_id = []
        self.events = {}  # : events like birth or death
        self.graphical_representations = [] # : instances of graphical representations
        self.images = {}  # : mapping of ordinal values to photos of this individual

    def __repr__(self):
        return 'individual "' + self.plain_name + '" ' + self.birth_date

    def _initialize(self):
        self._marriage_family_ids = self._get_marriage_family_ids()
        unsorted_marriages = [
            self._instances[('f', m)] for m in self._marriage_family_ids]
        sorted_pairs = zip([(m.marriage['ordinal_value'], i) if m.marriage else (
            0, i) for i, m in enumerate(unsorted_marriages)], unsorted_marriages)
        self.marriages = [m for ov, m in sorted(sorted_pairs)]

    def __lt__(self, other):
        """
        Sorting by name

        Args:
            other (BaseIndividual): the other instance

        Returns:
            bool: is less than
        """
        return self.plain_name < other.plain_name

    def _get_name(self):
        if True:
            raise NotImplementedError()
        return ""
    name = property(_get_name)

    def _get_plain_name(self):
        return ' '.join([n.strip() for n in self.name if n.strip() != ''])
    plain_name = property(_get_plain_name)

    def _get_children(self):
        """
        get the all children of this individual (all marriages)

        Returns:
            list: list of children individuals
        """
        children = []
        for m in self.marriages:
            children += m.children
        return children
    children = property(_get_children)

    def _get_birth_date(self):
        """
        get the birth (or christening or baptism) date

        Returns:
            str: birth date string
        """
        if self.events['birth_or_christening']:
            return self.events['birth_or_christening']['date'].date().strftime('%d.%m.%Y')
        else:
            return None
    birth_date = property(_get_birth_date)

    def _get_birth_label(self):
        """
        get the birth label used for displaying

        Returns:
            str: birth label
        """
        string = ''
        if self.events['birth_or_christening']:
            event = self.events['birth_or_christening']
            if event['comment']:
                string = self._instances.date_label_translation[event['comment']].format(
                    symbol='*', date=str(event['date'].date().year))
                # string += ' ' + self.events['birth_or_christening']['comment']
            else:
                string += '*\xa0' + event['date'].date().strftime('%d.%m.%Y')
        return string
    birth_label = property(_get_birth_label)

    def _get_death_label(self):
        """
        get death label used for displaying

        Returns:
            str: death label
        """
        string = ''
        if self.events['death_or_burial']:
            event = self.events['death_or_burial']
            if event['comment']:
                string = self._instances.date_label_translation[event['comment']].format(
                    symbol='\u2020', date=str(event['date'].date().year))
                # string += ' ' + self.events['birth_or_christening']['comment']
            else:
                string += '\u2020\xa0' + event['date'].date().strftime('%d.%m.%Y')
        return string
    death_label = property(_get_death_label)

    def _get_death_date(self):
        """
        get the death (or burial) date

        Returns:
            str: death date
        """
        if self.events['death_or_burial']:
            return self.events['death_or_burial']['date'].date().strftime('%d.%m.%Y')
        else:
            return None
    death_date = property(_get_death_date)

    def _get_info_text(self):
        content = [
            " ".join([n.strip() for n in self.name if n != '']).strip(),
            self.birth_label,
            self.death_label,
            '',
        ]
        for father, mother in self.get_father_and_mother():
            if father:
                content.append('Vater: {} ({})'.format(self.get_father_and_mother()[
                               0][0].plain_name, self.get_father_and_mother()[0][0].birth_label))
            if mother:
                content.append('Mutter: {} ({})'.format(self.get_father_and_mother()[
                               0][1].plain_name, self.get_father_and_mother()[0][1].birth_label))

        content.append('')
        for marriage in self.marriages:
            spouse = marriage.get_spouse(self.individual_id)
            content.append('Partner: {} ({}), Heirat: {}'.format(
                spouse.plain_name, spouse.birth_label, marriage.label))
            for index, child in enumerate(marriage.get_sorted_children()):
                content.append(' {}. Kind: {} ({})'.format(
                    index + 1, child.plain_name, child.birth_label))

        return '\n'.join(content)
    info_text = property(_get_info_text)

    def _get_short_info_text(self):
        content = [
            " ".join([n.strip() for n in self.name if n != '']).strip(),
            self.birth_label,
            self.death_label,
        ]
        return '\n'.join(content)
    short_info_text = property(_get_short_info_text)

    def _get_father_and_mother(self):
        if True:
            raise NotImplementedError()
        return ()

    def has_marriages(self):
        return len(self._marriage_family_ids) > 0

    def get_father_and_mother(self):
        return [self._instances[('f', family_id)].get_husband_and_wife() for family_id in self.child_of_family_id]

    def get_child_of_family(self):
        return [self._instances[('f', family_id)] for family_id in self.child_of_family_id]
    child_of_family = property(get_child_of_family)

    def has_graphical_representation(self):
        return len(self.graphical_representations) > 0

    def _get_marriage_family_ids(self):
        if True:
            raise NotImplementedError()
        return []
