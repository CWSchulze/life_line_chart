from .InstanceContainer import get_gedcom_instance_container
from .AncestorGraphFamily import ancestor_graph_family
from .AncestorGraphIndividual import ancestor_graph_individual
from .Exceptions import LifeLineChartCollisionDetected, LifeLineChartCannotMoveIndividual

import os
from copy import deepcopy
import logging
import json
import datetime


logging.basicConfig()#level=20)
logger = logging.getLogger("life_line_chart")
logger.setLevel(logging.INFO)

class BaseGraph():
    """
    Base class for life line charts.
    """    
    _default_formatting = {
        'margin_left' : 50,
        'margin_right' : 50,
        'margin_top' : 50,
        'margin_bottom' : 50,
        'vertical_step_size' : 20,
        'relative_line_thickness' : 0.5,
        'total_height' : 2000,
        'display_factor' : -1,
        'font_size_description': 0.7,
        'font_description_letter_offset' : [str(30 / 12.0)+''],
        'font_name' : 'Arial',
        'birth_label_active':True,
        'birth_label_along_path' : False,
        'birth_label_letter_x_offset': 0.8,
        'fade_individual_color' : True,
        'fade_individual_color_black_age' : 150,
        'marriage_label_active':True,
        'no_ring' : False,
        'death_label_active':True,
        'death_label_rotation':-90,
        'death_label_letter_x_offset': 0.8,
        'warp_shape': 'normal',
        'family_shape' : 0,
    }
    _default_positioning = {
        'generations':4,
        'compression_steps':-1, # debugging option
        'compress':True,
        'flip_to_optimize':True,
        'fathers_have_the_same_color': True,
    }
    _formatting_description = {
        'warp_shape' : {
            'short_description' : 'Warp the chart shape',
            'long_description' : 'The overall shape of the chart can be warped.'
        },
        'total_height' : {
            'short_description' : 'Total height',
            'long_description' : 'Total height of the whole chart.'
        },
        'relative_line_thickness' : {
            'short_description' : 'Relative line thickness',
            'long_description' : 'The line thickness of an individual is given relatively to the vertical step size.'
        },
        'vertical_step_size' : {
            'short_description' : 'Vertical step size',
            'long_description' : 'This is the distance from one line to another. This value is also used for scaling of other items.'
        },
        'birth_label_active' : {
            'short_description' : 'Show birth label',
            'long_description' : 'Activate the birth label.'
        },
        'birth_label_along_path' : {
            'short_description' : 'Birth label alogn path',
            'long_description' : 'The birth label is aligned to the individual line.'
        },
        'death_label_active' : {
            'short_description' : 'Show death label',
            'long_description' : 'Activate the death label.'
        },
        'marriage_label_active' : {
            'short_description' : 'Show marriage label',
            'long_description' : 'Activate the marriage label.'
        },
        'fade_individual_color' : {
            'short_description' : 'Fade individual color',
            'long_description' : 'The color of the individuals is faded to black with increasing age.'
        },
        'font_name' : {
            'short_description' : 'Font name',
            'long_description' : 'Name of the font family used for labels.'
        },
        'font_size_description' : {
            'short_description' : 'Relative font size',
            'long_description' : 'The font size is given relatively to the line thickness.'
        },
        'family_shape' : {
            'short_description' : 'Family shape',
            'long_description' : 'The shape of the families can be varied.'
        },
    }
    _positioning_description = {
        'generations' : {
            'short_description' : 'Maximum number of generations',
            'long_description' : 'When this number of generations has been reached, the algorithm doesn´\'t go any deeper'
        },
        'compress' : {
            'short_description' : 'Compress the graph vertically',
            'long_description' : 'By default every individual has a unique vertical slot. This can be inefficient with many generations. This algorithm lets several people share a vertical slot, if they do not overlap.'
        },
        'flip_to_optimize' : {
            'short_description' : 'Flip families to reduce vertical connections',
            'long_description' : 'Switch the position of mother and father in a family, to reduce the overall vertical cross connections in larger graphs (pedigree collapse).'
        },
        'fathers_have_the_same_color' : {
            'short_description' : 'Fathers have the same color',
            'long_description' : 'Starting from the root person, each father of an added individual has the same color as that individual.'
        },

    }
    _available_warp_shapes = ['normal', 'sine', 'triangle']
    _graphical_family_class = ancestor_graph_family # TODO: extract base class for other graph types
    _graphical_individual_class = ancestor_graph_individual # TODO: extract base class for other graph types
    def __init__(self, positioning = None, formatting = None, instance_container = get_gedcom_instance_container):
        # renderer = HighlightRenderer()
        # self._markdown_to_spans = mistune.Markdown(renderer=renderer)

        self.position_to_person_map = {}
        self._positioning = deepcopy(self._default_positioning)
        if positioning:
            self._positioning.update(positioning)
        self._formatting = deepcopy(self._default_formatting)
        if formatting:
            self._formatting.update(formatting)
        self._instances = instance_container()
        self._instances[('i',None)] = None
        self.graphical_individual_representations = []
        self.graphical_family_representations = []
        logger.debug('finished creating instances')
        
        self.min_x_index = 10000000
        self.max_x_index = -10000000
        self.min_ordinal = 10000000
        self.max_ordinal = -10000000

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

    def _create_individual_graphical_representation(self, individual):
        """
        create a graphical representation for an individual
        
        Args:
            individual (BaseIndividual): individual
        
        Returns:
            ancestor_graph_inidividual: created instance
        """        
        new_instance = self._graphical_individual_class(self._instances, individual.individual_id, self._formatting['vertical_step_size'])
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
            new_instance = self._graphical_family_class(self._instances, family.family_id)
            self.graphical_family_representations.append(new_instance)
        else:
            new_instance = family.graphical_representations[0]
            #print('the family was added twice:'+family.family_id)
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
                list_of_linked_individuals[(distance_of_this_individual, index)] = graphical_individual_representation
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
        if not family is None:
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
            raise LifeLineChartCannotMoveIndividual('This family does not exist')
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
            #return
        else:
            family_id = family.family_id
        if len(individual.graphical_representations) > 0:
            x_pos = self._move_single_individual(individual, family, x_index_offset)
            if None in x_pos or True:
                # only move ancestors if they exist
                if list(sorted(x_pos.values()))[0][1] != x_pos[family_id][1]:#len(x_pos) <= 1 or 
                    return
                #for cof in individual.get_child_of_family():
                cof = individual.graphical_representations[0].visible_parent_family
                if cof and cof.visual_placement_child and cof.visual_placement_child.individual_id == individual.individual_id:
                    if cof.husb:
                        #if cof.husb.graphical_representations[0].get_x_position() and len(cof.husb.graphical_representations[0].get_x_position()) == 1:
                            self._move_individual_and_ancestors(cof.husb, cof, x_index_offset)
                    if cof.wife:
                        #if cof.wife.graphical_representations[0].get_x_position() and len(cof.wife.graphical_representations[0].get_x_position()) == 1:
                            self._move_individual_and_ancestors(cof.wife, cof, x_index_offset)
                    #print (individual.get)
                if cof and len(cof.visible_children) > 1:
                    for child_individual_id, (ov, i, child_individual) in cof.visible_children.items():
                        if child_individual_id == individual.individual_id:
                            continue
                        pos = sorted(list(child_individual.graphical_representations[0].get_x_position().values()))[0]
                        if pos[2]:
                            x_pos = self._move_single_individual(child_individual, pos[2], x_index_offset)

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
        husb_x_pos = family.husb.graphical_representations[0].get_x_position()[family.family_id][1]
        husb_width = family.graphical_representations[0].husb_width
        wife_x_pos = family.wife.graphical_representations[0].get_x_position()[family.family_id][1]
        wife_width = family.graphical_representations[0].wife_width
        children_width = family.graphical_representations[0].children_width
        if not children_width:
            children_width = self._formatting['vertical_step_size']
            
        if husb_x_pos < wife_x_pos:
            husb_x_delta = wife_width + children_width
            wife_x_delta = -husb_width - children_width
            child_x_delta = wife_width - husb_width
        else:
            husb_x_delta = -wife_width - children_width
            wife_x_delta = husb_width + children_width
            child_x_delta = husb_width - wife_width

        for child_individual_id, (ov, i, child_individual) in family.graphical_representations[0].visible_children.items():
            pos = sorted(list(child_individual.graphical_representations[0].get_x_position().values()))
            x_pos = self._move_single_individual(child_individual, pos[0][2], child_x_delta)
                
        self._move_individual_and_ancestors(family.husb, family, husb_x_delta+1000000)
        self._move_individual_and_ancestors(family.wife, family, wife_x_delta)
        self._move_individual_and_ancestors(family.husb, family, -1000000)
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
        failed = []
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
                    start_y = graphical_individual_representation.get_birth_event()['ordinal_value']
                else:
                    start_y = list(x_pos.values())[i][0]
                if i < len(x_pos) - 1:
                    end_y = list(x_pos.values())[i+1][0]
                else:
                    end_y = graphical_individual_representation.get_death_event()['ordinal_value']
                position_to_person_map[x_index].append({
                    'start':start_y,
                    'end':end_y,
                    'individual':graphical_individual_representation
                })
                
                v[x_index].append(graphical_individual_representation)
                max_x = max(max_x, x_index)
                min_x = min(min_x, x_index)
        if len(collisions) > 0:
            raise LifeLineChartCollisionDetected()
                
        # block every x_index from birth to death in which an individual appears
        for x_index, graphical_individual_representation_list in v.items():
            x_positions = []
            for index, graphical_individual_representation_a in enumerate(graphical_individual_representation_list):
                for graphical_individual_representation_b in graphical_individual_representation_list[index+1:]:
                    birth_position_a = graphical_individual_representation_a.get_birth_event()['ordinal_value'] - 365*15
                    birth_position_b = graphical_individual_representation_b.get_birth_event()['ordinal_value'] - 365*15
                    death_position_a = graphical_individual_representation_a.get_death_event()['ordinal_value'] + 365*15
                    death_position_b = graphical_individual_representation_b.get_death_event()['ordinal_value'] + 365*15
                    if ((birth_position_a - birth_position_b)
                        *(birth_position_a - death_position_b) < 0 or
                        (death_position_a - birth_position_b)
                        *(death_position_a - death_position_b) < 0 or
                        (birth_position_b - birth_position_a)
                        *(birth_position_b - death_position_a) < 0 or
                        (death_position_b - birth_position_a)
                        *(death_position_b - death_position_a) < 0
                            ):
                        if early_raise:
                            raise LifeLineChartCollisionDetected(graphical_individual_representation_a, graphical_individual_representation_b)
                        collisions.append((graphical_individual_representation_a, graphical_individual_representation_b))
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
            x_indices = set()
            index_map = {}
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
                    logger.error("failed: " +str((x_index, value[2].family_id, graphical_individual_representation.name, v[x_index])))
                    #raise RuntimeError((x_index, key, graphical_individual_representation.name))
        full_index_list = list(sorted(v.keys()))
        for i in range(len(full_index_list)):
            if i not in full_index_list:
                graphical_individual_representation.items.append({
                    'type': 'rect',
                    'config': {
                        'insert' : (self._map_x_position(i), self._map_y_position(self.max_ordinal)),
                        'size' : (self._formatting['relative_line_thickness']*self._formatting['vertical_step_size'], self._map_y_position(self.min_ordinal)),
                        'fill' : 'black',
                        'fill-opacity':"0.5"
                    }
                })
                failed.append(('missing',i))
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
            self._formatting['margin_top']  
            - self._formatting['total_height'] * (self._formatting['display_factor']-1)/2 
            + (ordinal_value - self.min_ordinal)/(self.max_ordinal-self.min_ordinal) * self._formatting['total_height'] * self._formatting['display_factor']
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
        from math import pi, sin, cos
        if self._formatting['warp_shape'] == 'sine':
            y_rel = (1-sin((1-(pos_y - self.min_ordinal)/(self.max_ordinal - self.min_ordinal))*pi/2))*0.5
            x_av = (self.max_x_index + self.min_x_index)/2
            
            return self._map_x_position(pos_x*(1-y_rel) + y_rel*x_av), self._map_y_position(pos_y)
        elif self._formatting['warp_shape'] == 'triangle':
            y_rel = (pos_y - self.min_ordinal)/(self.max_ordinal - self.min_ordinal)*0.8
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
        from math import pi, sin, cos, atan, sqrt, asin
        p1 = self._map_position(pos_x, pos_y-0.5)
        p2 = self._map_position(pos_x, pos_y+0.5)
        gegen_kathete = p2[0]-p1[0]
        an_kathete = p2[1]-p1[1]
        hypotenuse = sqrt(gegen_kathete*gegen_kathete + an_kathete*an_kathete)
        angle = asin(gegen_kathete/hypotenuse)
        angle_deg = angle/pi*180 
        
        return angle_deg

    def _inverse_y_position(self, pos_y):
        return (
            pos_y
            - self._formatting['margin_top']
            + self._formatting['total_height'] * (self._formatting['display_factor']-1)/2 
        ) / (self._formatting['total_height'] * self._formatting['display_factor']) * (self.max_ordinal-self.min_ordinal) + self.min_ordinal

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
        return abs(self._map_y_position(self.min_ordinal) - self._map_y_position(self.max_ordinal)) + self._formatting['margin_bottom']

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
        if not possible_matches is None:
            for possible_match in possible_matches:
                if possible_match['start'] < ordinal_value and possible_match['end'] > ordinal_value:
                    return possible_match['individual'] 
        return None
                    # print(possible_match['individual'].individual.plain_name)
                    # print(datetime.date.fromordinal(ordinal_value))
                    # print(x_index)
  
