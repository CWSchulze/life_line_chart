
import os
from copy import deepcopy
import logging
import json

logger = logging.getLogger("life_line_chart")


def recursive_merge_dict_members(a, b, c=None):
    """
    merge b into reference a, return merged dict
    """
    changed = False
    if c == None:
        c = {}
    for k, v in a.items():
        if k in b:
            if type(v) == dict:
                changed, sub_dict = recursive_merge_dict_members(v, b[k]) or changed
                c[k] = sub_dict
            else:
                c[k] = deepcopy(b[k])
        else:
            c[k] = deepcopy(v)
            changed = True
    return changed, c

def get_strings(class_name, default_language='en_US.UTF-8'):
    """
    Read strings from file and fill missing translations

    Args:
        class_name (str): name of the class (used as filename)
    """
    strings = {}
    with open(os.path.join(os.path.dirname(__file__), class_name + 'Strings.json'),'r') as f:
        strings = json.load(f)


    changed = {}
    for lang, data in strings.items():
        if lang != default_language:
            changed[lang], strings[default_language] = recursive_merge_dict_members(strings[default_language], data)

    if any(changed.values()):
        # auto update string file!
        logger.warn('Updating string file.')
        file_content = json.dumps(strings, indent=4)
        with open(os.path.join(os.path.dirname(__file__), class_name + 'Strings.json'),'w') as f:
            f.write(file_content)

    return strings

