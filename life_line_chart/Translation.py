"""
Translation
===========

This is a collection of methods to translate or simply update strings stored in a dict.

To add a new language just add a top-level dict in the json files and import one of the Charts.
The new language will be filled with all available strings, so the structure is aligned with the
default language.

If googletrans is available, the strings will also be translated.
"""

import os
from copy import deepcopy
import logging
import json

logger = logging.getLogger("life_line_chart")

def translate_strings(data, source_language='en_EN.UTF-8', destination_language='de_DE.UTF-8', translator=None):
    """
    automatic translation of strings in a dict

    Args:
        data (dict or str): data to translate
        source_language (str, optional): source language. Defaults to 'en_EN.UTF-8'.
        destination_language (str, optional): destination language. Defaults to 'de_DE.UTF-8'.
        translator (googletrans.Translator, optional): for caching of the instance. Defaults to None.

    Returns:
        dict or str: translated object
    """
    if not translator:
        try:
            import googletrans
            translator = googletrans.Translator()
        except ImportError:
            logger.warning('Failed to load googletans module during automatic string translation')
            return data

    if type(data) == str:
        return translator.translate(data, src=source_language, dest=destination_language).text
    elif type(data) == dict:
        for k, v in data.items():
            data[k] = translate_strings(v, source_language, destination_language)
    return data

def recursive_merge_dict_members(a, b, translate_function=None, remove_unknown_keys=True):
    """
    merge b into reference a, return merged dict

    Args:
        a (dict): dict a is target
        b (dict): dict b is source
        translate_function (lambda, optional): function that translates strings. If none is
                                               provided, nothing will be translated. Defaults to None.

    Returns:
        dict: merged dict
    """
    changed = False
    c = {}
    b_key_list = list(b.keys())
    for a_index, (k, v) in enumerate(a.items()):
        b_index = b_key_list.index(k) if k in b_key_list else None
        if b_index is None:
            c[k] = deepcopy(v)
            if translate_function:
                c[k] = translate_function(c[k])
            changed = True
        else:
            changed = changed or b_index != a_index
            if type(v) == dict:
                sub_changed, sub_dict = recursive_merge_dict_members(v, b[k], translate_function, remove_unknown_keys)
                changed =  sub_changed or changed
                c[k] = sub_dict
            else:
                c[k] = deepcopy(b[k])
    if not remove_unknown_keys:
        for k in b_key_list:
            if k not in c:
                c[k] = deepcopy(b[k])
    return changed, c

def get_strings(class_name, default_language='en_US.UTF-8'):
    """
    Read strings from file and fill missing translations

    Args:
        class_name (str): name of the class (used as filename)
    """
    strings = {}
    with open(os.path.join(os.path.dirname(__file__), class_name + 'Strings.json'),'r',encoding='utf-8') as f:
        strings = json.load(f)


    changed = {}
    for lang, data in strings.items():
        if lang != default_language:
            changed[lang], strings[lang] = recursive_merge_dict_members(
                strings[default_language],
                data,
                lambda data, source=default_language, destination=lang:
                    translate_strings(data, source, destination))

    if any(changed.values()):
        # auto update string file!
        logger.warn('Updating string file.')
        file_content = json.dumps(strings, indent=4)
        with open(os.path.join(os.path.dirname(__file__), class_name + 'Strings.json'),'w',encoding='utf-8') as f:
            f.write(file_content)

    return strings

