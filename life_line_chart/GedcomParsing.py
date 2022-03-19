import datetime
import re


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
    1: 31,
    2: 29,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31
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
        elif date_info.group(1) == 'BET':
            comment = 'Between'
        elif date_info.group(2) is None and date_info.group(3) is None and date_info.group(4) is not None:
            comment = 'YearPrecision'

        month_max_, day_max_ = 12, 31
        month_min_, day_min_ = 1, 1
        year_min, year_max = None, None
        month_max, day_max = None, None
        month_min, day_min = None, None

        if date_info.group(1) == 'BET':
            if date_info.group(7):
                year_max = int(date_info.group(7))
            if date_info.group(6):
                month_max = _months.index(date_info.group(6)) + 1
            if date_info.group(5):
                day_max = int(date_info.group(5))

        if date_info.group(4):
            year_min = int(date_info.group(4))
            if not year_max:
                year_max = year_min
            precision = 'y' + precision
        if date_info.group(3):
            month_min = _months.index(date_info.group(3)) + 1
            if not month_max:
                month_max = month_min
            precision = 'm' + precision
        if date_info.group(2):
            day_min = int(date_info.group(2))
            if not day_max:
                day_max = day_min
            precision = 'd' + precision

        if date_info.group(1) == 'AFT':
            year_max = year_min + 15
        elif date_info.group(1) == 'BEF':
            year_min = year_max - 15

        if not month_max:
            month_max = month_max_
        if not month_min:
            month_min = month_min_
        if not day_max:
            day_max = day_max_
        if not day_min:
            day_min = day_min_

        day_max = min(_max_days[month_max], day_max)

        date_min = datetime.datetime(year_min, month_min, day_min, 0, 0, 0, 0)
        try:
            date_max = datetime.datetime(year_max, month_max, day_max, 0, 0, 0, 0)
        except ValueError:
            if month_max == 2:
                date_max = datetime.datetime(year_max, month_max, day_max, 0, 0, 0, 0)
            else:
                raise

        if tag_name in ['BURI', 'DEAT']:
            # if unknown move to the end of the year
            date = date_max
        else:
            # if unknown move to the beginning of the year
            date = date_min

        return {
            'tag_name': tag_name,
            'date': date,
            'ordinal_value': date.toordinal(),
            'ordinal_value_max': date_max.toordinal(),
            'ordinal_value_min': date_min.toordinal(),
            'comment': comment,
            'precision': precision
        }

    except Exception:
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
