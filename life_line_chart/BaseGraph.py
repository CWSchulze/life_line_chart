from .InstanceContainer import get_gedcom_instance_container
from .AncestorGraphFamily import ancestor_graph_family
from .AncestorGraphIndividual import ancestor_graph_individual
from .Exceptions import LifeLineChartCollisionDetected, LifeLineChartCannotMoveIndividual

import os
from copy import deepcopy
import logging

logger = logging.getLogger("life_line_chart")


class BaseGraph():
    """
    Base class for life line charts.
    """
    _default_formatting = {
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
        'individual_photo_relative_size': 2.5
    }
    _default_positioning = {
        'compression_steps': -1,  # debugging option
        'compress': False,
        'flip_to_optimize': False,
        'fathers_have_the_same_color': False,
    }
    _formatting_description = {
        'warp_shape': {
            'short_description': 'Warp the chart shape',
            'long_description': 'The overall shape of the chart can be warped.',
            'choices': {
                'normal': 'Normal grid shape',
                'sine': 'Sine shape',
                'triangle': 'Triangular shape'
            }
        },
        'individual_photo_active': {
            'short_description': 'Show photos',
            'long_description': 'Photos of the individual are shown.'
        },
        'individual_photo_relative_size': {
            'short_description': 'Photo size',
            'long_description': 'Photos which are shown are fitted into a square of this extent. The size is given relative to the line thickness.'
        },
        'total_height': {
            'short_description': 'Total height',
            'long_description': 'Total height of the whole chart.'
        },
        'relative_line_thickness': {
            'short_description': 'Relative line thickness',
            'long_description': 'The line thickness of an individual is given relatively to the vertical step size.'
        },
        'vertical_step_size': {
            'short_description': 'Vertical step size',
            'long_description': 'This is the distance from one line to another. This value is also used for scaling of other items.'
        },
        'birth_label_active': {
            'short_description': 'Show birth label',
            'long_description': 'Activate the birth label.'
        },
        'birth_label_along_path': {
            'short_description': 'Birth label along path',
            'long_description': 'The birth label is aligned to the individual line.',
            'tab': 'Label Configuration'
        },
        'birth_label_rotation': {
            'short_description': 'Birth label rotation',
            'long_description': 'The birth label is written in a text frame rotated by this value.',
            'tab': 'Label Configuration'
        },
        'birth_label_letter_x_offset': {
            'short_description': 'Birth label x offset',
            'long_description': 'The birth label is moved in x direction by this value, which is given relatively to the font size.',
            'tab': 'Label Configuration'
        },
        'birth_label_letter_y_offset': {
            'short_description': 'Birth label y offset',
            'long_description': 'The birth label is moved in y direction by this value, which is given relatively to the font size.',
            'tab': 'Label Configuration'
        },
        'birth_label_wrapping_active': {
            'short_description': 'Wrap words in birth label',
            'long_description': 'The birth label content is wrapped where possible.',
            'tab': 'Label Configuration'
        },
        'birth_label_anchor': {
            'short_description': 'Birth label anchor',
            'long_description': 'Text alignment of the birth label.',
            'choices': {
                'start' : 'Left',
                'middle' : 'Center',
                'end' : 'Right'
            },
            'tab': 'Label Configuration'
        },
        'death_label_active': {
            'short_description': 'Show death label',
            'long_description': 'Activate the death label.'
        },
        'death_label_rotation': {
            'short_description': 'Death label rotation',
            'long_description': 'The death label is written in a text frame rotated by this value.',
            'tab': 'Label Configuration'
        },
        'death_label_letter_x_offset': {
            'short_description': 'Death label x offset',
            'long_description': 'The death label is moved in x direction by this value, which is given relatively to the font size.',
            'tab': 'Label Configuration'
        },
        'death_label_letter_y_offset': {
            'short_description': 'Death label y offset',
            'long_description': 'The death label is moved in y direction by this value, which is given relatively to the font size.',
            'tab': 'Label Configuration'
        },
        'death_label_wrapping_active': {
            'short_description': 'Wrap words in death label',
            'long_description': 'The death label content is wrapped where possible.',
            'tab': 'Label Configuration'
        },
        'death_label_anchor': {
            'short_description': 'Death label anchor',
            'long_description': 'Text alignment of the death label.',
            'choices': {
                'start' : 'Left',
                'middle' : 'Center',
                'end' : 'Right'
            },
            'tab': 'Label Configuration'
        },
        'marriage_label_active': {
            'short_description': 'Show marriage label',
            'long_description': 'Activate the marriage label.'
        },
        'fade_individual_color': {
            'short_description': 'Fade individual color',
            'long_description': 'The color of the individuals is faded to black with increasing age.'
        },
        'font_name': {
            'short_description': 'Font name',
            'long_description': 'Name of the font family used for labels.',
            'tab': 'Label Configuration'
        },
        'font_size_description': {
            'short_description': 'Relative font size',
            'long_description': 'The font size is given relatively to the line thickness.',
            'tab': 'Label Configuration'
        },
        'family_shape': {
            'short_description': 'Family shape',
            'long_description': 'The shape of the families can be varied.',
            'choices': {
                0 : 'Rectangular',
                1 : 'Softer'
            }
        },
        'margin_year_max': {
            'short_description': 'Upper year minimum margin',
            'long_description': 'The upper bound of the chart is extended by at least this number of years.'
        },
        'margin_year_min': {
            'short_description': 'Lower year minimum margin',
            'long_description': 'The lower bound of the chart is extended by at least this number of years.'
        }
    }
    _positioning_description = {
        'compress': {
            'short_description': 'Compress the graph vertically',
            'long_description': 'By default every individual has a unique vertical slot. This can be inefficient with many generations. This algorithm lets several people share a vertical slot, if they do not overlap.'
        },
        'flip_to_optimize': {
            'short_description': 'Flip families to reduce vertical connections',
            'long_description': 'Switch the position of mother and father in a family, to reduce the overall vertical cross connections in larger graphs (pedigree collapse).'
        },
        'fathers_have_the_same_color': {
            'short_description': 'Fathers have the same color',
            'long_description': 'Starting from the root person, each father of an added individual has the same color as that individual.'
        },

    }
    _chart_configuration_root_individual_description = {
        'generations': {
            'short_description': 'Maximum number of generations',
            'long_description': 'When this number of generations has been reached, the algorithm doesn´\'t go any deeper'
        },
    }
    _available_warp_shapes = list(_formatting_description['warp_shape']['choices'].keys())
    # TODO: extract base class for other graph types
    _graphical_family_class = ancestor_graph_family
    # TODO: extract base class for other graph types
    _graphical_individual_class = ancestor_graph_individual

    def __init__(self, positioning=None, formatting=None, instance_container=get_gedcom_instance_container):
        self.position_to_person_map = {}
        self._positioning = BaseGraph.get_default_positioning()
        if positioning:
            self._positioning.update(positioning)
        self._formatting = BaseGraph.get_default_formatting()
        if formatting:
            self._formatting.update(formatting)
        self._instances = instance_container()
        self._instances[('i', None)] = None
        self.graphical_individual_representations = []
        self.graphical_family_representations = []
        self.additional_graphical_items = {}
        logger.debug('finished creating instances')

        self.min_x_index = 10000000
        self.max_x_index = -10000000
        self.min_ordinal = None
        self.max_ordinal = None
        self.chart_min_ordinal = None
        self.chart_max_ordinal = None

        # configuration of this graph
        self._chart_configuration = {}
        self._default_chart_configuration = {}

        self._backup_positioning = None
        self._backup_formatting = None
        self._backup_chart_configuration = None

    @staticmethod
    def get_default_formatting():
        """
        get the default formatting

        Returns:
            dict: formatting dict
        """
        return deepcopy(BaseGraph._default_formatting)

    @staticmethod
    def get_formatting_description():
        """
        get the formatting description to build UI

        Returns:
            dict: description of the formatting
        """
        return deepcopy(BaseGraph._formatting_description)

    @staticmethod
    def get_default_positioning():
        """
        get the deafult positioning

        Returns:
            dict: positioning dict
        """
        return deepcopy(BaseGraph._default_positioning)

    @staticmethod
    def get_positioning_description():
        """
        get the positioning description to build UI

        Returns:
            dict: description of the positioning
        """
        return deepcopy(BaseGraph._positioning_description)

    @staticmethod
    def get_chart_configuration_root_individual_description():
        """
        get the chart configuration root individual description to build UI

        Returns:
            dict: description of chart configuration root individual
        """
        return deepcopy(BaseGraph._chart_configuration_root_individual_description)

    def instantiate_all(self):
        """
        instantiate all families and individuals
        """
        self._instances.instantiate_all(self=self._instances)

    def set_formatting(self, formatting):
        """
        set the formatting configuration of the graph

        Args:
            formatting (dict): formatting dict
        """
        self._formatting.update(formatting)

    def set_positioning(self, positioning):
        """
        set the positioning configuration of the graph

        Args:
            positioning (dict): positioning dict
        """
        self._positioning.update(positioning)

    def set_chart_configuration(self, chart_configuration):
        """
        set the chart configuration of the graph

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
            ancestor_graph_inidividual: created instance
        """
        new_instance = self._graphical_individual_class(
            self._instances, individual.individual_id)
        if new_instance.birth_date is None or new_instance.death_date is None:
            del new_instance
            return None
        self.graphical_individual_representations.append(new_instance)
        return new_instance

    def _create_family_graphical_representation(self, family):
        """
        create a graphical representation for a family

        Args:
            family (BaseFamily): family

        Returns:
            ancestor_graph_family: created instance
        """
        if not family.graphical_representations:
            new_instance = self._graphical_family_class(
                self._instances, family.family_id)
            self.graphical_family_representations.append(new_instance)
        else:
            new_instance = family.graphical_representations[0]
            # print('the family was added twice:'+family.family_id)
        return new_instance

    def _calculate_sum_of_distances(self):
        """
        sum of distances between different families of one individual

        Returns:
            tuple: (total_distance, list_of_linked_individuals)
        """
        total_distance = 0
        list_of_linked_individuals = {}
        for index, graphical_individual_representation in enumerate(self.graphical_individual_representations):
            x_positions = graphical_individual_representation.get_x_position()
            distance_of_this_individual = 0
            if x_positions:
                vector = [p[1] for k, p in x_positions.items()]
                distance_of_this_individual += max(vector) - min(vector)
            total_distance += distance_of_this_individual
            if distance_of_this_individual > 0:
                list_of_linked_individuals[(
                    distance_of_this_individual, index)] = graphical_individual_representation
        return total_distance, list_of_linked_individuals

    def _move_single_individual(self, individual, family, x_index_offset):
        """
        move a single individual vertically

        Args:
            individual (BaseIndividual): individual instance
            family (BaseFamily): family instance
            x_index_offset (int): vertical offset

        Returns:
            dict: position dict of the graphical individual representation
        """
        x_pos = individual.graphical_representations[0].get_x_position()
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

    def _move_individual_and_ancestors(self, individual, family, x_index_offset):
        """
        move an individual and its ancestors vertically. Only ancestors are moved, which are strongly coupled with the individual.

        Args:
            individual (BaseIndividual): individual instance
            family (BaseFamily): family instance
            x_index_offset (int): vertical offset
        """
        if family is None:
            family_id = family
            # return
        else:
            family_id = family.family_id
        if len(individual.graphical_representations) > 0:
            x_pos = self._move_single_individual(
                individual, family, x_index_offset)
            if None in x_pos or True:
                # only move ancestors if they exist
                # len(x_pos) <= 1 or
                if list(sorted(x_pos.values()))[0][1] != x_pos[family_id][1]:
                    return
                # for cof in individual.get_child_of_family():
                cof = individual.graphical_representations[0].visible_parent_family
                if cof and cof.visual_placement_child and cof.visual_placement_child.individual_id == individual.individual_id:
                    if cof.husb:
                        # if cof.husb.graphical_representations[0].get_x_position() and len(cof.husb.graphical_representations[0].get_x_position()) == 1:
                            self._move_individual_and_ancestors(
                                cof.husb, cof, x_index_offset)
                    if cof.wife:
                        # if cof.wife.graphical_representations[0].get_x_position() and len(cof.wife.graphical_representations[0].get_x_position()) == 1:
                            self._move_individual_and_ancestors(
                                cof.wife, cof, x_index_offset)
                    # print (individual.get)
                if cof and len(cof.visible_children) > 1:
                    for child_individual_id, (_, _, child_individual) in cof.visible_children.items():
                        if child_individual_id == individual.individual_id:
                            continue
                        pos = sorted(
                            list(child_individual.graphical_representations[0].get_x_position().values()))[0]
                        if pos[2]:
                            x_pos = self._move_single_individual(
                                child_individual, pos[2], x_index_offset)

    def _flip_family(self, family):
        """
        Flip family. The three sections change order
        - father and ancestors
        - individual + siblings
        - mother and ancestors

        Args:
            family (BaseFamily): family instance
        """
        if family.husb is None or family.wife is None or not family.husb.has_graphical_representation() or not family.wife.has_graphical_representation():
            return
        husb_x_pos = family.husb.graphical_representations[0].get_x_position()[
            family.family_id][1]
        husb_width = family.graphical_representations[0].husb_width()
        wife_x_pos = family.wife.graphical_representations[0].get_x_position()[
            family.family_id][1]
        wife_width = family.graphical_representations[0].wife_width()
        children_width = family.graphical_representations[0].children_width
        if not children_width:
            children_width = self._formatting['vertical_step_size']
        if children_width != len(family.graphical_representations[0].visible_children):
            print("G")

        if husb_x_pos < wife_x_pos:
            husb_x_delta = wife_width + children_width
            wife_x_delta = -husb_width - children_width
            child_x_delta = wife_width - husb_width
        else:
            husb_x_delta = -wife_width - children_width
            wife_x_delta = husb_width + children_width
            child_x_delta = husb_width - wife_width

        for _, (_, _, child_individual) in family.graphical_representations[0].visible_children.items():
            pos = sorted(
                list(child_individual.graphical_representations[0].get_x_position().values()))
            self._move_single_individual(
                child_individual, pos[0][2], child_x_delta)

        self._move_individual_and_ancestors(
            family.husb, family, husb_x_delta+1000000)
        self._move_individual_and_ancestors(family.wife, family, wife_x_delta)
        self._move_individual_and_ancestors(family.husb, family, -1000000)
        self._instances.ancestor_width_cache.clear()
        pass

    def _check_compressed_x_position(self, early_raise):
        """
        check the compressed graph for overlapping individuals

        Args:
            early_raise (bool): raise an exception if the first individual overlap was found

        Raises:
            LifeLineChartCollisionDetected: overlapping found

        Returns:
            [type]: [description]
        """
        position_to_person_map = {}
        v = {}
        collisions = []
        min_x = 999999
        max_x = 0
        # assign the individuals to all x_indices in which they appear
        for graphical_individual_representation in self.graphical_individual_representations:
            x_pos = graphical_individual_representation.get_x_position()
            for i, value in enumerate(x_pos.values()):
                x_index = value[1]
                # if value[3]:
                #     continue
                # if x_index < 0:
                #     if early_raise:
                #         raise LifeLineChartCollisionDetected(graphical_individual_representation)
                #     collisions.append((graphical_individual_representation, None))
                if x_index not in v:
                    v[x_index] = []
                    position_to_person_map[x_index] = []
                if i == 0:
                    start_y = graphical_individual_representation.get_birth_date_ov()
                else:
                    start_y = list(x_pos.values())[i][0]
                if i < len(x_pos) - 1:
                    end_y = list(x_pos.values())[i+1][0]
                else:
                    end_y = graphical_individual_representation.get_death_date_ov()
                position_to_person_map[x_index].append({
                    'start': start_y,
                    'end': end_y,
                    'individual': graphical_individual_representation
                })

                v[x_index].append(graphical_individual_representation)
                max_x = max(max_x, x_index)
                min_x = min(min_x, x_index)
        if len(collisions) > 0:
            raise LifeLineChartCollisionDetected()

        # block every x_index from birth to death in which an individual appears
        for x_index, graphical_individual_representation_list in v.items():
            for index, graphical_individual_representation_a in enumerate(graphical_individual_representation_list):
                for graphical_individual_representation_b in graphical_individual_representation_list[index+1:]:
                    birth_position_a = graphical_individual_representation_a.get_birth_date_ov() - 365*15
                    birth_position_b = graphical_individual_representation_b.get_birth_date_ov() - 365*15
                    death_position_a = graphical_individual_representation_a.get_death_date_ov() + 365*15
                    death_position_b = graphical_individual_representation_b.get_death_date_ov() + 365*15
                    if ((birth_position_a - birth_position_b)
                                * (birth_position_a - death_position_b) < 0 or
                                (death_position_a - birth_position_b)
                                * (death_position_a - death_position_b) < 0 or
                                (birth_position_b - birth_position_a)
                                * (birth_position_b - death_position_a) < 0 or
                                (death_position_b - birth_position_a)
                                * (death_position_b - death_position_a) < 0):
                        if early_raise:
                            raise LifeLineChartCollisionDetected(
                                graphical_individual_representation_a, graphical_individual_representation_b)
                        collisions.append(
                            (graphical_individual_representation_a, graphical_individual_representation_b))
        # if len(collisions) > 0:
        #     raise RuntimeError()
        return collisions, min_x, max_x, position_to_person_map

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
        for graphical_individual_representation in self.graphical_individual_representations:
            x_pos = graphical_individual_representation.get_x_position()
            for value in x_pos.values():
                x_index = value[1]
                if value[3]:
                    continue
                # if not value[2] is None and graphical_individual_representation.individual_id not in value[2].children_individual_ids:
                #     continue
            #     x_indices.add(x_index)
            #     index_map[x_index] = value[2]
            # for x_index in x_indices:
                if x_index not in v:
                    v[x_index] = graphical_individual_representation.individual_id
                else:
                    failed.append(x_index)
                    # value = index_map[x_index]
                    logger.error(
                        "failed: " + str((x_index, value[2].family_id, graphical_individual_representation.name, v[x_index])))
                    # raise RuntimeError((x_index, key, graphical_individual_representation.name))
        full_index_list = list(sorted(v.keys()))
        for i in range(max(full_index_list)):
            if i not in full_index_list:
                graphical_individual_representation.items.append({
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
        map date information and vertical index to x and y axis. This function also supports warping of the whole graph.

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
        get the rotation of the lines which is caused by the warping of the whole graph

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
        get the full width of the graph including margins

        Returns:
            float: graph width
        """
        return (self._map_x_position(self.max_x_index) + self._formatting['margin_right'])

    def get_full_height(self):
        """
        get the full height of the graph including margins

        Returns:
            float: graph height
        """
        return abs(self._map_y_position(self.chart_min_ordinal) - self._map_y_position(self.chart_max_ordinal))

    def get_individual_from_position(self, pos_x, pos_y):
        """
        inverse mapping from graph position to individual instance

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
        clear all graphical items to render the graph with different settings
        """
        self.additional_graphical_items.clear()
        for graphical_individual_representation in self.graphical_individual_representations:
            graphical_individual_representation.items.clear()

    def clear_graphical_representations(self):
        """
        clear all graphical representations to rebuild the chart
        """
        self.max_ordinal = None
        self.min_ordinal = None
        self.additional_graphical_items.clear()
        self.graphical_individual_representations.clear()
        self.graphical_family_representations.clear()
        self.position_to_person_map = {}
        for key, instance in self._instances.items():
            instance.graphical_representations.clear()
