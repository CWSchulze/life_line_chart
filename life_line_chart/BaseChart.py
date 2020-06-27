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
        'horizontal_step_size': 40,
        'relative_line_thickness': 0.4,
        'total_height': 1500,
        'flip_vertically': False,
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
        'individual_photo_relative_distance': 1.1,
        'debug_visualize_connections': False,
        'debug_visualize_ambiguous_placement': False,
        'coloring_of_individuals': 'unique',
        'line_weighting': 'none'
    }
    DEFAULT_POSITIONING = {
        'unique_graphical_representation': True
    }
    DEFAULT_CHART_CONFIGURATION = {
    }
    SETTINGS_DESCRIPTION = _strings

    COLOR_CONFIGURATIONS = {
        'light': {
            'descendant_chart_marriage_lines': (0, 0, 0),
            'fade_to_death': (0, 0, 0),
            'grid_line': (210, 210, 210),
            'text_label': (0, 0, 0)
        },
        'dark': {
            'descendant_chart_marriage_lines': (200, 200, 200),
            'fade_to_death': (255, 255, 255),
            'grid_line': (20, 20, 20),
            'text_label': (200, 200, 200)
        }
    }
    _colors = COLOR_CONFIGURATIONS['light']

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
        self._debug_check_collision_counter = 0

    def instantiate_all(self):
        """
        Instantiate all families and individuals
        """
        self._instances.instantiate_all(self=self._instances)

    def set_formatting(self, formatting):
        """
        Set the formatting configuration of the chart

        Args:
            formatting (dict): formatting dict
        """
        self._formatting.update(formatting)

    def set_positioning(self, positioning):
        """
        Set the positioning configuration of the chart

        Args:
            positioning (dict): positioning dict
        """
        self._positioning.update(positioning)

    def set_chart_configuration(self, chart_configuration):
        """
        Set the chart configuration of the chart

        Args:
            chart_configuration (dict): chart configuration dict
        """
        self._chart_configuration.update(chart_configuration)

    def get_chart_configuration(self):
        """
        Get the chart configuration

        Returns:
            dict: chart configuration dict
        """
        return deepcopy(self._chart_configuration)

    def _create_individual_graphical_representation(self, individual, always_instantiate_new = False):
        """
        Create a graphical representation for an individual

        Args:
            individual (BaseIndividual): individual
            always_instantiate_new (bool): create separate representations for each appearance

        Returns:
            ancestor_chart_inidividual: created or reused instance
        """
        if not individual.graphical_representations or always_instantiate_new:
            # create new instance
            new_instance = self._graphical_individual_class(
                self._instances, individual.individual_id)
            if new_instance.birth_date is None or new_instance.death_date is None:
                del new_instance
                return None
            new_instance.g_id = (len(individual.graphical_representations) - 1, individual.individual_id)
            new_instance.color = (0,0,0)
            self.gr_individuals.append(new_instance)
        else:
            # reuse instance
            new_instance = individual.graphical_representations[-1]

        return new_instance

    def _create_family_graphical_representation(self, family, always_instantiate_new = False):
        """
        Create a graphical representation for a family

        Args:
            family (BaseFamily): family
            always_instantiate_new (bool): create separate representations for each appearance

        Returns:
            GraphicalFamily: created or reused instance
        """
        if not family.graphical_representations or always_instantiate_new:
            # create new instance
            new_instance = self._graphical_family_class(
                self._instances, family.family_id)
            new_instance.g_id = (len(family.graphical_representations) - 1, family.family_id)
            self.gr_families.append(new_instance)
        else:
            # reuse instance
            new_instance = family.graphical_representations[-1]
            # logger.debug('the family was added twice:'+family.family_id)
        return new_instance

    def _calculate_sum_of_distances(self):
        """
        Sum of distances between different families of one individual. This refers
        to connections across the chart due to pedigree collapse.

        Returns:
            tuple: (total_distance, list_of_linked_individuals)
        """
        total_distance = 0
        list_of_linked_individuals = {}
        for index, gr_individual in enumerate(self.gr_individuals):
            position_dict = gr_individual.get_position_dict()
            distance_of_this_individual = 0
            if position_dict:
                all_x_indices = [p[1] for k, p in position_dict.items()]
                distance_of_this_individual += sum([abs(a-b) for a, b in zip(all_x_indices[:-1],all_x_indices[1:])])
            total_distance += distance_of_this_individual
            if distance_of_this_individual > 0:
                list_of_linked_individuals[(
                    distance_of_this_individual, index)] = gr_individual
        return total_distance, list_of_linked_individuals

    def _move_single_individual(self, gr_individual, gr_family, x_index_offset):
        """
        Move an x-position of an individual in a family.
        The parent family in an ancestor chart can be placed (and strongly connected)
        to one marriage. If the gr_family is one of the connected pair, then both
        are moved.

        Args:
            gr_individual (GraphicalIndividual): individual instance
            gr_family (GraphicalFamily): family instance
            x_index_offset (int): horizontal offset

        Returns:
            dict: position dict of the graphical individual representation
        """

        position_dict = gr_individual.get_position_dict()
        other_g_id = gr_individual.get_other_family_connected_to_birth_position(gr_family)

        if gr_family is not None:
            g_id = gr_family.g_id
        else:
            g_id = None

        if other_g_id != "there is no connected family":
            if g_id in position_dict and other_g_id in position_dict:
                position_dict[other_g_id] = (
                    position_dict[other_g_id][0],
                    position_dict[other_g_id][1]+x_index_offset,
                    position_dict[other_g_id][2],
                    position_dict[other_g_id][3],
                )

        if g_id in position_dict:
            position_dict[g_id] = (
                position_dict[g_id][0],
                position_dict[g_id][1]+x_index_offset,
                position_dict[g_id][2],
                position_dict[g_id][3],
            )
        else:
            raise LifeLineChartCannotMoveIndividual(
                'This family does not exist')
        return position_dict

    def _move_individual_and_ancestors(self, gr_individual, gr_family, x_index_offset, discovery_cache = None):
        """
        Move an individual and its ancestors horizontally. Only ancestors are moved,
        which are strongly coupled with the individual.

        Args:
            gr_individual (GraphicalIndividual): gr_individual instance
            gr_family (GraphicalFamily): family instance
            x_index_offset (int): horizontal offset
        """
        if discovery_cache is None:
            discovery_cache = []
        discovery_cache.append(gr_individual)

        # move this individual
        self._move_single_individual(
            gr_individual, gr_family, x_index_offset)

        gr_cofs = gr_individual.connected_parent_families
        if len(gr_cofs) == 0:
            discovery_cache.pop()
            return
        gr_cof = gr_cofs[0]

        #for strongly_connected_parent_family in gr_individual.connected_parent_families:
        strongly_connected_parent_family, strongly_connected_spouse_family = gr_individual.ancestor_chart_parent_family_placement
        if strongly_connected_parent_family and (strongly_connected_spouse_family == strongly_connected_parent_family or gr_family == strongly_connected_spouse_family or strongly_connected_spouse_family == None):
            if strongly_connected_parent_family.gr_husb:
                # if cof.gr_husb.get_position_dict() and len(cof.gr_husb.get_position_dict()) == 1:
                    self._move_individual_and_ancestors(
                        strongly_connected_parent_family.gr_husb, strongly_connected_parent_family, x_index_offset, discovery_cache)
            if strongly_connected_parent_family.gr_wife:
                # if cof.gr_wife.get_position_dict() and len(cof.gr_wife.get_position_dict()) == 1:
                    self._move_individual_and_ancestors(
                        strongly_connected_parent_family.gr_wife, strongly_connected_parent_family, x_index_offset, discovery_cache)
            # print (gr_individual.get)
            if True or gr_cof and gr_cof.gr_husb is None and gr_cof.gr_wife is None:
                for gr_child_individual in gr_cof.visible_children:
                    if gr_child_individual == gr_individual:
                        continue
                    self._move_single_individual(
                        gr_child_individual, gr_cof, x_index_offset)
        discovery_cache.pop()

    def _check_compressed_x_position(self, early_raise, position_to_person_map=None, min_distance=15):
        """
        Check the compressed chart for overlapping individuals. Overlapping is allowed if the minimum
        distance between the individual family sections is greater than min_distance years.

        Args:
            early_raise (bool): raise an exception if the first individual overlap was found
            position_to_person_map (dict): if required, they position map can be obtained. Defaults to None.
            min_distance (float): if the distance falls below this value, the exception is thrown.

        Raises:
            LifeLineChartCollisionDetected: overlapping found
        """
        self._debug_check_collision_counter += 1
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

        line_bend_orientation = 0 if (str(type(self)) == "<class 'life_line_chart.DescendantChart.DescendantChart'>" and self._positioning['chart_layout'] == 'cactus') else 1
        # assign the individuals to all x_indices in which they appear
        for gr_individual in self.gr_individuals:
            position_vector = list(gr_individual.get_position_dict().values())
            spouse_families = list(gr_individual.get_spouse_positions().values())
            missing_families = len(position_vector)-len(spouse_families)
            if missing_families:
                if spouse_families:
                    spouse_families = [spouse_families[0]] * missing_families + spouse_families
                else:
                    spouse_families = [(None, None, None, None)] * missing_families

            for i, value in enumerate(position_vector):
                if line_bend_orientation == 1:
                    x_index = value[1]
                else:
                    x_index = position_vector[1][1]
                marriage = spouse_families[i][2]
                if x_index not in v:
                    v[x_index] = []

                    if position_to_person_map is not None:
                        position_to_person_map[x_index] = []
                if i == 0:
                    start_y = gr_individual.birth_date_ov
                else:
                    start_y = position_vector[i][0]
                if i < len(position_vector) - 1:
                    end_y = position_vector[i+1][0]
                else:
                    end_y = gr_individual.death_date_ov

                if start_y == end_y:
                    # happens in ancestor charts if spouse family is None (i.e. the root individual)
                    continue

                if position_to_person_map is not None:
                    position_to_person_map[x_index].append({
                        'start': start_y,
                        'end': end_y,
                        'individual': gr_individual,
                        'family': marriage
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
        return collisions, min_x, max_x

    def _map_y_position(self, ordinal_value):
        """
        Map date information to y axis.

        Args:
            ordinal_value (float or int): ordinal value of the datetime

        Returns:
            float: y position
        """
        display_factor = 1 if self._formatting['flip_vertically'] else -1
        return (
            + (ordinal_value - self.chart_min_ordinal)/(self.chart_max_ordinal-self.chart_min_ordinal) *
            self._formatting['total_height'] * display_factor
            - self._formatting['total_height'] * (display_factor-1)/2
        )

    def _map_x_position(self, x_index):
        """
        Map vertical index to x axis.

        Args:
            x_index (float or int): horizontal index

        Returns:
            float: x position
        """
        return self._formatting['margin_left'] + x_index*self._formatting['horizontal_step_size']

    def _map_position(self, x_index, ov):
        """
        Map date information and horizontal index to x and y axis. This function also supports
        warping of the whole chart.

        Args:
            x_index (float or int): horizontal index
            ov (float or int): ordinal value of the datetime

        Returns:
            tuple: (x position, y position)
        """
        from math import pi, sin
        if self._formatting['warp_shape'] == 'sine':
            y_rel = (1-sin((1-(ov - self.min_ordinal) /
                            (self.max_ordinal - self.min_ordinal))*pi/2))*0.5
            x_av = (self.max_x_index + self.min_x_index)/2
            warped_x_index = x_index*(1-y_rel) + y_rel*x_av
            return self._map_x_position(warped_x_index), self._map_y_position(ov)
        elif self._formatting['warp_shape'] == 'triangle':
            y_rel = (ov - self.min_ordinal) / \
                (self.max_ordinal - self.min_ordinal)*0.8
            x_av = (self.max_x_index + self.min_x_index)/2
            warped_x_index = x_index*(1-y_rel) + y_rel*x_av
            return self._map_x_position(warped_x_index), self._map_y_position(ov)
        else:
            return int(round(self._map_x_position(x_index))), self._map_y_position(ov)

    def _inverse_map_position(self, pos_x, pos_y):
        """
        Map x and y axis to date information and horizontal index. This function also supports warping of the whole chart.

        Args:
            pos_x (float or int): horizontal index
            pos_y (float or int): ordinal value of the datetime

        Returns:
            tuple: (x position, y position)
        """
        from math import pi, sin
        if self._formatting['warp_shape'] == 'sine':
            warped_x_index, ov = self._inverse_x_position_float(pos_x), self._inverse_y_position(pos_y)
            y_rel = (1-sin((1-(ov - self.min_ordinal) /
                            (self.max_ordinal - self.min_ordinal))*pi/2))*0.5
            x_av = (self.max_x_index + self.min_x_index)/2
            x_index = (warped_x_index - y_rel*x_av)/(1-y_rel)
            return int(round(x_index)), ov
        elif self._formatting['warp_shape'] == 'triangle':
            warped_x_index, ov = self._inverse_x_position_float(pos_x), self._inverse_y_position(pos_y)
            y_rel = (ov - self.min_ordinal) / \
                (self.max_ordinal - self.min_ordinal)*0.8
            x_av = (self.max_x_index + self.min_x_index)/2
            x_index = (warped_x_index - y_rel*x_av)/(1-y_rel)
            return int(round(x_index)), ov
        else:
            return int(round(self._inverse_x_position_float(pos_x))), self._inverse_y_position(pos_y)

    def _orientation_angle(self, pos_x, pos_y):
        """
        Get the rotation of the lines which is caused by the warping of the whole chart. This
        is used for the rotation of text.

        Args:
            pos_x (float or int): horizontal index
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
        Map back a delta display size to the delta ordinal value

        Args:
            delta_y (float): difference of display size

        Returns:
            float: difference of ordinal value
        """
        display_factor = 1 if self._formatting['flip_vertically'] else -1
        return delta_y / (self._formatting['total_height'] * display_factor) * (self.chart_max_ordinal-self.chart_min_ordinal)

    def _inverse_y_position(self, pos_y):
        """
        Map back a display position to an ordinal value

        Args:
            pos_y (float): display position

        Returns:
            float: ordinal value
        """
        display_factor = 1 if self._formatting['flip_vertically'] else -1
        return (
            pos_y
            + self._formatting['total_height'] *
            (display_factor-1)/2
        ) / (self._formatting['total_height'] * display_factor) * (self.chart_max_ordinal-self.chart_min_ordinal) + self.chart_min_ordinal

    def _inverse_x_position_float(self, pos_x):
        return (pos_x - self._formatting['margin_left'])/self._formatting['horizontal_step_size']

    def get_full_width(self):
        """
        Get the full width of the chart including margins

        Returns:
            float: chart width
        """
        return (self._map_x_position(self.max_x_index) + self._formatting['margin_right'])

    def get_full_height(self):
        """
        Get the full height of the chart including margins

        Returns:
            float: chart height
        """
        return abs(self._map_y_position(self.chart_min_ordinal) - self._map_y_position(self.chart_max_ordinal))

    def get_individual_from_position(self, pos_x, pos_y):
        """
        Inverse mapping from chart position to individual instance

        Args:
            pos_x (float or int): x position
            pos_y (float or int): y position

        Returns:
            tuple: graphical individual instance, and graphical family instance
        """
        # x_index = self._inverse_x_position(pos_x)
        # ordinal_value = int(self._inverse_y_position(pos_y))
        x_index, ordinal_value = self._inverse_map_position(pos_x, pos_y)
        possible_matches = self.position_to_person_map.get(x_index)
        if possible_matches is not None:
            for possible_match in possible_matches:
                if possible_match['start'] < ordinal_value and possible_match['end'] > ordinal_value:
                    return possible_match['individual'], possible_match['family']
        return None, None

    def clear_svg_items(self):
        """
        Clear all graphical items to render the chart with different settings
        """
        self.additional_graphical_items.clear()
        for gr_individual in self.gr_individuals:
            gr_individual.items.clear()

    def clear_graphical_representations(self):
        """
        Clear all graphical representations to rebuild the chart
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

    def get_filtered_photos(self, birth_ordinal_value, original_images):
        images = {}
        photo_width = self._formatting['relative_line_thickness'] * self._formatting['individual_photo_relative_size'] * self._formatting['horizontal_step_size'] # * (1 + self.max_x_index - self.min_x_index)
        photo_height = photo_width * self._formatting['individual_photo_relative_distance']
        photo_ov_height = abs(self._inverse_y_delta(photo_height))
        ov_list = list(original_images.keys())
        settings_list = list(original_images.values())
        if len(original_images) > 0:
            max_ordinal = max(list(original_images.keys()))
        else:
            max_ordinal = -1
        latest_ordinal = birth_ordinal_value - photo_ov_height

        closest_index = -1
        used_indices_list = []
        while closest_index < len(ov_list) and latest_ordinal < max_ordinal:
            offset_ov_list = [(abs(v - latest_ordinal), i) for i, v in enumerate(ov_list) if i not in used_indices_list and v > latest_ordinal]
            if not offset_ov_list:
                break
            offset_ov_list.sort()
            closest_index = offset_ov_list[0][1]
            used_indices_list.append(closest_index)
            settings = settings_list[closest_index]
            exact_ordinal_value = ov_list[closest_index]
            relative_photo_height = min(1, settings['size'][1] / settings['size'][0])
            current_ordinal = max(latest_ordinal + 0.5*photo_ov_height*relative_photo_height, exact_ordinal_value)
            images[current_ordinal] = settings
            latest_ordinal = current_ordinal + 0.5*photo_ov_height*relative_photo_height
        # for ordinal_value, settings in sorted(original_images.items()):
        #     # filename = settings['filename']
        #     if len(images) > 0:
        #         max_ordinal = max(list(images.keys()))
        #     else:
        #         max_ordinal = -1
        #     if round((ordinal_value-birth_ordinal_value)/image_step_size) > round((max_ordinal-birth_ordinal_value)/image_step_size):
        #         images[birth_ordinal_value + round((ordinal_value-birth_ordinal_value)/image_step_size)
        #                 * image_step_size] = settings
        return images

    def get_filtered_photos_raster(self, birth_ordinal_value, original_images):
        images = {}
        photo_width = self._formatting['relative_line_thickness'] * self._formatting['individual_photo_relative_size'] * self._formatting['horizontal_step_size'] # * (1 + self.max_x_index - self.min_x_index)
        photo_height = photo_width * self._formatting['individual_photo_relative_distance']
        photo_ov_height = abs(self._inverse_y_delta(photo_height))
        image_step_size = photo_ov_height
        for ordinal_value, settings in sorted(original_images.items()):
            # filename = settings['filename']
            if len(images) > 0:
                max_ordinal = max(list(images.keys()))
            else:
                max_ordinal = -1
            if round((ordinal_value-birth_ordinal_value)/image_step_size) > round((max_ordinal-birth_ordinal_value)/image_step_size):
                images[birth_ordinal_value + round((ordinal_value-birth_ordinal_value)/image_step_size)
                        * image_step_size] = settings
        return images
