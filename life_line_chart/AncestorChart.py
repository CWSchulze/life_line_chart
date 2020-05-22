import os
from .SimpleSVGItems import Line, Path, CubicBezier
import logging
import hashlib
import datetime
import svgwrite
from copy import deepcopy
from .BaseSVGChart import BaseSVGChart
from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected
from cmath import sqrt, exp, pi
from math import floor, ceil

logger = logging.getLogger("life_line_chart")

class AncestorChart(BaseSVGChart):
    """
    Ancestor Chart
    ==============

    The ancestor chart shows the ancestors of one or more root individuals.
    The parents only enclose direct children. Both, father and mother are
    visible. Usually ancestors are visible, optionally all children of a
    visible family can be added.

    Each individual appears once. So in case of a second marriage, the
    individual is connected across the chart to the second spouse. Because
    of that, ancestor collapse is visualized.
    """

    def __init__(self, positioning=None, formatting=None, instance_container=None):
        BaseSVGChart.__init__(self, positioning, formatting, instance_container)

        # configuration of this chart
        self._chart_configuration.update(self.get_default_chart_configuration())
        # self._graphical_family_class = GraphicalFamily # TODO: necessary if other graphs are implemented
        # self._graphical_individual_class = GraphicalIndividual # TODO: necessary if other graphs are implemented

    @staticmethod
    def get_default_chart_configuration():
        """
        get the default chart configuration

        Returns:
            dict: default chart configuration dict
        """

        return {
            'root_individuals': [],
            'family_children': [],
            'discovery_blacklist': []
        }

    def select_individuals(self, individual, generations=None, color=None, filter=None):
        """
        Select individuals to show. This is done by creating instances of graphical representations.

        Args:
            individual (BaseIndividual): starting point for selection
            generations (int): number of generations to search for ancestors.
            color (list, optional): RGB color. Defaults to None.
            filter (lambda, optional): lambda(BaseIndividual) : return Boolean. Defaults to None.
        """

        if filter and filter(individual):
            return

        if not individual.has_graphical_representation():
            gr_individual = self._create_individual_graphical_representation(
                individual)

            if gr_individual is None:
                return

            if color is None:
                i = int(hashlib.sha1(" ".join(gr_individual.name).encode(
                    'utf8')).hexdigest(), 16) % (10 ** 8)
                c = (i*23 % 255, i*41 % 255, (i*79 % 245) + 10)
                f = 255/max(c)
                c = [int(x*f) for x in c]
                f = min(1, 500/sum(c))
                c = [int(x*f) for x in c]
                gr_individual.color = c
            else:
                gr_individual.color = color
        else:
            gr_individual = individual.graphical_representations[0]

        child_of_families = individual.get_child_of_family()[:1]
        for child_of_family in child_of_families:
            family = self._create_family_graphical_representation(
                child_of_family)
            family.add_visible_children(individual)
            gr_individual.visible_parent_family = family
            if generations > 0 or generations < 0:
                # parents = individual.get_father_and_mother()
                father, mother = child_of_family.get_husband_and_wife()
                if father:
                    self.select_individuals(
                        father, generations - 1, color=gr_individual.color if self._positioning['fathers_have_the_same_color'] else None, filter=filter)
                if mother:
                    self.select_individuals(
                        mother, generations - 1, filter=filter)
            # family.visible_children.sort()

    def select_family_children(self, family, filter=None):
        """
        Select children of a family. This is done by creating instances of graphical representations.

        Args:
            individual (BaseIndividual): starting point for selection
            filter (lambda, optional): lambda(BaseIndividual) : return Boolean. Defaults to None.
        """

        if not family.has_graphical_representation():
            return
        for child in family.get_children():
            if filter and filter(child):
                continue

            if not child.has_graphical_representation():
                gr_individual = self._create_individual_graphical_representation(
                    child)

                if gr_individual is None:
                    return

                i = int(hashlib.sha1(" ".join(gr_individual.name).encode(
                    'utf8')).hexdigest(), 16) % (10 ** 8)
                c = (i*23 % 255, i*41 % 255, (i*79 % 245) + 10)
                f = 255/max(c)
                c = [int(x*f) for x in c]
                f = min(1, 500/sum(c))
                c = [int(x*f) for x in c]
                gr_individual.color = c

                family.graphical_representations[0].add_visible_children(child)
                child.graphical_representations[0].visible_parent_family = family.graphical_representations[0]


    def place_selected_individuals(self, individual, child_family, spouse_family, child_of_family, x_offset=0, discovery_cache=[]):
        """
        Place the graphical representations in direction of x

        Args:
            individual (BaseIndividual): individual
            child_family (BaseFamily): I dont remember
            spouse_family (BaseFamily): Spouse family of this individual
            child_of_family (BaseFamily): child-of-family of this individual
        """
        discovery_cache.append(individual.plain_name)

        logger.info(f"discovering {individual.plain_name}")
        x_position = x_offset
        gr_individual = individual.graphical_representations[0]
        gr_individual.x_start = x_position
        self.min_x_index = min(self.min_x_index, x_position)
        child_of_families = individual.get_child_of_family()

        # recursively add the father branch
        for local_child_of_family in child_of_families:
            father, mother = local_child_of_family.get_husband_and_wife()
            if father and father.has_graphical_representation():
                fathers_child_of_families = father.get_child_of_family()
                if fathers_child_of_families:
                    fathers_born_in_family = fathers_child_of_families[0]
                else:
                    fathers_born_in_family = None
                if not father.graphical_representations[0].get_x_position() or local_child_of_family.family_id not in father.graphical_representations[0].get_x_position():
                    father.graphical_representations[0].visual_placement_child = (
                        individual, spouse_family)
                    if local_child_of_family.has_graphical_representation():
                        local_child_of_family.graphical_representations[0].visual_placement_child = individual
                    # father.graphical_representations[0].visual_placement_child = spouse_family
                    self.place_selected_individuals(
                        father, spouse_family, local_child_of_family, fathers_born_in_family, x_position, discovery_cache)
                    width = father.graphical_representations[0].get_width(
                        local_child_of_family)
                    if local_child_of_family.has_graphical_representation():
                        local_child_of_family.graphical_representations[0].husb_width = \
                            lambda gr=father.graphical_representations[0], cof=local_child_of_family: gr.get_width(cof)
                    x_position += width

        # add the main individual and its visible siblings
        children_start_x = x_position

        if child_of_family is not None and child_of_family.has_graphical_representation() and child_of_family.graphical_representations[0].visible_children:
            siblings = [sibling for _, _, sibling in sorted(child_of_family.graphical_representations[0].visible_children.values())]
        else:
            siblings = [individual]
        for sibling in siblings:
            if sibling.individual_id == individual.individual_id:
                if sibling.graphical_representations[0].get_x_position() is None or spouse_family is not None and spouse_family.family_id not in sibling.graphical_representations[0].get_x_position():
                    # add new position of this spouse family
                    sibling.graphical_representations[0].set_x_position(
                        x_position, spouse_family)

                    if child_of_family and child_of_family.family_id not in sibling.graphical_representations[0].get_x_position():
                        # not added yet, so this is the primary cof placement
                        sibling.graphical_representations[0].set_x_position(
                            x_position, child_of_family, True)

                    x_position += 1

            elif not sibling.graphical_representations[0].get_x_position() or child_of_family.family_id not in sibling.graphical_representations[0].get_x_position():
                if not sibling.graphical_representations[0].visual_placement_child:
                    sibling.graphical_representations[
                        0].visual_placement_child = gr_individual.visual_placement_child
                    sibling.graphical_representations[0].set_x_position(
                        x_position,
                        child_of_family)
                    x_position += 1

        if child_of_family and child_of_family.has_graphical_representation() and not child_of_family.graphical_representations[0].children_width:
            child_of_family.graphical_representations[0].children_width = x_position - \
                children_start_x

        # recursively add the mother branch
        for local_child_of_family in child_of_families:
            father, mother = local_child_of_family.get_husband_and_wife()
            if mother and mother.has_graphical_representation():
                mothers_child_of_families = mother.get_child_of_family()
                if mothers_child_of_families:
                    mothers_born_in_family = mothers_child_of_families[0]
                else:
                    mothers_born_in_family = None
                if not mother.graphical_representations[0].get_x_position() or local_child_of_family.family_id not in mother.graphical_representations[0].get_x_position():
                    mother.graphical_representations[0].visual_placement_child = (
                        individual, spouse_family)
                    if local_child_of_family.has_graphical_representation():
                        local_child_of_family.graphical_representations[0].visual_placement_child = individual
                    # mother.graphical_representations[0].visual_placement_child = spouse_family
                    self.place_selected_individuals(
                        mother, spouse_family, local_child_of_family, mothers_born_in_family, x_position, discovery_cache)
                    x_min, x_max = mother.graphical_representations[0].get_range(
                        local_child_of_family)
                    width = x_max - x_min + 1
                    if local_child_of_family.has_graphical_representation():
                        local_child_of_family.graphical_representations[0].wife_width = \
                            lambda gr=mother.graphical_representations[0], cof=local_child_of_family: gr.get_width(cof)
                    x_position += width

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

    def _compress_single_individual_position(self, individual, cof, direction):
        """
        move single individual until it collides
        """
        try:
            i = 0
            while i < 5000:
                i += 1
                self._move_single_individual(individual, cof, direction)
                self._check_compressed_x_position(True)
        except LifeLineChartCollisionDetected:
            pass
        self._move_single_individual(individual, cof, - direction)

    def _compress_chart_ancestor_graph(self, gr_family):
        """
        compress the chart vertically.

        # TODO: compressing fails if siblings are dragged apart which reunite families in later generations (Andreas Adam Lindner)

        Args:
            gr_family (GraphicalFamily): graphical family representation instance
        """
        individuals = []
        if gr_family is None:
            return

        family_was_flipped = False
        x_pos_husb = None
        x_pos_wife = None
        if gr_family.husb is not None and gr_family.husb.has_graphical_representation():
            x_pos_husb = gr_family.husb.graphical_representations[0].get_x_position()[
                gr_family.family_id][1]
            individuals.append((1, gr_family.husb))
        if gr_family.wife is not None and gr_family.wife.has_graphical_representation():
            x_pos_wife = gr_family.wife.graphical_representations[0].get_x_position()[
                gr_family.family_id][1]
            individuals.append((-1, gr_family.wife))
        if x_pos_husb and x_pos_wife and x_pos_husb > x_pos_wife:
            family_was_flipped = True

        for _, individual in sorted(individuals):
            cofs = individual.get_child_of_family()
            for cof in cofs:
                if cof.has_graphical_representation():
                    if cof.husb is None or cof.wife is None \
                            or not cof.husb.has_graphical_representation() \
                            or not cof.wife.has_graphical_representation():
                        this_individual_x_pos = individual.graphical_representations[0].get_x_position()[
                            cof.family_id][1]
                        parent_x_pos = None
                        if cof.husb is not None and cof.husb.has_graphical_representation():
                            parent_x_pos = cof.husb.graphical_representations[0].get_x_position()[
                                cof.family_id][1]
                        if cof.wife is not None and cof.wife.has_graphical_representation():
                            parent_x_pos = cof.wife.graphical_representations[0].get_x_position()[
                                cof.family_id][1]
                        if parent_x_pos is not None and this_individual_x_pos > parent_x_pos:
                            self._compress_single_individual_position(
                                individual, cof, -1)
                            # self._move_single_individual(individual, cof, parent_x_pos - this_individual_x_pos + 1)
                        elif parent_x_pos is not None and this_individual_x_pos < parent_x_pos:
                            self._compress_single_individual_position(
                                individual, cof, 1)
                            # self._move_single_individual(individual, cof, parent_x_pos - this_individual_x_pos - 1)
                    try:
                        self._compress_chart_ancestor_graph(
                            cof.graphical_representations[0])
                    except KeyError as e:
                        pass
        for original_direction_factor, individual in sorted(individuals):
            if individual is None:
                continue
            i = 0
            if family_was_flipped:
                direction_factor = - original_direction_factor
            else:
                direction_factor = original_direction_factor

            self.compression_steps -= 1
            if self.compression_steps <= 0:
                continue

            if not individual.graphical_representations[0].visible_parent_family or not individual.graphical_representations[0].visible_parent_family.family_id in individual.graphical_representations[0].get_x_position():
                # try:
                #     while i < 50000:
                #         self._move_single_individual(
                #             individual, individual.graphical_representations[0].visible_parent_family, direction_factor*1)
                #         self._check_compressed_x_position(True)
                #         i += 1
                # except LifeLineChartCollisionDetected:
                #     # print("   collision of " + " and ".join([" ".join(a.name) for a in e.args]))
                #     self._move_single_individual(
                #         individual, individual.graphical_representations[0].visible_parent_family, -direction_factor*1)
                # except LifeLineChartCannotMoveIndividual:
                #     pass
                continue
            # try:
            #     while i < 50000:
            #         _move_single_individual(individual, individual.graphical_representations[0].visible_parent_family, direction_factor*1)
            #         _check_compressed_x_position(True)
            #         i += 1
            # except:
            #     _move_single_individual(individual, individual.graphical_representations[0].visible_parent_family, -direction_factor*1)

            try:
                while i < 50000:
                    self._move_individual_and_ancestors(
                        individual, individual.graphical_representations[0].visible_parent_family, direction_factor*1)
                    self._check_compressed_x_position(True)
                    i += 1
            except LifeLineChartCollisionDetected as e:
                # print("   collision of " + " and ".join([" ".join(a.name) for a in e.args]))
                self._move_individual_and_ancestors(
                    individual, individual.graphical_representations[0].visible_parent_family, -direction_factor*1)
            except LifeLineChartCannotMoveIndividual as e:
                pass
            except KeyError as e:
                pass
            if i != 0:
                logger.info('moved ' + ' '.join(individual.name) +
                            ' by ' + str(i * direction_factor * 1))

    def modify_layout(self, root_individual_id):
        """
        improvement of individual placement.

        Args:
            root_individual_id (str): root individual id used as root node for compression
        """
        self.check_unique_x_position()

        if self._positioning['flip_to_optimize']:
            width, loli = self._calculate_sum_of_distances()
            old_width = width
            candidantes = set()
            for key in sorted(loli.keys()):
                # continue
                # if index == 1:
                #     continue
                def collect_candidates(children):
                    for child in children:
                        if len(child.graphical_representations) > 0:
                            candidantes.add(child)
                            collect_candidates(child.children)

                individual = loli[key]
                collect_candidates(individual.children)
                for cof in individual.individual.get_child_of_family():
                    collect_candidates(cof.get_children())

            # candidantes = set()
            items = list(reversed(sorted([(child.graphical_representations[0].get_birth_date_ov(), index, child) for index, child in enumerate(candidantes)])))
            failed = []
            for ov, _, child in items:
                c_pos = list(
                    child.graphical_representations[0].get_x_position().values())[1:]
                for x_pos in c_pos:
                    if x_pos[2] is None:
                        continue
                    # family_id = key2[2]
                    # x_pos = c_pos[key2]
                    self._flip_family(x_pos[2])
                    failed, _, _ = self.check_unique_x_position()
                    if len(failed) > 0:
                        logger.error("failed flipping " +
                                     str((x_pos[2].family_id, ov)))
                        break
                    new_width, _ = self._calculate_sum_of_distances()
                    if new_width >= width:
                        self._flip_family(x_pos[2])
                    else:
                        width = new_width
                # print (x_pos)
                if len(failed) > 0:
                    break

            logger.info(
                f"flipping reduced the cross connections by {width - old_width} (i.e. from {old_width} to {width})")

        # for gr_family in self.graphical_family_representations:
        if self._positioning['compress']:
            failed, old_x_min_index, old_x_max_index = self.check_unique_x_position()
            old_width = old_x_max_index - old_x_min_index
            self.compression_steps = 1e30
            if 'compression_steps' in self._formatting and self._formatting['compression_steps'] > 0:
                self.compression_steps = self._formatting['compression_steps']
            self._compress_chart_ancestor_graph(self._instances[(
                'i', root_individual_id)].graphical_representations[0].visible_parent_family)

            # compressed chart should be aligned left
            _, min_index_x, max_index_x, self.position_to_person_map = self._check_compressed_x_position(
                False)
            self._move_individual_and_ancestors(self._instances[('i', root_individual_id)], sorted(list(self._instances[(
                'i', root_individual_id)].graphical_representations[0].get_x_position().values()))[0][2], -(min_index_x-old_x_min_index)*1)
            keys = sorted(list(self.position_to_person_map.keys()))
            for key in keys:
                self.position_to_person_map[key - (
                    min_index_x - old_x_min_index) * 1] = self.position_to_person_map.pop(key)
            width = (max_index_x - min_index_x) + 1
            self.min_x_index = 0
            self.max_x_index = width
            logger.info(
                f"compression reduced the total width by {width - old_width} (i.e. from {old_width} to {width})")
        else:
            _, _, _, self.position_to_person_map = self._check_compressed_x_position(
                False)
        # for collision in collisions:
        #     if collision[1] is None:
        #         print("collision of " + " ".join(collision[0].name))
        #     else:
        #         print("collision of " + " ".join(collision[0].name) + " with " + " ".join(collision[1].name))

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
                self.select_individuals(root_individual, generations, filter=local_filter_lambda)

            for family_id in self._chart_configuration['family_children']:
                family = self._instances[(
                    'f', family_id)]
                self.select_family_children(family, filter=local_filter_lambda)

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
                    root_individual, None, None, self._instances[('f', cof_family_id)], x_pos)

                x_pos += root_individual.graphical_representations[0].get_width(None)

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
