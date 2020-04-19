from copy import deepcopy
import datetime
from dateutil.parser import parse


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
        content = parent_item[tag_name]['DATE']['tag_data']
        comment = None
        if content.startswith('EST'):
            comment = 'Estimated'
            content = content[4:]
        if content.startswith('ABT'):
            comment = 'About'
            content = content[4:]
        if content.startswith('CAL'):
            comment = 'Calculated'
            content = content[4:]
        if content.startswith('AFT'):
            comment = 'After'
            content = content[4:]
        if content.startswith('BEF'):
            comment = 'Before'
            content = content[4:]
        if content.isnumeric():
            try:
                test = int(content)
                if tag_name in ['BURI', 'DEAT']:
                    date = datetime.datetime(test, 12, 31, 0, 0, 0, 0)
                else:
                    date = datetime.datetime(test, 1, 1, 0, 0, 0, 0)
                if comment is None:
                    comment = 'YearPrecision'
            except:
                date = parse(content)
            return {
                'tag_name': tag_name,
                'date': date,
                'ordinal_value': date.toordinal(),
                'comment': comment
            }
        else:
            try:
                date = parse(content.split('\n')[0])
                return {
                    'tag_name': tag_name,
                    'date': date,
                    'ordinal_value': date.toordinal(),
                    'comment': comment
                }
            except:
                pass
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
