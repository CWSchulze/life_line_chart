"""
Life Line Chart Module
======================

This module can be used to generate genealogy charts.
"""

import logging

from .BaseChart import BaseChart
from .AncestorChart import AncestorChart
from .DescendantChart import DescendantChart

from .GraphicalIndividual import GraphicalIndividual
from .GraphicalFamily import GraphicalFamily

from .BaseFamily import BaseFamily
from .BaseIndividual import BaseIndividual, estimate_birth_date, estimate_death_date

from .InstanceContainer import InstanceContainer

# from .GedcomParsing import get_date_dict_from_tag, estimate_marriage_date, get_gedcom_instance_container

from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected, LifeLineChartNotEnoughInformationToDisplay

__version__ = "1.5.0"

logging.basicConfig()
logger = logging.getLogger("life_line_chart")
logger.setLevel(logging.FATAL)

