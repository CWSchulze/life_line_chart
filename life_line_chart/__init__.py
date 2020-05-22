"""
Life Line Chart Module
======================

This module can be used to generate genealogy charts.
"""

from .BaseGraph import BaseGraph
from .AncestorGraph import AncestorGraph
from .DescendantGraph import DescendantGraph

from .AncestorGraphIndividual import ancestor_graph_individual
from .AncestorGraphFamily import ancestor_graph_family

from .BaseFamily import BaseFamily
from .BaseIndividual import BaseIndividual, estimate_birth_date, estimate_death_date
from .GedcomIndividual import GedcomIndividual
from .GedcomFamily import GedcomFamily

from .InstanceContainer import InstanceContainer, get_gedcom_instance_container

from .GedcomParsing import get_date_dict_from_tag, estimate_marriage_date

from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected, LifeLineChartNotEnoughInformationToDisplay

__version__ = "1.3.0"

import logging
logging.basicConfig()
logger = logging.getLogger("life_line_chart")
logger.setLevel(logging.FATAL)

