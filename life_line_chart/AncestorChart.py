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
    of that, pedigree collapse can be visualized.
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
            'discovery_blacklist': [],
            'ancestor_placement': {}
    }
    DEFAULT_CHART_CONFIGURATION.update(BaseSVGChart.DEFAULT_CHART_CONFIGURATION)

    SETTINGS_DESCRIPTION = _strings

    def __init__(self, positioning=None, formatting=None, instance_container=None):
        BaseSVGChart.__init__(self, positioning, formatting, instance_container)

        # configuration of this chart
        self._chart_configuration.update(AncestorChart.DEFAULT_CHART_CONFIGURATION)

    def select_individuals(self, individual, generations=None, filter=None, discovery_cache=None):
        """
        Select individuals to show. This is done by creating instances of graphical representations.

        Args:
            individual (BaseIndividual): starting point for selection
            generations (int): number of generations to search for ancestors.
            filter (lambda, optional): lambda(BaseIndividual) : return Boolean. Defaults to None.
            discovery_cache (list): list of discovered individuals
        """

        if filter and filter(individual):
            return
        if discovery_cache is None:
            discovery_cache = []

        needs_instance = not individual.has_graphical_representation()

        gr_individual = self._create_individual_graphical_representation(
            individual, not self._positioning['unique_graphical_representation'])

        if needs_instance:
            discovery_cache.append(individual.individual_id)
            gr_individual.debug_label = '\n' + str(len(discovery_cache))

        if gr_individual is None:
            return

        go_deeper = True
        child_of_families = individual.child_of_families[:1]
        for child_of_family in child_of_families:
            gr_child_of_family = self._create_family_graphical_representation(
                child_of_family, not self._positioning['unique_graphical_representation'])
            gr_child_of_family.add_visible_children(gr_individual)

            if generations > 0 or generations < 0:
                father, mother = child_of_family.get_husband_and_wife()
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
                if mother:
                    gr_mother = self.select_individuals(
                        mother, generations - 1 if go_deeper else 0,
                        filter=filter,
                        discovery_cache=discovery_cache)
                    if gr_mother and gr_child_of_family.gr_wife is None:
                        gr_child_of_family.gr_wife = gr_mother
        return gr_individual

    def select_family_children(self, gr_family, filter=None):
        """
        Select children of a family. This is done by creating instances of graphical representations.

        Args:
            gr_family (GraphicalFamily): starting point for selection
            filter (lambda, optional): lambda(BaseIndividual) : return Boolean. Defaults to None.
        """

        if gr_family is None:
            return
        for child in gr_family.family.get_children():
            if filter and filter(child):
                continue
            if child in [vc.individual for vc in gr_family.visible_children]:
                continue

            if not child.has_graphical_representation() or not self._positioning['unique_graphical_representation']:
                gr_child = self._create_individual_graphical_representation(
                    child, not self._positioning['unique_graphical_representation'])

                if gr_child is None:
                    return
                gr_child.qualified_for_placement = False
                gr_child.color = (0,0,0)

                gr_family.add_visible_children(gr_child)
                gr_child.ancestor_chart_parent_family_placement = gr_family, None

    def place_selected_individuals(self, gr_individual, gr_spouse_family, gr_child_of_family, x_offset=0, discovery_cache=None, root_node_discovery_cache=None):
        """
        Place the graphical representations in direction of x

        Args:
            gr_individual (GraphicalIndividual): individual
            gr_spouse_family (GraphicalFamily): Spouse family of this individual
            gr_child_of_family (GraphicalFamily): child-of-family of this individual
            x_offset (int): starting position
            discovery_cache (list): list of discovered individuals
            root_node_discovery_cache (list): list of discovered individuals
        """
        if discovery_cache is None:
            discovery_cache = []
        if root_node_discovery_cache is None:
            root_node_discovery_cache = []

        individual = gr_individual.individual
        if gr_child_of_family:
            child_of_family = gr_child_of_family.family
        else:
            child_of_family = None
        if gr_spouse_family:
            spouse_family = gr_spouse_family.family
        else:
            spouse_family = None
        if (gr_individual, gr_spouse_family) in discovery_cache:
            # if this individual has already been placed in this marriage family
            return

        # logger.debug(f"discovering {individual.plain_name}")
        x_position = x_offset
        self.min_x_index = min(self.min_x_index, x_position)

        # +----------------------------------------------
        # | start with going back to the actual root node
        # +----------------------------------------------

        # get siblings
        child_of_families = gr_individual.connected_parent_families
        if gr_child_of_family and gr_child_of_family.visible_children:
            siblings = gr_child_of_family.visible_children
        else:
            siblings = [gr_individual]

        gr_spouse_family_g_id = gr_spouse_family.g_id if gr_spouse_family else None
        gr_child_of_family_g_id = gr_child_of_family.g_id if gr_child_of_family else None

        placement_config = self._chart_configuration['ancestor_placement'].get(gr_child_of_family_g_id)
        if placement_config and gr_child_of_family:
            place_ancestors_here = \
                (gr_spouse_family_g_id == placement_config[0]) and \
                (gr_individual.g_id == placement_config[1])
        else:
            # define where to place the ancestors
            # choose first marriage (if visibly married) of oldest visible sibling
            place_ancestors_here = \
                gr_individual == [s for s in siblings if s.qualified_for_placement][0] and \
                (not gr_individual.visible_marriages or gr_spouse_family == gr_individual.visible_marriages[0])

        # go back to root node
        root_node_discovery_cache += siblings
        if gr_spouse_family:
            for gr_child in gr_spouse_family.visible_children:
                c_vms = gr_child.visible_marriages
                if not c_vms:
                    c_vms = [None]
                for c_m in c_vms:
                    if gr_child not in root_node_discovery_cache:
                        if gr_child.get_position_dict() is None:
                            self.place_selected_individuals(
                                gr_child, c_m, gr_spouse_family,
                                x_position, discovery_cache, root_node_discovery_cache)

        if (gr_individual, spouse_family) in discovery_cache:
            # when this node was handled by the place_selected_individuals call in a root node
            # then we should return here
            return

        # +----------------------------------------------
        # | add father branch, siblings and mother branch
        # +----------------------------------------------

        def add_parent(parent_variable_name, x_position):
            """
            Add mother or father to the chart

            Args:
                parent_variable_name (str): 'husb' or 'wife'
                x_position (int): x position index

            Returns:
                int: new x position index
            """
            for gr_local_child_of_family in child_of_families:
                gr_parent = getattr(
                    gr_local_child_of_family, 'gr_' + parent_variable_name)

                if gr_parent and place_ancestors_here:
                    if not gr_parent.has_position_vector(gr_local_child_of_family):
                        gr_parent_families = gr_parent.connected_parent_families
                        if gr_parent_families:
                            gr_parent_family = gr_parent_families[0]
                        else:
                            gr_parent_family = None

                        gr_individual.ancestor_chart_parent_family_placement = gr_local_child_of_family, gr_spouse_family
                        self.place_selected_individuals(
                            gr_parent, gr_local_child_of_family, gr_parent_family,
                            x_position, discovery_cache, root_node_discovery_cache)
                        width = gr_parent.get_ancestor_width(
                            gr_local_child_of_family)
                        setattr(gr_local_child_of_family, parent_variable_name + '_width',
                            lambda gr=gr_parent, cof=gr_local_child_of_family: gr.get_ancestor_width(cof)
                            )
                        x_position += width
                    else:
                        logger.debug('Second try to add parent! This should not happen. '+str(gr_parent))
            return x_position

        # add the father branch
        x_position = add_parent('husb', x_position)

        # add the main individual and its visible siblings
        for gr_sibling in siblings:
            # only set x position of cof if ancestors shall be placed here and have not been added yet!
            # this can be a detached head, or an x position shared with a spouse family (-> ancestor_placement_marriage)
            child_of_family_must_be_added = not gr_sibling.has_position_vector(gr_child_of_family) and place_ancestors_here

            # spouse family position should be added only if sibling is gr_individual
            # => So only if we are at the right x position
            spouse_family_must_be_added = not gr_sibling.has_position_vector(gr_spouse_family)
            sibling = gr_sibling.individual
            if sibling.individual_id == individual.individual_id:
                if spouse_family_must_be_added:
                    if child_of_family_must_be_added:
                        # not added yet, so this is the primary cof placement
                        gr_sibling.set_position_vector(
                            x_position, gr_child_of_family, True)
                        # either this has already been set when adding the parent, or it should be added here!
                        gr_sibling.ancestor_placement_marriage = gr_spouse_family
                    # add new position of this spouse family
                    gr_sibling.set_position_vector(
                        x_position, gr_spouse_family)
                    x_position += 1
            elif child_of_family_must_be_added:
                # add siblings beside the main sibling
                gr_sibling.set_position_vector(
                    x_position,
                    gr_child_of_family, True)
                x_position += 1

        if gr_child_of_family is not None and gr_child_of_family.gr_husb is None and gr_child_of_family.gr_wife is None:
            if gr_child_of_family.strongly_connected_children[0] is None and place_ancestors_here:
                # add the strong connection between siblings and their parent family, if
                # the parents are not visible, but their family has a graphical representation.
                # -> these are the families where the discovery stops due to the generation limit.
                #    but since siblings in these families are placed together, they have to share
                #    the strong connection to the family.
                gr_individual.ancestor_chart_parent_family_placement = gr_child_of_family, gr_spouse_family

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
        discovery_cache.append((gr_individual, gr_spouse_family))

    def _flip_family(self, gr_family):
        """
        Flip family. The three sections change order
        - father and ancestors
        - individual + siblings
        - mother and ancestors

        Args:
            gr_family (GraphicalFamily): family instance
        """
        # logger.debug(f"flipping {gr_family}")
        def func(gr_family):
            xpos_w = []
            for gr_f, gr_i in gr_family.gr_wife.get_all_ancestors():
                xpos_w.append(gr_i.get_position_dict(gr_f.family)[1])
            xpos_h = []
            for gr_f, gr_i in gr_family.gr_husb.get_all_ancestors():
                xpos_h.append(gr_i.get_position_dict(gr_f.family)[1])
            return (max(xpos_w), min(xpos_w), max(xpos_w)- min(xpos_w), gr_family.gr_wife.get_ancestor_range(gr_family)),(max(xpos_h), min(xpos_h), max(xpos_h)- min(xpos_h), gr_family.gr_husb.get_ancestor_range(gr_family))
        if gr_family.gr_husb is None and gr_family.gr_wife is None:
            return
        if gr_family.gr_husb is not None:
            husb_x_pos = gr_family.gr_husb.get_x_index(gr_family.g_id)
            husb_width = gr_family.husb_width()
        else:
            husb_x_pos = None
            husb_width = 0
        if gr_family.gr_wife is not None:
            wife_x_pos = gr_family.gr_wife.get_x_index(gr_family.g_id)
            wife_width = gr_family.wife_width()
        else:
            wife_x_pos = None
            wife_width = 0
        vcs = gr_family.visible_children
        children_width = len(vcs)
        if children_width == 0:
            if gr_family.gr_husb is None or gr_family.gr_wife is None:
                return
            children_x_center = (husb_x_pos + wife_x_pos)/2.0
        else:
            children_x_positions = [gr_child.get_position_dict(gr_family)[1] for gr_child in vcs]
            children_x_center = sum(children_x_positions)*1.0/children_width

        if wife_x_pos and children_x_center < wife_x_pos or husb_x_pos and husb_x_pos < children_x_center:
            husb_x_delta = wife_width + children_width
            wife_x_delta = -husb_width - children_width
            child_x_delta = wife_width - husb_width
        else:
            husb_x_delta = -wife_width - children_width
            wife_x_delta = husb_width + children_width
            child_x_delta = husb_width - wife_width

        for gr_child in vcs:
            for gr_parent_family in gr_child.connected_parent_families:
                self._move_single_individual(
                    gr_child, gr_parent_family, child_x_delta)

        if gr_family.gr_husb:
            self._move_individual_and_ancestors(gr_family.gr_husb, gr_family, husb_x_delta)
        if gr_family.gr_wife:
            self._move_individual_and_ancestors(gr_family.gr_wife, gr_family, wife_x_delta)
        self._instances.ancestor_width_cache.clear()

    def _compress_single_individual_position(self, gr_individual, gr_cof, direction, nSteps=50000):
        """
        Move single gr_individual until it collides.
        """
        if nSteps <= 0:
            return
        try:
            i = 0
            while i < nSteps:
                i += 1
                self._move_single_individual(gr_individual, gr_cof, direction)
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
                    self._move_single_individual(gr_individual, gr_cof, -direction)
                    self._check_compressed_x_position(True)
                except:
                    pass
                else:
                    break

    def _compress_chart_ancestor_graph(self, gr_family):
        """
        Compress the chart horizontally.

        Args:
            gr_family (GraphicalFamily): graphical family representation instance
        """
        gr_individuals = []
        if gr_family is None:
            return

        family_was_flipped = False
        x_pos_husb = None
        x_pos_wife = None
        gr_husb = gr_family.gr_husb
        gr_wife = gr_family.gr_wife
        if gr_husb:
            x_pos_husb = gr_husb.get_x_index(gr_family.g_id)
            if gr_family.husb.child_of_families and gr_family.husb.child_of_families[0]:# \
                gr_individuals.append((1, gr_husb))
        if gr_wife:
            x_pos_wife = gr_wife.get_x_index(gr_family.g_id)
            if gr_family.wife.child_of_families and gr_family.wife.child_of_families[0]:# \
                gr_individuals.append((-1, gr_wife))

        vcs = gr_family.visible_children
        children_width = len(vcs)
        children_x_positions = [gr_child.get_x_index(gr_family.g_id) for gr_child in vcs]
        children_x_center = sum(children_x_positions)*1.0/children_width
        blocked_positions = children_x_positions.copy()
        if x_pos_husb: blocked_positions.append(x_pos_husb)
        if x_pos_wife: blocked_positions.append(x_pos_wife)

        if x_pos_husb and children_x_center < x_pos_husb or x_pos_wife and x_pos_wife < children_x_center:
            family_was_flipped = True

        for _, gr_individual in sorted(gr_individuals):
            gr_cofs = gr_individual.connected_parent_families
            for gr_cof in gr_cofs:
                try:
                    self._compress_chart_ancestor_graph(gr_cof)
                except KeyError as e:
                    pass
            if self.debug_optimization_compression_steps <= 0:
                break
        if self.debug_optimization_compression_steps <= 0:
            return
        for original_direction_factor, gr_individual in sorted(gr_individuals):
            if gr_individual is None:
                continue
            i = 0
            i2 = 0
            if family_was_flipped:
                direction_factor = - original_direction_factor
            else:
                direction_factor = original_direction_factor

            this_individual_x_pos = gr_individual.get_x_index(gr_family.g_id)
            if not gr_individual.has_position_vector(gr_family):
                continue
            if this_individual_x_pos and (this_individual_x_pos + direction_factor*1) in blocked_positions:
                continue

            try:
                while i < 50000:
                    if (i+1)%1000 == 0:
                        logger.warning(f'i {i} for gr_individual {gr_individual}')
                    i += 1
                    self._move_individual_and_ancestors(
                        gr_individual, gr_family, direction_factor*1)
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
                            gr_individual, gr_family, -direction_factor*1)
                        self.debug_optimization_compression_steps -= 1
                        if self.debug_optimization_compression_steps <= 0:
                            break
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

        if self.debug_optimization_compression_steps <= 0:
            return
        for _, gr_individual in sorted(gr_individuals):
            self._move_child_to_center_between_parents(gr_individual)
            self.debug_optimization_compression_steps -= 1
            if self.debug_optimization_compression_steps <= 0:
                break

    def _move_child_to_center_between_parents(self, gr_individual):
        """
        Move an individual to the center between its parents.

        Args:
            gr_individual (GraphicalIndividual): individual
        """
        gr_cofs = gr_individual.connected_parent_families
        for gr_cof in gr_cofs:
            husb_x_pos = None
            gr_husb = gr_cof.gr_husb
            gr_wife = gr_cof.gr_wife
            if gr_husb is not None:
                husb_x_pos = gr_husb.get_x_index(gr_cof.g_id)
                middle_x_pos = husb_x_pos
            wife_x_pos = None
            if gr_wife is not None:
                wife_x_pos = gr_wife.get_x_index(gr_cof.g_id)
                middle_x_pos = wife_x_pos
            if husb_x_pos and wife_x_pos:
                middle_x_pos = (husb_x_pos + wife_x_pos)/2.0
            elif husb_x_pos is None and wife_x_pos is None:
                continue
            this_individual_x_pos = gr_individual.get_x_index(gr_cof.g_id)
            nSteps = int(abs(this_individual_x_pos - middle_x_pos))
            if nSteps > 0:
                if nSteps > 1000:
                    logger.error(f'nSteps {nSteps} for gr_individual {gr_individual}')
                direction = -1 if this_individual_x_pos > middle_x_pos else 1
                self._compress_single_individual_position(
                    gr_individual, gr_cof, direction, nSteps)

    def modify_layout(self, root_individual_id):
        """
        Improvement of individual placement.

        Args:
            root_individual_id (str): root individual id used as root node for compression
        """
        failed, _, _ = self.check_unique_x_position()

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
                for gr_family in gr_child.visible_marriages:
                    if gr_family is None:
                        continue
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
                                        str((gr_family, gr_family.family_id, ov)) + str(nSteps))
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
                f"flipping reduced the cross connections by {old_width - width} (i.e. from {old_width} to {width})")

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
            for gr_family in gr_root_individual.connected_parent_families:
                self._compress_chart_ancestor_graph(gr_family)
            if self.debug_optimization_compression_steps > 0:
                self._move_child_to_center_between_parents(gr_root_individual)

            # compressed chart should be aligned left
            _, min_index_x, max_index_x = self._check_compressed_x_position(
                False, self.position_to_person_map)
            self._move_individual_and_ancestors(
                gr_root_individual,
                sorted(list(gr_root_individual.get_position_dict().values()))[0][2],
                -(min_index_x-old_x_min_index)*1)
            keys = sorted(list(self.position_to_person_map.keys()))
            for key in keys:
                self.position_to_person_map[key - (
                    min_index_x - old_x_min_index) * 1] = self.position_to_person_map.pop(key)
            width = (max_index_x - min_index_x) + 1
            self.min_x_index = 0
            self.max_x_index = width
            logger.info(
                f"compression reduced the total width by {old_width - width} (i.e. from {old_width} to {width})")
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
                if family.has_graphical_representation():
                    self.select_family_children(family.graphical_representations[0], filter=local_filter_lambda)

            x_pos = 0
            for settings in self._chart_configuration['root_individuals']:
                root_individual_id = settings['individual_id']
                generations = settings['generations']
                root_individual = self._instances[(
                    'i', root_individual_id)]
                if root_individual.has_graphical_representation() and root_individual.graphical_representations[0].get_position_dict() is not None:
                    continue
                gr_root_individual = root_individual.graphical_representations[0]
                cof_family_id = None
                if root_individual.child_of_family_id:
                    cof_family_id = root_individual.child_of_family_id[0]
                cof_family = self._instances[('f', cof_family_id)]
                gr_cof_family = None
                if cof_family:
                    gr_cof_family = cof_family.graphical_representations[0]
                spouse_family = None
                vms = gr_root_individual.visible_marriages
                if vms:
                    for vm in vms:
                        gr_spouse_family = vm
                        self.place_selected_individuals(
                            gr_root_individual, gr_spouse_family, gr_cof_family, x_pos)
                else:
                    self.place_selected_individuals(
                        gr_root_individual, None, gr_cof_family, x_pos)

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
