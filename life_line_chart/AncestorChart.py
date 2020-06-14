import os
import logging
import datetime
import svgwrite
from copy import deepcopy
from .SimpleSVGItems import Line, Path, CubicBezier
from .BaseSVGChart import BaseSVGChart
from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected
from .Translation import get_strings, recursive_merge_dict_members

logger = logging.getLogger("life_line_chart")

_strings = get_strings('AncestorChart')
_, _strings = recursive_merge_dict_members(BaseSVGChart.SETTINGS_DESCRIPTION, _strings, remove_unknown_keys=False)


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

    DEFAULT_POSITIONING = {
        'debug_optimization_compression_steps': -1,  # debugging option
        'debug_optimization_flipping_steps': -1,  # debugging option
        'compress': False,
        'flip_to_optimize': False,
    }
    DEFAULT_POSITIONING.update(BaseSVGChart.DEFAULT_POSITIONING)

    DEFAULT_FORMATTING = {
        'fathers_have_the_same_color': False,
    }
    DEFAULT_FORMATTING.update(BaseSVGChart.DEFAULT_FORMATTING)

    DEFAULT_CHART_CONFIGURATION = {
            'root_individuals': [],
            'family_children': [],
            'discovery_blacklist': []
    }
    DEFAULT_CHART_CONFIGURATION.update(BaseSVGChart.DEFAULT_CHART_CONFIGURATION)

    SETTINGS_DESCRIPTION = _strings

    def __init__(self, positioning=None, formatting=None, instance_container=None):
        BaseSVGChart.__init__(self, positioning, formatting, instance_container)

        # configuration of this chart
        self._chart_configuration.update(AncestorChart.DEFAULT_CHART_CONFIGURATION)

    def select_individuals(self, individual, generations=None, filter=None, discovery_cache=[]):
        """
        Select individuals to show. This is done by creating instances of graphical representations.

        Args:
            individual (BaseIndividual): starting point for selection
            generations (int): number of generations to search for ancestors.
            filter (lambda, optional): lambda(BaseIndividual) : return Boolean. Defaults to None.
        """

        if filter and filter(individual):
            return

        if not individual.has_graphical_representation():
            gr_individual = self._create_individual_graphical_representation(
                individual)

            if gr_individual is None:
                return

            gr_individual.color = (0,0,0)
            discovery_cache.append(individual.individual_id)
            gr_individual.debug_label = '\n' + str(len(discovery_cache))
        else:
            # must not leave here, because merging of different family branches would stop here
            # if len(individual.child_of_families) > 0 and individual.child_of_families[0].has_graphical_representation():
            #     return
            gr_individual = individual.graphical_representations[0]

        go_deeper = True
        child_of_families = individual.child_of_families[:1]
        for child_of_family in child_of_families:
            # if not (generations > 0 or generations < 0):
            #     continue
            new_f_gr = not child_of_family.has_graphical_representation()
            gr_child_of_family = self._create_family_graphical_representation(
                child_of_family)
            gr_child_of_family.add_visible_children(gr_individual)

            if generations > 0 or generations < 0:
                father, mother = child_of_family.get_husband_and_wife()
                new_gr = new_f_gr and father and not father.has_graphical_representation()
                if father:
                    gr_father = self.select_individuals(
                        father,
                        generations - 1 if go_deeper else 0,
                        filter=filter,
                        discovery_cache=discovery_cache)

                    if gr_father and gr_child_of_family.gr_husb is None:
                        gr_child_of_family.gr_husb = gr_father

            if generations > 0 or generations < 0:
                father, mother = child_of_family.get_husband_and_wife()
                new_gr = new_f_gr and mother and not mother.has_graphical_representation()
                if mother:
                    gr_mother = self.select_individuals(
                        mother, generations - 1 if go_deeper else 0,
                        filter=filter,
                        discovery_cache=discovery_cache)
                    if gr_mother and gr_child_of_family.gr_wife is None:
                        gr_child_of_family.gr_wife = gr_mother
        return gr_individual

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
                gr_child = self._create_individual_graphical_representation(
                    child)

                if gr_child is None:
                    return

                gr_child.color = (0,0,0)

                family.graphical_representations[0].add_visible_children(gr_child)
                gr_child.strongly_connected_parent_family = family.graphical_representations[0]

    def place_selected_individuals(self, gr_individual, child_family, spouse_family, child_of_family, x_offset=0, discovery_cache=[], root_node_discovery_cache=[]):
        """
        Place the graphical representations in direction of x

        Args:
            individual (BaseIndividual): individual
            child_family (BaseFamily): I dont remember
            spouse_family (BaseFamily): Spouse family of this individual
            child_of_family (BaseFamily): child-of-family of this individual
        """

        individual = gr_individual.individual
        if child_of_family and child_of_family.has_graphical_representation():
            gr_child_of_family = child_of_family.graphical_representations[0]
        else:
            gr_child_of_family = None
        if spouse_family and spouse_family.has_graphical_representation():
            gr_spouse_family = spouse_family.graphical_representations[0]
        else:
            gr_spouse_family = None
        if (gr_individual, spouse_family) in discovery_cache:
            # if this individual has already been placed in this marriage family
            return

        logger.info(f"discovering {individual.plain_name}")
        x_position = x_offset
        self.min_x_index = min(self.min_x_index, x_position)

        # +----------------------------------------------
        # | start with going back to the actual root node
        # +----------------------------------------------

        # get siblings
        child_of_families = gr_individual.connected_parent_families
        if child_of_family is not None and child_of_family.has_graphical_representation() and child_of_family.graphical_representations[0].visible_children:
            siblings = child_of_family.graphical_representations[-1].visible_children
        else:
            siblings = [gr_individual]

        # go back to root node
        root_node_discovery_cache += siblings
        if spouse_family and spouse_family.has_graphical_representation():
            for gr_child in spouse_family.graphical_representations[0].visible_children:
                c_vms = [vm.family for vm in gr_child.visible_marriages]
                if not c_vms:
                    c_vms = [None]
                for c_m in c_vms:
                    if gr_child not in root_node_discovery_cache:
                        if gr_child.get_x_position() is None:
                            self.place_selected_individuals(
                                gr_child, None, c_m, spouse_family,
                                x_position, discovery_cache, root_node_discovery_cache)

        if (gr_individual,spouse_family) in discovery_cache:
            # when this node was handled by the place_selected_individuals call in a root node
            # then we should return here
            return

        # +----------------------------------------------
        # | add father branch, siblings and mother branch
        # +----------------------------------------------

        def add_parent(parent_variable_name, x_position):
            """
            add mother or father to the chart

            Args:
                parent_variable_name (str): 'husb' or 'wife'
                x_position (int): x position index

            Returns:
                int: new x position index
            """
            for gr_local_child_of_family in child_of_families:
                local_child_of_family = gr_local_child_of_family.family
                gr_parent = getattr(
                    gr_local_child_of_family, 'gr_' + parent_variable_name)
                if not gr_parent:
                    continue
                if not gr_parent.has_x_position(local_child_of_family):
                    parent_child_of_families = gr_parent.individual.child_of_families
                    if parent_child_of_families:
                        parent_born_in_family = parent_child_of_families[0]
                    else:
                        parent_born_in_family = None

                    if local_child_of_family.has_graphical_representation():
                        gr_individual.strongly_connected_parent_family = gr_local_child_of_family
                    self.place_selected_individuals(
                        gr_parent, spouse_family, local_child_of_family, parent_born_in_family,
                        x_position, discovery_cache, root_node_discovery_cache)
                    width = gr_parent.get_ancestor_width(
                        gr_local_child_of_family)
                    setattr(gr_local_child_of_family, parent_variable_name + '_width',
                        lambda gr=gr_parent, cof=gr_local_child_of_family: gr.get_ancestor_width(cof)
                        )
                    x_position += width
            return x_position

        # add the father branch
        x_position = add_parent('husb', x_position)

        # add the main individual and its visible siblings
        for gr_sibling in siblings:
            sibling = gr_sibling.individual
            if sibling.individual_id == individual.individual_id:
                if not gr_sibling.has_x_position(spouse_family):
                    # add new position of this spouse family
                    gr_sibling.set_x_position(
                        x_position, spouse_family)

                    if not gr_sibling.has_x_position(child_of_family):
                        # not added yet, so this is the primary cof placement
                        gr_sibling.set_x_position(
                            x_position, child_of_family, True)
                        gr_sibling.first_marriage_strongly_connected_to_parent_family = True

                    x_position += 1

            elif not gr_sibling.has_x_position(child_of_family):
                gr_sibling.set_x_position(
                    x_position,
                    child_of_family)
                x_position += 1
                gr_sibling.first_marriage_strongly_connected_to_parent_family = False

        # add the mother branch
        x_position = add_parent('wife', x_position)

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
        discovery_cache.append((gr_individual,spouse_family))

    def _compress_single_individual_position(self, gr_individual, cof, direction, nSteps=50000):
        """
        move single gr_individual until it collides
        """
        if nSteps <= 0:
            return
        try:
            i = 0
            while i < nSteps:
                i += 1
                self._move_single_individual(gr_individual, cof, direction)
                if i < nSteps:
                    self._check_compressed_x_position(True, min_distance=1)
                else:
                    self._check_compressed_x_position(True)
        except LifeLineChartCollisionDetected as e:
            # print(e)
            i2 = i
            while i2 >= 0:
                i2 -= 1
                try:
                    self._move_single_individual(gr_individual, cof, -direction)
                    self._check_compressed_x_position(True)
                except:
                    pass
                else:
                    break

    def _compress_chart_ancestor_graph(self, gr_family):
        """
        compress the chart vertically.

        # TODO: compressing fails if siblings are dragged apart which reunite families in later generations (Andreas Adam Lindner)

        Args:
            gr_family (GraphicalFamily): graphical family representation instance
        """
        gr_individuals = []
        if gr_family is None:
            return

        family_was_flipped = False
        x_pos_husb = None
        x_pos_wife = None
        if gr_family.gr_husb:
            x_pos_husb = gr_family.gr_husb.get_x_position()[
                gr_family.family_id][1]
            if gr_family.husb.child_of_families and gr_family.husb.child_of_families[0]:# \
                    #and (gr_family.husb.child_of_families[0].husb and gr_family.husb.child_of_families[0].husb.has_graphical_representation()) \
                    #and (gr_family.husb.child_of_families[0].wife and gr_family.husb.child_of_families[0].wife.has_graphical_representation()):
                gr_individuals.append((1, gr_family.gr_husb))
        if gr_family.gr_wife:
            x_pos_wife = gr_family.gr_wife.get_x_position()[
                gr_family.family_id][1]
            if gr_family.wife.child_of_families and gr_family.wife.child_of_families[0]:# \
                    #and (gr_family.wife.child_of_families[0].husb and gr_family.wife.child_of_families[0].husb.has_graphical_representation()) \
                    #and (gr_family.wife.child_of_families[0].wife and gr_family.wife.child_of_families[0].wife.has_graphical_representation()) \
                gr_individuals.append((-1, gr_family.gr_wife))

        vcs = gr_family.visible_children
        children_width = len(vcs)
        children_x_positions = [gr_child.get_x_position(gr_family)[1] for gr_child in vcs]
        children_x_center = sum(children_x_positions)*1.0/children_width
        blocked_positions = children_x_positions.copy()
        if x_pos_husb: blocked_positions.append(x_pos_husb)
        if x_pos_wife: blocked_positions.append(x_pos_wife)

        if x_pos_husb and children_x_center < x_pos_husb or x_pos_wife and x_pos_wife < children_x_center:
            family_was_flipped = True

        for _, gr_individual in sorted(gr_individuals):
            cofs = gr_individual.individual.child_of_families
            for cof in cofs:
                if cof.has_graphical_representation():
                    gr_cof = cof.graphical_representations[0]
                    try:
                        self._compress_chart_ancestor_graph(gr_cof)
                    except KeyError as e:
                        pass

                if self.debug_optimization_compression_steps <= 0:
                    break
            if self.debug_optimization_compression_steps <= 0:
                break
        if self.debug_optimization_compression_steps <= 0:
            return
        for original_direction_factor, gr_individual in sorted(gr_individuals):
            if gr_individual is None:
                continue
            #gr_individual = individual.graphical_representations[0]
            i = 0
            if family_was_flipped:
                direction_factor = - original_direction_factor
            else:
                direction_factor = original_direction_factor

            vms = gr_individual.visible_marriages
            if vms:
                strongly_connected_parent_family = vms[0]

                this_individual_x_pos = gr_individual.get_x_position()[
                    strongly_connected_parent_family.family_id][1]
                if not gr_individual.has_x_position(strongly_connected_parent_family):
                    continue
                if this_individual_x_pos and (this_individual_x_pos + direction_factor*1) in blocked_positions:
                    continue

                try:
                    while i < 50000:
                        if (i+1)%1000 == 0:
                            logger.warning(f'i {i} for gr_individual {gr_individual}')
                        i += 1
                        self._move_individual_and_ancestors(
                            gr_individual, strongly_connected_parent_family, direction_factor*1)
                        self.debug_optimization_compression_steps -= 1
                        if self.debug_optimization_compression_steps <= 0:
                            break
                        self._check_compressed_x_position(True, min_distance=1)
                except LifeLineChartCollisionDetected as e:
                    # print(e)
                    i2 = i
                    while i2 >= 0:
                        i2 -= 1
                        try:
                            self._move_individual_and_ancestors(
                                gr_individual, strongly_connected_parent_family, -direction_factor*1)
                            self._check_compressed_x_position(True)
                        except:
                            pass
                        else:
                            break
                    self.debug_optimization_compression_steps -= 1
                    if self.debug_optimization_compression_steps <= 0:
                        break
                except LifeLineChartCannotMoveIndividual as e:
                    pass
                except KeyError as e:
                    pass

                if self.debug_optimization_compression_steps <= 0:
                    break
                if i2 != 0:
                    logger.info('moved ' + ' '.join(gr_individual.get_name()) +
                                ' by ' + str(i2 * direction_factor * 1))
        #for _, gr_individual in sorted(gr_individuals):
            self._move_child_to_center_between_parents(gr_individual)

    def _move_child_to_center_between_parents(self, gr_individual):
        cofs = gr_individual.individual.child_of_families
        for cof in cofs:
            if cof.has_graphical_representation():
                gr_cof = cof.graphical_representations[0]
                husb_x_pos = None
                if gr_cof.gr_husb is not None:
                    husb_x_pos = gr_cof.gr_husb.get_x_position()[
                        cof.family_id][1]
                wife_x_pos = None
                if cof.wife is not None and cof.wife.has_graphical_representation():
                    wife_x_pos = gr_cof.gr_wife.get_x_position()[
                        cof.family_id][1]
                if husb_x_pos and wife_x_pos and True:
                    middle_x_pos = (husb_x_pos + wife_x_pos)/2.0
                    this_individual_x_pos = gr_individual.get_x_position()[
                        cof.family_id][1]
                    nSteps = int(abs(this_individual_x_pos - middle_x_pos))
                    if nSteps > 0:
                        if nSteps > 1000:
                            logger.error(f'nSteps {nSteps} for gr_individual {gr_individual}')
                        direction = -1 if this_individual_x_pos > middle_x_pos else 1
                        self._compress_single_individual_position(
                            gr_individual, cof, direction, nSteps)

    def modify_layout(self, root_individual_id):
        """
        improvement of individual placement.

        Args:
            root_individual_id (str): root individual id used as root node for compression
        """
        self.check_unique_x_position()

        candidates = []
        if self._positioning['flip_to_optimize']:
            width, loli = self._calculate_sum_of_distances()
            old_width = width
            for key in loli.keys():
                def collect_candidates(gr_children):
                    for gr_child in gr_children:
                        # if gr_child not in candidates:
                        candidates.append(gr_child)
                        collect_candidates(gr_child.visible_children)

                gr_individual = loli[key]
                if gr_individual not in candidates:
                    candidates.append(gr_individual)
                collect_candidates(gr_individual.visible_children)
                for gr_cof in gr_individual.connected_parent_families:
                    collect_candidates(gr_cof.visible_children)

            nSteps = self._positioning['debug_optimization_flipping_steps']

            failed = []
            has_been_done = []
            for gr_child in candidates:
                ov = gr_child.birth_date_ov
                c_pos = list(gr_child.get_x_position().values())
                c_pos = c_pos[1:]

                for x_pos in c_pos:
                    family = x_pos[2]
                    if family is None:
                        continue
                    gr_family = family.graphical_representations[0]
                    if gr_family not in has_been_done:
                        has_been_done.append(gr_family)

                        nSteps -= 1
                        if nSteps == 0:
                            break

                        self._flip_family(gr_family)

                        nSteps -= 1
                        if nSteps == 0:
                            break

                        failed, _, _ = self.check_unique_x_position()
                        if len(failed) > 0:
                            logger.error("failed flipping " +
                                        str((family, family.family_id, ov)) + str(nSteps))
                            break
                        new_width, _ = self._calculate_sum_of_distances()
                        # print (f'step={nSteps} new_width={new_width} width_difference={new_width-old_width} algorithm_failed={len(failed) > 0} better={new_width < width}')
                        if new_width >= width:
                            self._flip_family(gr_family)
                        else:
                            width = new_width
                # print (x_pos)
                if nSteps == 0:
                    break
                if len(failed) > 0:
                    break

            logger.info(
                f"flipping reduced the cross connections by {width - old_width} (i.e. from {old_width} to {width})")

        # for gr_family in self.gr_families:
        if self._positioning['compress']:
            root_individual = self._instances[(
                'i', root_individual_id)]
            gr_root_individual = root_individual.graphical_representations[0]

            failed, old_x_min_index, old_x_max_index = self.check_unique_x_position()
            old_width = old_x_max_index - old_x_min_index
            self.debug_optimization_compression_steps = 1e30
            if 'debug_optimization_compression_steps' in self._positioning and self._positioning['debug_optimization_compression_steps'] > 0:
                self.debug_optimization_compression_steps = self._positioning['debug_optimization_compression_steps']
            for family in gr_root_individual.connected_parent_families:
                self._compress_chart_ancestor_graph(family)
            self._move_child_to_center_between_parents(gr_root_individual)

            # compressed chart should be aligned left
            _, min_index_x, max_index_x = self._check_compressed_x_position(
                False, self.position_to_person_map)
            self._move_individual_and_ancestors(
                root_individual.graphical_representations[0],
                sorted(list(gr_root_individual.get_x_position().values()))[0][2],
                -(min_index_x-old_x_min_index)*1)
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
            self._check_compressed_x_position(
                False, self.position_to_person_map)

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
        self._debug_check_collision_counter = 0
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
                self.select_individuals(root_individual, generations, filter=local_filter_lambda, discovery_cache=[])

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
                if root_individual.has_graphical_representation() and root_individual.graphical_representations[0].get_x_position() is not None:
                    continue
                cof_family_id = None
                if root_individual.child_of_family_id:
                    cof_family_id = root_individual.child_of_family_id[0]
                spouse_family = None
                vms = root_individual.graphical_representations[0].visible_marriages
                if vms:
                    for vm in vms:
                        self.place_selected_individuals(
                            root_individual.graphical_representations[0], None, vm.family, self._instances[('f', cof_family_id)], x_pos, [], [])
                        spouse_family = vm.family.graphical_representations[0]
                else:
                    self.place_selected_individuals(
                        root_individual.graphical_representations[0], None, None, self._instances[('f', cof_family_id)], x_pos, [], [])

                x_pos = max(0, self.max_x_index)

            for settings in self._chart_configuration['root_individuals']:
                root_individual_id = settings['individual_id']
                generations = settings['generations']
                try:
                    self.modify_layout(root_individual_id)
                except Exception as e:
                    pass

            for gir in self.gr_individuals:
                color = None
                if color_lambda:
                    color = color_lambda(gir)
                if color_lambda is None or color is None:
                    if self._formatting['fathers_have_the_same_color']:
                        color = self._instances.color_generator_fathers_have_the_same_color(gir)
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
                if color_lambda:
                    color = color_lambda(gir)
                if color_lambda is None or color is None:
                    if self._formatting['fathers_have_the_same_color']:
                        color = self._instances.color_generator_fathers_have_the_same_color(gir)
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
