import datetime
import re
import os
import logging
import json
from .GedcomIndividual import GedcomIndividual
from .GedcomFamily import GedcomFamily
from .ReadGedcom import read_data
from .InstanceContainer import InstanceContainer

logging.basicConfig()  # level=20)
logger = logging.getLogger("life_line_chart")


_months = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC"
]
_precision = [
    'ABT',
    'CAL',
    'EST',
    'AFT',
    'BEF'
]
_date_expr = re.compile('(?:(' + '|'.join(_precision) + ') )?(?:(\\d+) )?(?:(' + '|'.join(_months) + ') )?(\\d{4})')
_interval_expr = re.compile('(BET) (?:(\\d+) (' + '|'.join(_months) + ') )?(\\d{4}) AND (?:(\\d+) (' + '|'.join(_months) + ') )?(\\d{4})')

def get_date_dict_from_tag(parent_item, tag_name):
    """
    read the date from a gedcom tag

    Args:
        parent_item (dict): parent event node to output the result
        tag_name (str): event type
    """

    # TODO: Implement BET = Between
    try:
        if tag_name not in parent_item:
            return
        if 'DATE' not in parent_item[tag_name]:
            return
        comment = None
        content = parent_item[tag_name]['DATE']['tag_data']
        date_info = _date_expr.match(content)
        if date_info is None:
            date_info = _interval_expr.match(content)
        if date_info.group(1) == 'EST':
            comment = 'Estimated'
        elif date_info.group(1) == 'ABT':
            comment = 'About'
        elif date_info.group(1) == 'CAL':
            comment = 'Calculated'
        elif date_info.group(1) == 'AFT':
            comment = 'After'
        elif date_info.group(1) == 'BEF':
            comment = 'Before'
        elif date_info.group(2) is None and date_info.group(3) is None and date_info.group(4) is not None:
            comment = 'YearPrecision'

        if tag_name in ['BURI', 'DEAT']:
            # if unknown move to the end of the year
            month, day = 12, 31
        else:
            # if unknown move to the beginning of the year
            month, day = 1, 1

        if date_info.group(1) == 'BET' and tag_name in ['BURI', 'DEAT']:
            # move to the end of the interval
            if date_info.group(5):
                day = int(date_info.group(5))
            if date_info.group(6):
                month = _months.index(date_info.group(6)) + 1
            if date_info.group(7):
                year = int(date_info.group(7))
        else:
            if date_info.group(2):
                day = int(date_info.group(2))
            if date_info.group(3):
                month = _months.index(date_info.group(3)) + 1
            if date_info.group(4):
                year = int(date_info.group(4))

        date = datetime.datetime(year, month, day, 0, 0, 0, 0)
        return {
            'tag_name': tag_name,
            'date': date,
            'ordinal_value': date.toordinal(),
            'comment': comment
        }

    except:
        pass


def _get_relevant_events(database_indi, individual_id, target):
    parent_item = database_indi[individual_id].get('BIRT')
    if parent_item:
        target['birth'] = get_date_dict_from_tag(
            database_indi[individual_id], 'BIRT')
        if target['birth'] is None:
            target.pop('birth')
    parent_item = database_indi[individual_id].get('CHR')
    if parent_item:
        target['christening'] = get_date_dict_from_tag(
            database_indi[individual_id], 'CHR')
        if target['christening'] is None:
            target.pop('christening')
    parent_item = database_indi[individual_id].get('BAPM')
    if parent_item:
        target['baptism'] = get_date_dict_from_tag(
            database_indi[individual_id], 'BAPM')
        if target['baptism'] is None:
            target.pop('baptism')
    parent_item = database_indi[individual_id].get('DEAT')
    if parent_item:
        target['death'] = get_date_dict_from_tag(
            database_indi[individual_id], 'DEAT')
        if target['death'] is None:
            target.pop('death')
    parent_item = database_indi[individual_id].get('BURI')
    if parent_item:
        target['burial'] = get_date_dict_from_tag(
            database_indi[individual_id], 'BURI')
        if target['burial'] is None:
            target.pop('burial')

    if 'birth' in target:
        target['birth_or_christening'] = target['birth']
    elif 'birth_or_christening' not in target and 'christening' in target:
        target['birth_or_christening'] = target['christening']
    elif 'birth_or_christening' not in target and 'baptism' in target:
        target['birth_or_christening'] = target['baptism']
    else:
        target['birth_or_christening'] = None

    if 'death' in target:
        target['death_or_burial'] = target['death']
    elif 'death_or_burial' not in target and 'burial' in target:
        target['death_or_burial'] = target['burial']
    else:
        target['death_or_burial'] = None


def estimate_marriage_date(family):
    """
    If the marriage date is unknown, then estimate the date by assuming:
        - the marriage took place before the first child was born

    Args:
        family (BaseFamily): family instance
    """
    if family.marriage is None:
        children_events = []
        for child in family.children_individual_ids:
            child_events = {}
            _get_relevant_events(family._database_indi, child, child_events)
            if child_events['birth_or_christening']:
                children_events.append(child_events['birth_or_christening'])

        # unsorted_marriages = [family._instances[('f',m)] for m in family._marriage_family_ids]
        if len(children_events) > 0:
            sorted_pairs = list(zip([(m['ordinal_value'], i) for i, m in enumerate(
                children_events)], children_events))
            sorted_pairs.sort()
            family.marriage = sorted_pairs[0][1]


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
