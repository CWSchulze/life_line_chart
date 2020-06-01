import datetime
import re
import os
import logging
import json




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
_max_days = {
    1:31,
    2:29,
    3:31,
    4:30,
    5:31,
    6:30,
    7:31,
    8:31,
    9:30,
    10:31,
    11:30,
    12:31
}

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
        precision = ''
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
                precision += 'd'
            if date_info.group(6):
                month = _months.index(date_info.group(6)) + 1
                precision += 'm'
            if date_info.group(7):
                year = int(date_info.group(7))
                precision += 'y'
        else:
            if date_info.group(2):
                day = int(date_info.group(2))
                precision += 'd'
            if date_info.group(3):
                month = _months.index(date_info.group(3)) + 1
                precision += 'm'
            if date_info.group(4):
                year = int(date_info.group(4))
                precision += 'y'

        try:
            date = datetime.datetime(year, month, min(_max_days[month], day), 0, 0, 0, 0)
        except ValueError as e:
            if month==2:
                date = datetime.datetime(year, month, min(_max_days[month]-1, day), 0, 0, 0, 0)
            else:
                raise


        return {
            'tag_name': tag_name,
            'date': date,
            'ordinal_value': date.toordinal(),
            'comment': comment,
            'precision' : precision
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

