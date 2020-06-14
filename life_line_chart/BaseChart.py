import os
from copy import deepcopy
import logging

from .GraphicalFamily import GraphicalFamily
from .GraphicalIndividual import GraphicalIndividual
from .Exceptions import LifeLineChartCollisionDetected, LifeLineChartCannotMoveIndividual
from .Translation import get_strings

logger = logging.getLogger("life_line_chart")

_strings = get_strings('BaseChart')


class BaseChart():
    """
    Base class for life line charts.
    """
    DEFAULT_FORMATTING = {
        'margin_left': 50,
        'margin_right': 50,
        'margin_year_max': 5,
        'margin_year_min': 10,
        'vertical_step_size': 40,
        'relative_line_thickness': 0.4,
        'total_height': 1500,
        'display_factor': -1,
        'font_size_description': 0.7,
        'font_description_letter_offset': [str(30 / 12.0)],
        'font_name': 'Arial',
        'birth_label_active': True,
        'birth_label_along_path': False,
        'birth_label_rotation': 0,
        'birth_label_anchor': 'middle',
        'birth_label_wrapping_active': True,
        'birth_label_letter_x_offset': 0,
        'birth_label_letter_y_offset': 1,
        'fade_individual_color': True,
        'fade_individual_color_black_age': 200,
        'marriage_label_active': False,
        'no_ring': False,
        'death_label_active': True,
        'death_label_rotation': 0,
        'death_label_anchor': 'middle',
        'death_label_wrapping_active': True,
        'death_label_letter_x_offset': 0,
        'death_label_letter_y_offset': -1,
        'warp_shape': 'normal',
        'family_shape': 0,
        'individual_photo_active': False,
        'individual_photo_relative_size': 2.5,
        'debug_visualize_connections': True,
        'debug_visualize_ambiguous_placement': True,
        'coloring_of_individuals': 'unique'
    }
    DEFAULT_POSITIONING = {
    }
    DEFAULT_CHART_CONFIGURATION = {
    }
    SETTINGS_DESCRIPTION = _strings

    # TODO: extract base class for other chart types
    _graphical_family_class = GraphicalFamily
    # TODO: extract base class for other chart types
    _graphical_individual_class = GraphicalIndividual

    def __init__(self, positioning=None, formatting=None, instance_container=None):
        self.position_to_person_map = {}
        self._positioning = deepcopy(self.DEFAULT_POSITIONING)
        if positioning:
            self._positioning.update(positioning)
        self._formatting = deepcopy(self.DEFAULT_FORMATTING)
        if formatting:
            self._formatting.update(formatting)
        self._instances = instance_container
        self._instances.graph_link = self
        self._instances[('i', None)] = None
        self.gr_individuals = []
        self.gr_families = []
        # strong graphical connections which must not be broken by optimization algorithms

        self.additional_graphical_items = {}
        logger.debug('finished creating instances')

        self.min_x_index = 10000000
        self.max_x_index = -10000000
        self.min_ordinal = None
        self.max_ordinal = None
        self.chart_min_ordinal = None
        self.chart_max_ordinal = None

        # configuration of this chart
        self._chart_configuration = deepcopy(self.DEFAULT_CHART_CONFIGURATION)

        self._backup_positioning = None
        self._backup_formatting = None
        self._backup_chart_configuration = None

    def instantiate_all(self):
        """
        instantiate all families and individuals
        """
        self._instances.instantiate_all(self=self._instances)

    def set_formatting(self, formatting):
        """
        set the formatting configuration of the chart

        Args:
            formatting (dict): formatting dict
        """
        self._formatting.update(formatting)

    def set_positioning(self, positioning):
        """
        set the positioning configuration of the chart

        Args:
            positioning (dict): positioning dict
        """
        self._positioning.update(positioning)

    def set_chart_configuration(self, chart_configuration):
        """
        set the chart configuration of the chart

        Args:
            chart_configuration (dict): chart configuration dict
        """
        self._chart_configuration.update(chart_configuration)

    def get_chart_configuration(self):
        """
        get the chart configuration

        Returns:
            dict: chart configuration dict
        """
        return deepcopy(self._chart_configuration)

    def _create_individual_graphical_representation(self, individual):
        """
        create a graphical representation for an individual

        Args:
            individual (BaseIndividual): individual

        Returns:
            ancestor_chart_inidividual: created instance
        """
        new_instance = self._graphical_individual_class(
            self._instances, individual.individual_id)
        if new_instance.birth_date is None or new_instance.death_date is None:
            del new_instance
            return None
        self.gr_individuals.append(new_instance)
        new_instance.g_id = (len(individual.graphical_representations) - 1, individual.individual_id)
        return new_instance

    def _create_family_graphical_representation(self, family):
        """
        create a graphical representation for a family

        Args:
            family (BaseFamily): family

        Returns:
            GraphicalFamily: created instance
        """
        if not family.graphical_representations:
            new_instance = self._graphical_family_class(
                self._instances, family.family_id)
            self.gr_families.append(new_instance)
        else:
            new_instance = family.graphical_representations[0]
            # print('the family was added twice:'+family.family_id)
        new_instance.g_id = (len(family.graphical_representations) - 1, family.family_id)
        return new_instance

    def _calculate_sum_of_distances(self):
        """
        sum of distances between different families of one individual

        Returns:
            tuple: (total_distance, list_of_linked_individuals)
        """
        total_distance = 0
        list_of_linked_individuals = {}
        for index, gr_individual in enumerate(self.gr_individuals):
            x_positions = gr_individual.get_x_position()
            distance_of_this_individual = 0
            if x_positions:
                vector = [p[1] for k, p in x_positions.items()]
                distance_of_this_individual += max(vector) - min(vector)
            total_distance += distance_of_this_individual
            if distance_of_this_individual > 0:
                list_of_linked_individuals[(
                    distance_of_this_individual, index)] = gr_individual
        return total_distance, list_of_linked_individuals

    def _move_single_individual(self, gr_individual, family, x_index_offset):
        """
        move a single individual vertically

        Args:
            individual (BaseIndividual): individual instance
            family (BaseFamily): family instance
            x_index_offset (int): vertical offset

        Returns:
            dict: position dict of the graphical individual representation
        """
        x_pos = gr_individual.get_x_position()
        positions = sorted(list(x_pos.values()))
        if family is not None:
            family_id = family.family_id
        else:
            family_id = None

        for position in positions:
            if position[2]:
                other_family_id = position[2].family_id
            else:
                other_family_id = position[2]
            if family_id == other_family_id:
                continue
            if family_id in x_pos and position[1] == x_pos[family_id][1] and (position[3] or x_pos[family_id][3]):
                x_pos[other_family_id] = (
                    x_pos[other_family_id][0],
                    x_pos[other_family_id][1]+x_index_offset,
                    x_pos[other_family_id][2],
                    x_pos[other_family_id][3],
                )
        if family_id in x_pos:
            x_pos[family_id] = (
                x_pos[family_id][0],
                x_pos[family_id][1]+x_index_offset,
                x_pos[family_id][2],
                x_pos[family_id][3],
            )
        else:
            raise LifeLineChartCannotMoveIndividual(
                'This family does not exist')
        return x_pos

    def _move_individual_and_ancestors(self, gr_individual, family, x_index_offset):
        """
        move an individual and its ancestors vertically. Only ancestors are moved, which are strongly coupled with the individual.

        Args:
            gr_individual (GraphicalIndividual): gr_individual instance
            family (BaseFamily): family instance
            x_index_offset (int): vertical offset
        """

        if family is None:
            family_id = family
        else:
            family_id = family.family_id

        # move this individual
        x_pos = self._move_single_individual(
            gr_individual, family, x_index_offset)

        if gr_individual.first_marriage_strongly_connected_to_parent_family == False:
            # if the head of the individual is detached, then dont move anyone else
            return
        vms = gr_individual.visible_marriages
        if vms:
            # if this is not the first marriage, dont move anyone else
            if vms[0] != family:
                return

        cofs = gr_individual.individual.child_of_families
        if len(cofs) == 0 or not cofs[0].has_graphical_representation():
            return
        cof = cofs[0]
        gr_cof = cofs[0].graphical_representations[0]

        #for strongly_connected_parent_family in gr_individual.connected_parent_families:
        strongly_connected_parent_family = gr_individual.strongly_connected_parent_family
        if strongly_connected_parent_family:
            if strongly_connected_parent_family.gr_husb:
                # if cof.gr_husb.get_x_position() and len(cof.gr_husb.get_x_position()) == 1:
                    self._move_individual_and_ancestors(
                        strongly_connected_parent_family.gr_husb, strongly_connected_parent_family, x_index_offset)
            if strongly_connected_parent_family.gr_wife:
                # if cof.gr_wife.get_x_position() and len(cof.gr_wife.get_x_position()) == 1:
                    self._move_individual_and_ancestors(
                        strongly_connected_parent_family.gr_wife, strongly_connected_parent_family, x_index_offset)
        # print (gr_individual.get)
        for gr_child_individual in gr_cof.visible_children:
            if gr_child_individual == gr_individual:
                continue
            x_pos = self._move_single_individual(
                gr_child_individual, cof, x_index_offset)

    def _flip_family(self, gr_family):
        """
        Flip family. The three sections change order
        - father and ancestors
        - individual + siblings
        - mother and ancestors

        Args:
            gr_family (GraphicalFamily): family instance
        """
        if gr_family.gr_husb is None and gr_family.gr_wife is None:
            return
        if gr_family.gr_husb is not None:
            husb_x_pos = gr_family.gr_husb.get_x_position()[
                gr_family.family_id][1]
            husb_width = gr_family.husb_width()
        else:
            husb_x_pos = None
            husb_width = 0
        if gr_family.gr_wife is not None:
            wife_x_pos = gr_family.gr_wife.get_x_position()[
                gr_family.family_id][1]
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
            children_x_positions = [gr_child.get_x_position(gr_family)[1] for gr_child in vcs]
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
            pos = list(gr_child.get_x_position().values())
            self._move_single_individual(
                gr_child, pos[0][2], child_x_delta)

        if gr_family.gr_husb:
            self._move_individual_and_ancestors(gr_family.gr_husb, gr_family, husb_x_delta)
        if gr_family.gr_wife:
            self._move_individual_and_ancestors(gr_family.gr_wife, gr_family, wife_x_delta)
        self._instances.ancestor_width_cache.clear()

    def _check_compressed_x_position(self, early_raise, position_to_person_map=None, min_distance=15):
        """
        check the compressed chart for overlapping individuals

        Args:
            early_raise (bool): raise an exception if the first individual overlap was found

        Raises:
            LifeLineChartCollisionDetected: overlapping found

        Returns:
            [type]: [description]
        """
        v = {}
        collisions = []
        min_x = 999999
        max_x = 0
        if position_to_person_map is not None:
            position_to_person_map.clear()

        def check_collision(gr_individual_a, start_y_a, end_y_a, gr_individual_b, start_y_b, end_y_b):
            if gr_individual_a == gr_individual_b:
                return False
            start_position_a = start_y_a - 365*min_distance
            start_position_b = start_y_b - 365*min_distance
            end_position_a = end_y_a + 365*min_distance
            end_position_b = end_y_b + 365*min_distance
            if ((start_position_a - start_position_b)
                * (start_position_a - end_position_b) < 0 or
                (end_position_a - start_position_b)
                * (end_position_a - end_position_b) < 0 or
                (start_position_b - start_position_a)
                * (start_position_b - end_position_a) < 0 or
                (end_position_b - start_position_a)
                    * (end_position_b - end_position_a) < 0):
                    return True
            return False

        # assign the individuals to all x_indices in which they appear
        for gr_individual in self.gr_individuals:
            x_pos_vector = list(gr_individual.get_x_position().values())

            for i, value in enumerate(x_pos_vector):
                x_index = value[1]
                # if value[3]:
                #     continue
                # if x_index < 0:
                #     if early_raise:
                #         raise LifeLineChartCollisionDetected(gr_individual)
                #     collisions.append((gr_individual, None))
                if x_index not in v:
                    v[x_index] = []

                    if position_to_person_map is not None:
                        position_to_person_map[x_index] = []
                if i == 0:
                    start_y = gr_individual.birth_date_ov
                else:
                    start_y = x_pos_vector[i][0]
                if i < len(x_pos_vector) - 1:
                    end_y = x_pos_vector[i+1][0]
                else:
                    end_y = gr_individual.death_date_ov

                if start_y == end_y:
                    # happens in ancestor charts if spouse family is None (i.e. the root individual)
                    continue

                # position_to_person_map[x_index].append(
                #     PositionToPersonMapItem(
                #     start_y,
                #     end_y,
                #     gr_individual
                # ))
                if position_to_person_map is not None:
                    position_to_person_map[x_index].append({
                        'start': start_y,
                        'end': end_y,
                        'individual': gr_individual
                    })

                v[x_index].append((gr_individual, start_y, end_y))#, gr_individual.birth_date_ov, gr_individual.death_date_ov))
                max_x = max(max_x, x_index)
                min_x = min(min_x, x_index)
        if len(collisions) > 0:
            raise LifeLineChartCollisionDetected()

        # block every x_index from birth to death in which an individual appears
        for x_index, gr_individuals in v.items():
            for index, (gr_individual_a, start_y_a, end_y_a) in enumerate(gr_individuals):
                for gr_individual_b, start_y_b, end_y_b in gr_individuals[index+1:]:
                    if check_collision(gr_individual_a, start_y_a, end_y_a, gr_individual_b, start_y_b, end_y_b):
                        if early_raise:
                            raise LifeLineChartCollisionDetected(
                                gr_individual_a, gr_individual_b)
                        collisions.append(
                            (gr_individual_a, gr_individual_b))
        # if len(collisions) > 0:
        #     raise RuntimeError()
        return collisions, min_x, max_x

    def check_unique_x_position(self):
        """
        check if every individual position has a unique vertical slot

        Raises:
            RuntimeError: overlap was found

        Returns:
            tuple: (list of failures, min_x_index, max_x_index)
        """
        failed = []
        v = {}
        for gr_individual in self.gr_individuals:
            x_pos = gr_individual.get_x_position()
            for value in x_pos.values():
                x_index = value[1]
                if value[3]:
                    continue
                # if not value[2] is None and gr_individual.individual_id not in value[2].children_individual_ids:
                #     continue
            #     x_indices.add(x_index)
            #     index_map[x_index] = value[2]
            # for x_index in x_indices:
                if x_index not in v:
                    v[x_index] = gr_individual.individual_id
                else:
                    failed.append(x_index)
                    # value = index_map[x_index]
                    logger.error(
                        "failed: " + str((x_index, value[2].family_id, gr_individual.individual.plain_name, v[x_index])))
                    # raise RuntimeError((x_index, key, gr_individual.individual.plain_name))
        full_index_list = list(sorted(v.keys()))
        for i in range(max(full_index_list)):
            if i not in full_index_list:
                if self._formatting['debug_visualize_ambiguous_placement']:
                    gr_individual.items.append({
                        'type': 'rect',
                        'config': {
                            'insert': (self._map_x_position(i), 0),
                            'size': (self._formatting['relative_line_thickness']*self._formatting['vertical_step_size'], self._formatting['total_height']),
                            'fill': 'black',
                            'fill-opacity': "0.5"
                        }
                    })
                failed.append(('missing', i))
        return failed, full_index_list[0], full_index_list[-1]

    def _map_y_position(self, ordinal_value):
        """
        map date information to y axis

        Args:
            ordinal_value (float or int): ordinal value of the datetime

        Returns:
            float: y position
        """
        return (
            + (ordinal_value - self.chart_min_ordinal)/(self.chart_max_ordinal-self.chart_min_ordinal) *
            self._formatting['total_height'] *
            self._formatting['display_factor']
            - self._formatting['total_height'] *
            (self._formatting['display_factor']-1)/2
        )

    def _map_x_position(self, x_index):
        """
        map vertical index to x axis

        Args:
            x_index (float or int): vertical index

        Returns:
            float: x position
        """
        return self._formatting['margin_left'] + x_index*self._formatting['vertical_step_size']

    def _map_position(self, pos_x, pos_y):
        """
        map date information and vertical index to x and y axis. This function also supports warping of the whole chart.

        Args:
            pos_x (float or int): vertical index
            pos_y (float or int): ordinal value of the datetime

        Returns:
            tuple: (x position, y position)
        """
        from math import pi, sin
        if self._formatting['warp_shape'] == 'sine':
            y_rel = (1-sin((1-(pos_y - self.min_ordinal) /
                            (self.max_ordinal - self.min_ordinal))*pi/2))*0.5
            x_av = (self.max_x_index + self.min_x_index)/2

            return self._map_x_position(pos_x*(1-y_rel) + y_rel*x_av), self._map_y_position(pos_y)
        elif self._formatting['warp_shape'] == 'triangle':
            y_rel = (pos_y - self.min_ordinal) / \
                (self.max_ordinal - self.min_ordinal)*0.8
            x_av = (self.max_x_index + self.min_x_index)/2

            return self._map_x_position(pos_x*(1-y_rel) + y_rel*x_av), self._map_y_position(pos_y)
        else:
            return self._map_x_position(pos_x), self._map_y_position(pos_y)

    def _orientation_angle(self, pos_x, pos_y):
        """
        get the rotation of the lines which is caused by the warping of the whole chart

        Args:
            pos_x (float or int): vertical index
            pos_y (float or int): ordinal value of the datetime

        Returns:
            float: angle
        """
        from math import pi, sqrt, asin
        p1 = self._map_position(pos_x, pos_y-0.5)
        p2 = self._map_position(pos_x, pos_y+0.5)
        gegen_kathete = p2[0]-p1[0]
        an_kathete = p2[1]-p1[1]
        hypotenuse = sqrt(gegen_kathete*gegen_kathete + an_kathete*an_kathete)
        angle = asin(gegen_kathete/hypotenuse)
        angle_deg = angle/pi*180

        return angle_deg

    def _inverse_y_delta(self, delta_y):
        """
        map back a delta display size to the delta ordinal value

        Args:
            delta_y (float): difference of display size

        Returns:
            float: difference of ordinal value
        """
        return delta_y / (self._formatting['total_height'] * self._formatting['display_factor']) * (self.max_ordinal-self.min_ordinal)

    def _inverse_y_position(self, pos_y):
        """
        map back a display position to an ordinal value

        Args:
            pos_y (float): display position

        Returns:
            float: ordinal value
        """
        return (
            pos_y
            + self._formatting['total_height'] *
            (self._formatting['display_factor']-1)/2
        ) / (self._formatting['total_height'] * self._formatting['display_factor']) * (self.chart_max_ordinal-self.chart_min_ordinal) + self.chart_min_ordinal

    def _inverse_x_position(self, pos_x):
        return int(round((pos_x - self._formatting['margin_left'])/self._formatting['vertical_step_size']))

    def get_full_width(self):
        """
        get the full width of the chart including margins

        Returns:
            float: chart width
        """
        return (self._map_x_position(self.max_x_index) + self._formatting['margin_right'])

    def get_full_height(self):
        """
        get the full height of the chart including margins

        Returns:
            float: chart height
        """
        return abs(self._map_y_position(self.chart_min_ordinal) - self._map_y_position(self.chart_max_ordinal))

    def get_individual_from_position(self, pos_x, pos_y):
        """
        inverse mapping from chart position to individual instance

        Args:
            pos_x (float or int): x position
            pos_y (float or int): y position

        Returns:
            BaseIndividual: individual instance
        """
        x_index = self._inverse_x_position(pos_x)
        ordinal_value = int(self._inverse_y_position(pos_y))
        possible_matches = self.position_to_person_map.get(x_index)
        if possible_matches is not None:
            for possible_match in possible_matches:
                if possible_match['start'] < ordinal_value and possible_match['end'] > ordinal_value:
                    return possible_match['individual']
        return None

    def clear_svg_items(self):
        """
        clear all graphical items to render the chart with different settings
        """
        self.additional_graphical_items.clear()
        for gr_individual in self.gr_individuals:
            gr_individual.items.clear()

    def clear_graphical_representations(self):
        """
        clear all graphical representations to rebuild the chart
        """
        self.max_ordinal = None
        self.min_ordinal = None
        self.additional_graphical_items.clear()
        self.gr_individuals.clear()
        self.gr_families.clear()
        self._instances.clear_connections()
        self.position_to_person_map = {}
        for _, instance in self._instances.items():
            if instance is not None:
                instance.graphical_representations.clear()
