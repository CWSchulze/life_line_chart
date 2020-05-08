# import pytest
from life_line_chart import GedcomParsing, InstanceContainer, GedcomIndividual, ancestor_graph_individual, ancestor_graph_family, GedcomFamily
from life_line_chart import ReadGedcom, get_gedcom_instance_container
import os


def test_instance_container_load():
    instances = get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'gramps_sample.ged'))

    assert len(instances._data) == 2
    # autocreate
    i = instances[('i', '@I1@')]
    assert len(instances._data) == 3
    assert i.plain_name == 'Keith Lloyd Smith'

    f = instances[('f', '@F1@')]
    assert len(instances._data) == 4
    assert f.wife_individual_id == '@I25@'
    assert f.husband_individual_id == '@I27@'

    # asking does not instantiate
    assert not ('i', '@I2@') in instances

    # load all
    instances.instantiate_all(instances)
    assert len(instances._data) == 59

    assert ('i', '@I2@') in instances

    # get all individuals
    individuals = [instance for key,
                   instance in instances.items() if key[0] == 'i']
    assert len(individuals) == 42


def test_instance_container_labels():
    instances = get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'gramps_sample.ged'))

    # load all
    instances.instantiate_all(instances)
    assert len(instances._data) == 59

    # get all individuals
    individual_plain_names = [instance.plain_name for key,
                              instance in instances.items() if key[0] == 'i']
    individual_birth_labels = [
        instance.birth_label for key, instance in instances.items() if key[0] == 'i']
    individual_death_labels = [
        instance.death_label for key, instance in instances.items() if key[0] == 'i']
    assert str(
        individual_plain_names[1:5]) == "['Keith Lloyd Smith', 'Hans Peter Smith', 'Hanna Smith', 'Herman Julius Nielsen']"
    assert str(
        individual_birth_labels[1:5]) == "['*\\u200911.08.1966', '*\\u200917.04.1904', '*\\u200929.01.1821', '*\\u200931.08.1889']"
    assert str(
        individual_death_labels[1:5]) == "['', '†\\u200929.01.1977', '†\\u2009geschätzt\\u20091896', '†\\u20091945']"
