import os
from .SimpleSVGItems import Line, Path, CubicBezier
import logging
import datetime
import svgwrite
from copy import deepcopy
from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected
#from cmath import sqrt, exp, pi
from math import floor, ceil, sqrt, exp, pi
from .BaseSVGChart import BaseSVGChart

logger = logging.getLogger("life_line_chart")


class DescendantChart(BaseSVGChart):
    """
    Descendant Chart
    ================

    The descendant chart shows the descendants of one or more root individuals.
    The parents enclose direct children. Both, father and mother are visible.

    Each individual appears once. So in case of a second marriage, the
    individual is connected across the chart to the second spouse. Because
    of that, ancestor collapse is visualized.
    """

    DEFAULT_CHART_CONFIGURATION = {
            'root_individuals': [],
            'discovery_blacklist': []
    }
    DEFAULT_CHART_CONFIGURATION.update(BaseSVGChart.DEFAULT_CHART_CONFIGURATION)


    def __init__(self, positioning=None, formatting=None, instance_container=None):
        BaseSVGChart.__init__(self, positioning, formatting, instance_container)

        # configuration of this chart
        self._chart_configuration.update(DescendantChart.DEFAULT_CHART_CONFIGURATION)

    def select_descendants(self, individual, generations=None, color=None, filter=None):
        """
        create graphical representations for all descendants.

        Args:
            individual (BaseIndividual): parent individual
            generations (int, optional): number of generations to go deeper. Defaults to None.
            color (tuple, optional): RGB value of the individuals. Defaults to None.
            filter (lambda, optional): filter for individuals. Defaults to None.
        """
        if filter and filter(individual):
            return

        if not individual.has_graphical_representation():
            gr_individual = self._create_individual_graphical_representation(
                individual)

            if gr_individual is None:
                return

            if color is None:
                gr_individual.color = self._instances.color_generator(individual)
            else:
                gr_individual.color = color
        else:
            gr_individual = individual.graphical_representations[0]

        for marriage in individual.marriages:
            if marriage.has_graphical_representation():
                continue

            #gr_individual.visible_parent_family = gr_marriage
            if generations > 0 or generations < 0:
                gr_marriage = self._create_family_graphical_representation(
                    marriage)

                spouse = marriage.get_spouse(individual.individual_id)
                if spouse is not None and not spouse.has_graphical_representation():
                    if filter is None or filter(spouse) == False:
                        gr_spouse = self._create_individual_graphical_representation(
                            spouse)

                        if gr_spouse is not None:
                            if color is None:
                                gr_spouse.color = self._instances.color_generator(spouse)
                            else:
                                gr_spouse.color = color

                for child in marriage.children:
                    self.select_descendants(
                        child, generations - 1, filter=filter)
                    if child.has_graphical_representation():
                        gr_marriage.add_visible_children(child)
                        child.graphical_representations[0].visible_parent_family = gr_marriage
                cofs = individual.child_of_families
                if len(cofs) > 0:
                    gr_marriage.visual_placement_parent_family = individual.child_of_families[0]

    def place_selected_individuals(self, individual, child_of_family, x_offset=0, discovery_cache=[]):
        """
        Place the graphical representations in direction of x

        Args:
            individual (BaseIndividual): individual
            child_of_family (BaseFamily): child-of-family of this individual
        """
        discovery_cache.append(individual.plain_name)

        logger.info(f"discovering {individual.plain_name}")
        if not individual.has_graphical_representation():
            return
        x_position = x_offset
        gr_individual = individual.graphical_representations[0]
        self.min_x_index = min(self.min_x_index, x_position)

        visible_marriages = \
            [marriage for marriage in individual.marriages \
                if marriage.has_graphical_representation() and (child_of_family is None or \
                    marriage.graphical_representations[0].visual_placement_parent_family.family_id == child_of_family.family_id)]


        if len(visible_marriages) == 0:
            gr_individual.set_x_position(
                    x_position, child_of_family, True)
            x_position += 1

        for marriage_index, marriage in enumerate(reversed(visible_marriages)):
            if not marriage.has_graphical_representation():
                continue

            if marriage_index == len(visible_marriages) - 1:
                if gr_individual.get_x_position() is None or \
                        child_of_family is not None and child_of_family.family_id not in gr_individual.get_x_position():
                    gr_individual.set_x_position(
                        x_position, child_of_family)

            if gr_individual.get_x_position() is None or \
                    marriage.family_id not in gr_individual.get_x_position():
                gr_individual.set_x_position(
                    x_position, marriage)
                x_position += 1


            for child in marriage.children:
                self.place_selected_individuals(
                    child, marriage, x_position,
                    discovery_cache=discovery_cache)
                if child.has_graphical_representation():
                    width = child.graphical_representations[0].get_width2(
                        marriage)
                    x_position += width

            spouse = marriage.get_spouse(individual.individual_id)
            if spouse is not None and spouse.has_graphical_representation():
                gr_spouse = spouse.graphical_representations[0]
                if not gr_spouse.get_x_position() or marriage.family_id not in gr_spouse.get_x_position():
                    gr_spouse.set_x_position(
                        x_position, marriage)
                    x_position += 1

        self.max_x_index = max(self.max_x_index, x_position)

        # recalculate
        birth_ordinal_value = gr_individual.get_birth_date_ov()
        death_ordinal_value = gr_individual.get_death_date_ov()
        if self.min_ordinal is not None and self.max_ordinal is not None:
            self.min_ordinal = min(self.min_ordinal, birth_ordinal_value)
            self.max_ordinal = max(self.max_ordinal, death_ordinal_value)
        elif death_ordinal_value and birth_ordinal_value:
            self.min_ordinal = birth_ordinal_value
            self.max_ordinal = death_ordinal_value

    def modify_layout(self, root_individual_id):
        """
        improvement of individual placement.

        Args:
            root_individual_id (str): root individual id used as root node for compression
        """
        self.check_unique_x_position(False)
        _, _, _, self.position_to_person_map = self._check_compressed_x_position(
                False)

    def update_chart(self, filter_lambda=None, color_lambda=None, images_lambda=None, rebuild_all=False, update_view=False):
        rebuild_all = rebuild_all or self._positioning != self._backup_positioning or \
            self._chart_configuration != self._backup_chart_configuration
        update_view = update_view or rebuild_all or self._formatting != self._backup_formatting
        def local_filter_lambda(individual, _filter_lambda=filter_lambda):
            if individual.individual_id in self._chart_configuration['discovery_blacklist']:
                return True
            if _filter_lambda is not None:
                return _filter_lambda(individual)
            return False

        if rebuild_all:
            self.clear_graphical_representations()
            for settings in self._chart_configuration['root_individuals']:
                root_individual_id = settings['individual_id']
                generations = settings['generations']
                root_individual = self._instances[(
                    'i', root_individual_id)]
                self.select_descendants(root_individual, generations, filter=local_filter_lambda)

            x_pos = 0
            for settings in self._chart_configuration['root_individuals']:
                root_individual_id = settings['individual_id']
                generations = settings['generations']
                root_individual = self._instances[(
                    'i', root_individual_id)]
                cof_family_id = None
                if root_individual.child_of_family_id:
                    cof_family_id = root_individual.child_of_family_id[0]
                self.place_selected_individuals(
                    root_individual, self._instances[('f', cof_family_id)], x_pos)

                x_pos += root_individual.graphical_representations[0].get_width2(self._instances[('f', cof_family_id)])

            for settings in self._chart_configuration['root_individuals']:
                root_individual_id = settings['individual_id']
                generations = settings['generations']
                try:
                    self.modify_layout(root_individual_id)
                except Exception as e:
                    pass

            #backup color
            for gir in self.graphical_individual_representations:
                gir.color_backup = gir.color

            for gir in self.graphical_individual_representations:
                gir.color = gir.color_backup
                if color_lambda:
                    color = color_lambda(gir.individual_id)
                    if color:
                        gir.color = color
                if images_lambda:
                    gir.individual.images = images_lambda(gir.individual.individual_id)

            self.define_svg_items()

        elif update_view:
            self.clear_svg_items()

            for gir in self.graphical_individual_representations:
                gir.color = gir.color_backup
                if color_lambda:
                    color = color_lambda(gir.individual_id)
                    if color:
                        gir.color = color
                if images_lambda:
                    gir.individual.images = images_lambda(gir.individual.individual_id)
            self.define_svg_items()
        self._backup_chart_configuration = deepcopy(self._chart_configuration)
        self._backup_formatting = deepcopy(self._formatting)
        self._backup_positioning = deepcopy(self._positioning)
        return update_view or rebuild_all
