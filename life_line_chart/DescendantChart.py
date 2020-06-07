import os
from .SimpleSVGItems import Line, Path, CubicBezier
import logging
import datetime
import svgwrite
from copy import deepcopy
from .BaseSVGChart import BaseSVGChart
from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected
from .Translation import get_strings, recursive_merge_dict_members

logger = logging.getLogger("life_line_chart")

_strings = get_strings('DescendantChart')
_, _strings = recursive_merge_dict_members(BaseSVGChart.SETTINGS_DESCRIPTION, _strings, remove_unknown_keys=False)


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

    DEFAULT_FORMATTING = {
        'highlight_descendants': False,
    }
    DEFAULT_FORMATTING.update(BaseSVGChart.DEFAULT_FORMATTING)

    DEFAULT_CHART_CONFIGURATION = {
            'root_individuals': [],
            'discovery_blacklist': []
    }
    DEFAULT_CHART_CONFIGURATION.update(BaseSVGChart.DEFAULT_CHART_CONFIGURATION)

    SETTINGS_DESCRIPTION = _strings

    def __init__(self, positioning=None, formatting=None, instance_container=None):
        BaseSVGChart.__init__(self, positioning, formatting, instance_container)

        # configuration of this chart
        self._chart_configuration.update(DescendantChart.DEFAULT_CHART_CONFIGURATION)

    def select_descendants(self, individual, generations=None, filter=None):
        """
        create graphical representations for all descendants.

        Args:
            individual (BaseIndividual): parent individual
            generations (int, optional): number of generations to go deeper. Defaults to None.
            filter (lambda, optional): filter for individuals. Defaults to None.
        """
        if filter and filter(individual):
            return

        if not individual.has_graphical_representation():
            gr_individual = self._create_individual_graphical_representation(
                individual)

            if gr_individual is None:
                return
        else:
            logger.warning('why this?')
            gr_individual = individual.graphical_representations[-1]

        for marriage in individual.marriages:
            if marriage.has_graphical_representation():
                continue

            if generations > 0 or generations < 0:
                gr_marriage = self._create_family_graphical_representation(
                    marriage)

                if gr_marriage.husb == individual:
                    gr_marriage.gr_husb = gr_individual
                else:
                    gr_marriage.gr_wife = gr_individual

                spouse = marriage.get_spouse(individual.individual_id)
                if spouse is not None and not spouse.has_graphical_representation():
                    if filter is None or filter(spouse) == False:
                        gr_spouse = self._create_individual_graphical_representation(
                            spouse)

                    if gr_marriage.husb == spouse:
                        gr_marriage.gr_husb = gr_spouse
                    else:
                        gr_marriage.gr_wife = gr_spouse

                for child in marriage.children:
                    gr_child = self.select_descendants(
                        child, generations - 1, filter=filter)
                    if gr_child:
                        gr_marriage.add_visible_children(gr_child)
                        #gr_child.strongly_connected_parent_family = gr_marriage
                cofs = individual.child_of_families
                if len(cofs) > 0:
                    gr_marriage.visual_placement_parent_family = individual.child_of_families[0]
        return gr_individual

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
            spouse = marriage.get_spouse(individual.individual_id)

            # starting x index of gr_individual is first marriage (i.e. last in reversed list)
            if marriage_index == len(visible_marriages) - 1:
                if not gr_individual.has_x_position(child_of_family):
                    gr_individual.set_x_position(
                        x_position, child_of_family)

            if marriage_index == len(visible_marriages) - 1:
                if not gr_individual.has_x_position(marriage):
                    gr_individual.set_x_position(
                        x_position, marriage)
                    x_position += 1
            else:
                if spouse is not None and spouse.has_graphical_representation():
                    gr_spouse = spouse.graphical_representations[0]
                    if not gr_spouse.has_x_position(marriage):
                        gr_spouse.set_x_position(
                            x_position, marriage)
                        x_position += 1


            for child in marriage.get_sorted_children():
                self.place_selected_individuals(
                    child, marriage, x_position,
                    discovery_cache=discovery_cache)
                if child.has_graphical_representation():
                    width = child.graphical_representations[0].get_descendant_width(
                        marriage)
                    x_position += width

            if marriage_index < len(visible_marriages) - 1:
                if not gr_individual.has_x_position(marriage):
                    gr_individual.set_x_position(
                        x_position, marriage)
                    x_position += 1
            else:
                if spouse is not None and spouse.has_graphical_representation():
                    gr_spouse = spouse.graphical_representations[0]
                    if not gr_spouse.has_x_position(marriage):
                        gr_spouse.set_x_position(
                            x_position, marriage)
                        x_position += 1

        self.max_x_index = max(self.max_x_index, x_position)

        # recalculate
        birth_ordinal_value = gr_individual.birth_date_ov
        death_ordinal_value = gr_individual.death_date_ov
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
        """
        Update the chart, caching of positioning data is regarded

        Args:
            filter_lambda (lambda(BaseIndividual), optional): filtering of individuals. Defaults to None.
            color_lambda (lambda(GraphicalIndividual), optional): coloring of individuals. Defaults to None.
            images_lambda (lambda(BaseIndividual), optional): images of individuals. Defaults to None.
            rebuild_all (bool, optional): clear cache, rebuild everything. Defaults to False.
            update_view (bool, optional): update formatting only. Defaults to False.

        Returns:
            bool: view has changed
        """
        rebuild_all = rebuild_all or self._positioning != self._backup_positioning or \
            self._chart_configuration != self._backup_chart_configuration
        update_view = update_view or rebuild_all or self._formatting != self._backup_formatting
        def local_filter_lambda(individual, _filter_lambda=filter_lambda):
            if individual.individual_id in self._chart_configuration['discovery_blacklist']:
                return True
            if _filter_lambda is not None:
                return _filter_lambda(individual)
            return False
        if color_lambda:
            update_view = True
        if images_lambda:
            update_view = True
        self._instances.color_getter = self._instances.color_getters[self._formatting['coloring_of_individuals']]

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

                x_pos += root_individual.graphical_representations[0].get_descendant_width(self._instances[('f', cof_family_id)])

            for settings in self._chart_configuration['root_individuals']:
                root_individual_id = settings['individual_id']
                generations = settings['generations']
                try:
                    self.modify_layout(root_individual_id)
                except Exception as e:
                    pass


            for gir in self.gr_individuals:
                color = None
                if color_lambda is None:
                    color = color_lambda
                if color_lambda is None or color is None:
                    if self._formatting['highlight_descendants']:
                        cofs = gir.individual.child_of_families
                        if not cofs or not cofs[0].has_graphical_representation():
                            marriages = gir.visible_marriages
                            if marriages:
                                spouse = marriages[0].get_spouse(gir)
                                if spouse and spouse.individual.child_of_families and spouse.individual.child_of_families[0].has_graphical_representation():
                                    color = (225,225,225)
                    if color is None:
                        color = self._instances.color_getter(gir)
                gir.color = color
                if images_lambda:
                    images = images_lambda(gir.individual)
                else:
                    images = {}
                gir.individual.images = images

            self.define_svg_items()

        elif update_view:
            self.clear_svg_items()

            for gir in self.gr_individuals:
                color = None
                if color_lambda is None:
                    color = color_lambda
                if color_lambda is None or color is None:
                    if self._formatting['highlight_descendants']:
                        cofs = gir.child_of_families
                        if cofs and cofs[0].has_graphical_representation():
                            color = (215,215,215)
                    if color is None:
                        color = self._instances.color_getter(gir)
                gir.color = color
                if images_lambda:
                    images = images_lambda(gir.individual)
                else:
                    images = {}
                gir.individual.images = images

            self.define_svg_items()
        self._backup_chart_configuration = deepcopy(self._chart_configuration)
        self._backup_formatting = deepcopy(self._formatting)
        self._backup_positioning = deepcopy(self._positioning)
        return update_view or rebuild_all
