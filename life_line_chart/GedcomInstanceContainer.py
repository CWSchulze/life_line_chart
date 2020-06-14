import os
import logging
import json

from .GedcomIndividual import GedcomIndividual
from .GedcomFamily import GedcomFamily
from .ReadGedcom import read_data
from .InstanceContainer import InstanceContainer

logging.basicConfig()  # level=20)
logger = logging.getLogger("life_line_chart")


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
                try:
                    self[('f', family_id)] = GedcomFamily(
                        self, database_fam, database_indi, family_id)
                except:
                    pass
        for individual_id in list(database_indi.keys()):
            if not ('i', individual_id) in self:
                try:
                    self[('i', individual_id)] = GedcomIndividual(
                        self, database_fam, database_indi, individual_id)
                except:
                    pass

    logger.debug('start creating instances')
    return InstanceContainer(
        lambda self, key: GedcomFamily(
            self, database_fam, database_indi, key[1]),
        lambda self, key: GedcomIndividual(
            self, database_fam, database_indi, key[1]),
        lambda self: instantiate_all(self, database_fam, database_indi))