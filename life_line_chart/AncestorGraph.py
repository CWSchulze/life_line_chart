import os
from .SimpleSVGItems import Line, Path, CubicBezier
import logging
import hashlib
import datetime
import svgwrite
from copy import deepcopy
from .BaseGraph import BaseGraph, get_gedcom_instance_container
from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected
from cmath import sqrt, exp, pi

logging.basicConfig()  # level=20)
logger = logging.getLogger("life_line_chart")
logger.setLevel(logging.INFO)

J = exp(2j*pi/3)
Jc = 1/J


def Cardano(a, b, c, d):
    z0 = b/3/a
    a2, b2 = a*a, b*b
    p = -b2/3/a2 + c/a
    q = (b/27*(2*b2/a2-9*c/a)+d)/a
    D = -4*p*p*p-27*q*q
    r = sqrt(-D/27+0j)
    u = ((-q-r)/2)**0.33333333333333333333333
    v = ((-q+r)/2)**0.33333333333333333333333
    w = u*v
    w0 = abs(w+p/3)
    w1 = abs(w*J+p/3)
    w2 = abs(w*Jc+p/3)
    if w0 < w1:
        if w2 < w0:
            v *= Jc
    elif w2 < w1:
        v *= Jc
    else:
        v *= J
    return u+v-z0, u*J+v*Jc-z0, u*Jc+v*J-z0

class AncestorGraph(BaseGraph):
    """
    This class enables setting up ancestor graphs and save them
    """

    def __init__(self, positioning=None, formatting=None, instance_container=get_gedcom_instance_container):
        BaseGraph.__init__(self, positioning, formatting, instance_container)
        # self._graphical_family_class = ancestor_graph_family # TODO: necessary if other graphs are implemented
        # self._graphical_individual_class = ancestor_graph_individual # TODO: necessary if other graphs are implemented

    def select_individuals(self, individual, generations=None, color=None, filter=None):
        """
        Select individuals to show. This is done by creating instances of graphical representations.

        Args:
            individual (BaseIndividual): starting point for selection
            generations (int, optional): number of generations to search for ancestors. Defaults to None.
            color (list, optional): RGB color. Defaults to None.
            filter (lambda, optional): lambda(BaseIndividual) : return Boolean. Defaults to None.
        """

        if filter and filter(individual):
            return

        if generations is None:
            generations = self._positioning['generations']

        if not individual.has_graphical_representation():
            individual_representation = self._create_individual_graphical_representation(
                individual)

            if individual_representation is None:
                return

            if color is None:
                i = int(hashlib.sha1(" ".join(individual_representation.name).encode(
                    'utf8')).hexdigest(), 16) % (10 ** 8)
                c = (i*23 % 255, i*41 % 255, (i*79 % 245) + 10)
                f = 255/max(c)
                c = [int(x*f) for x in c]
                f = min(1, 500/sum(c))
                c = [int(x*f) for x in c]
                individual_representation.color = c
            else:
                individual_representation.color = color
        else:
            individual_representation = individual.graphical_representations[0]

        child_of_families = individual.get_child_of_family()
        for child_of_family in child_of_families:
            family = self._create_family_graphical_representation(
                child_of_family)
            family.add_visible_children(individual)
            individual_representation.visible_parent_family = family
            if generations > 0 or generations < 0:
                # parents = individual.get_father_and_mother()
                father, mother = child_of_family.get_husband_and_wife()
                if father:
                    self.select_individuals(
                        father, generations - 1, color=individual_representation.color if self._positioning['fathers_have_the_same_color'] else None, filter=filter)
                if mother:
                    self.select_individuals(
                        mother, generations - 1, filter=filter)
            # family.visible_children.sort()
    def place_selected_individuals(self, individual, child_family, spouse_family, child_of_family, x_offset=0):
        """
        Place the graphical representations in direction of x

        Args:
            individual (BaseIndividual): individual
            child_family (BaseFamily): I dont remember
            spouse_family (BaseFamily): Spouse family of this individual
            child_of_family (BaseFamily): child-of-family of this individual
        """
        # logger.info('start setting placement')
        x_position = x_offset
        individual.graphical_representations[0].x_start = x_position
        self.min_x_index = min(self.min_x_index, x_position)
        child_of_families = individual.get_child_of_family()
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
                    local_child_of_family.graphical_representations[0].visual_placement_child = individual
                    # father.graphical_representations[0].visual_placement_child = spouse_family
                    self.place_selected_individuals(
                        father, spouse_family, local_child_of_family, fathers_born_in_family, x_position)
                    # x_position = father.graphical_representations[0].get_x_position()
                    width = father.graphical_representations[0].get_width(
                        spouse_family)
                    if local_child_of_family:
                        local_child_of_family.graphical_representations[0].husb_width = width
                    x_position += width

        children_start_x = x_position
        if individual.graphical_representations[0].get_x_position() is None or spouse_family is not None and spouse_family.family_id not in individual.graphical_representations[0].get_x_position() or False:
            individual.graphical_representations[0].set_x_position(
                x_position, spouse_family)
            # if child_of_family :# and len(child_of_family.graphical_representations[0].visible_children) > 1:
            if child_of_family and not child_of_family.family_id in individual.graphical_representations[0].get_x_position():
                individual.graphical_representations[0].set_x_position(
                    x_position, child_of_family, True)
            x_position += 1
        if not child_of_family or not child_of_family.graphical_representations:
            # x_position += 1
            if True or not individual.graphical_representations[0].get_x_position() or False:
                pass
        else:
            for _, _, sibling in sorted(child_of_family.graphical_representations[0].visible_children.values()):
                if sibling.individual_id == individual.individual_id:
                    if not sibling.graphical_representations[0].get_x_position() or not child_of_family.family_id in sibling.graphical_representations[0].get_x_position():
                        pass
                        # sibling.graphical_representations[0].set_x_position(x_position - 1, child_of_family)
                        # x_position += 1
                else:
                    if not sibling.graphical_representations[0].get_x_position() or not child_of_family.family_id in sibling.graphical_representations[0].get_x_position():
                        if not sibling.graphical_representations[0].visual_placement_child:
                            sibling.graphical_representations[
                                0].visual_placement_child = individual.graphical_representations[0].visual_placement_child
                            sibling.graphical_representations[0].set_x_position(
                                x_position, child_of_family)
                        # if sibling != individual:
                            x_position += 1

                    # for marriage in sibling.marriages:
                    #     sibling.graphical_representations[0].set_x_position()
                    #     print ("s")
        if child_of_family and child_of_family.has_graphical_representation() and not child_of_family.graphical_representations[0].children_width:
            child_of_family.graphical_representations[0].children_width = x_position - \
                children_start_x

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
                    # mother.graphical_representations[0].visual_placement_child = spouse_family
                    local_child_of_family.graphical_representations[0].visual_placement_child = individual
                    self.place_selected_individuals(
                        mother, spouse_family, local_child_of_family, mothers_born_in_family, x_position)
                    # x_position = mother.graphical_representations[0].get_x_position()
                    width = mother.graphical_representations[0].get_width(
                        spouse_family)
                    if local_child_of_family:
                        local_child_of_family.graphical_representations[0].wife_width = width
                    x_position += width
        self.max_x_index = max(self.max_x_index, x_position)
        individual.graphical_representations[0].x_end = x_position
        if child_of_family:
            if child_of_family.family_id not in individual.graphical_representations[0].widths:
                if child_of_family and child_of_family.has_graphical_representation() and len(child_of_family.graphical_representations[0].visible_children) > 1:
                    individual.graphical_representations[0].widths[child_of_family.family_id] = max(
                        0, individual.graphical_representations[0].x_end - individual.graphical_representations[0].x_start)
                    individual.graphical_representations[0].range[child_of_family.family_id] = (
                        individual.graphical_representations[0].x_start, individual.graphical_representations[0].x_end)
                else:
                    individual.graphical_representations[0].widths[child_of_family.family_id] = max(
                        0, individual.graphical_representations[0].x_end - individual.graphical_representations[0].x_start)
                    individual.graphical_representations[0].range[child_of_family.family_id] = (
                        individual.graphical_representations[0].x_start, individual.graphical_representations[0].x_end)
                    # print("as")
            # else:
            #     logger.info("Width was already set for "+child_of_family.family_id)

        if not child_of_family or not child_of_family.graphical_representations:
            if child_family not in individual.graphical_representations[0].widths:
                if child_family:
                    individual.graphical_representations[0].widths[child_family.family_id] = 1
                else:
                    individual.graphical_representations[0].widths[child_family] = 1
            pass
        else:
            for _, _, sibling in sorted(child_of_family.graphical_representations[0].visible_children.values()):
                if child_family:
                    sibling.graphical_representations[0].widths[child_family.family_id] = max(
                        0, individual.graphical_representations[0].x_end - individual.graphical_representations[0].x_start)
                    sibling.graphical_representations[0].range[child_family.family_id] = (
                        individual.graphical_representations[0].x_start, individual.graphical_representations[0].x_end)
                else:
                    sibling.graphical_representations[0].widths[child_family] = max(
                        0, individual.graphical_representations[0].x_end - individual.graphical_representations[0].x_start)
                    sibling.graphical_representations[0].range[child_family] = (
                        individual.graphical_representations[0].x_start, individual.graphical_representations[0].x_end)
        min_ordinal = 9e99
        max_ordinal = -9e99
        for graphical_individual_representation in self.graphical_individual_representations:
            birth_event = graphical_individual_representation.get_birth_event()
            if not birth_event:
                continue
            birth_ordinal_value = birth_event['ordinal_value']
            death_event = graphical_individual_representation.get_death_event()
            death_ordinal_value = death_event['ordinal_value']
            min_ordinal = min(min_ordinal, birth_ordinal_value)
            max_ordinal = max(max_ordinal, death_ordinal_value)
        self.min_ordinal = min_ordinal-3000
        self.max_ordinal = max_ordinal+3000

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
            

    def _compress_graph_ancestor_graph(self, graphical_family_representation):
        """
        compress the graph vertically.

        Args:
            graphical_family_representation (AncestorGraphFamily): graphical family representation instance
        """
        individuals = []
        if graphical_family_representation is None:
            return

        family_was_flipped = False
        x_pos_husb = None
        x_pos_wife = None
        if graphical_family_representation.husb is not None and graphical_family_representation.husb.has_graphical_representation():
            x_pos_husb = graphical_family_representation.husb.graphical_representations[0].get_x_position()[
                               graphical_family_representation.family_id][1]
            individuals.append((1, graphical_family_representation.husb))
        if graphical_family_representation.wife is not None and graphical_family_representation.wife.has_graphical_representation():
            x_pos_wife = graphical_family_representation.wife.graphical_representations[0].get_x_position()[
                            graphical_family_representation.family_id][1]
            individuals.append((-1, graphical_family_representation.wife))
        if x_pos_husb and x_pos_wife and x_pos_husb > x_pos_wife:
            family_was_flipped = True
        
        for index, (_, individual) in enumerate(sorted(individuals)):
            cofs = individual.get_child_of_family()
            for cof in cofs:
                if cof.has_graphical_representation():
                    if cof.husb is None or cof.wife is None \
                            or not cof.husb.has_graphical_representation() \
                            or not cof.wife.has_graphical_representation():
                        this_individual_x_pos = individual.graphical_representations[0].get_x_position()[cof.family_id][1]
                        parent_x_pos = None
                        if cof.husb is not None and cof.husb.has_graphical_representation():
                            parent_x_pos = cof.husb.graphical_representations[0].get_x_position()[cof.family_id][1]
                        if cof.wife is not None and cof.wife.has_graphical_representation():
                            parent_x_pos = cof.wife.graphical_representations[0].get_x_position()[cof.family_id][1]
                        if parent_x_pos is not None and this_individual_x_pos > parent_x_pos:
                            self._compress_single_individual_position(individual, cof, -1)
                            # self._move_single_individual(individual, cof, parent_x_pos - this_individual_x_pos + 1)
                        elif parent_x_pos is not None and this_individual_x_pos < parent_x_pos:
                            self._compress_single_individual_position(individual, cof, 1)
                            # self._move_single_individual(individual, cof, parent_x_pos - this_individual_x_pos - 1)
                    self._compress_graph_ancestor_graph(
                        cof.graphical_representations[0])
        for index, (original_direction_factor, individual) in enumerate(sorted(individuals)):
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
            except LifeLineChartCollisionDetected:
                # print("   collision of " + " and ".join([" ".join(a.name) for a in e.args]))
                self._move_individual_and_ancestors(
                    individual, individual.graphical_representations[0].visible_parent_family, -direction_factor*1)
            except LifeLineChartCannotMoveIndividual:
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
            items = list(reversed(sorted([(child.graphical_representations[0].get_birth_event()[
                         'ordinal_value'], index, child) for index, child in enumerate(candidantes)])))
            failed = []
            for ov, index, child in items:
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
                    if new_width > width:
                        self._flip_family(x_pos[2])
                    else:
                        width = new_width
                # print (x_pos)
                if len(failed) > 0:
                    break

            logger.info(
                f"flipping reduced the cross connections by {width - old_width} (i.e. from {old_width} to {width})")

        # for graphical_family_representation in self.graphical_family_representations:
        if self._positioning['compress']:
            failed, old_x_min_index, old_x_max_index = self.check_unique_x_position()
            old_width = old_x_max_index - old_x_min_index
            self.compression_steps = 1e30
            if 'compression_steps' in self._formatting and self._formatting['compression_steps'] > 0:
                self.compression_steps = self._formatting['compression_steps']
            self._compress_graph_ancestor_graph(self._instances[(
                'i', root_individual_id)].graphical_representations[0].visible_parent_family)

            # compressed graph should be aligned left
            _, min_index_x, max_index_x, self.position_to_person_map = self._check_compressed_x_position(False)
            self._move_individual_and_ancestors(self._instances[('i',root_individual_id)], sorted(list(self._instances[('i',root_individual_id)].graphical_representations[0].get_x_position().values()))[0][2], -(min_index_x-old_x_min_index)*1)
            keys = sorted(list(self.position_to_person_map.keys()))
            for key in keys:
                self.position_to_person_map[key - (old_x_min_index - min_index_x) * 1] = self.position_to_person_map.pop(key)
            width = (max_index_x - min_index_x)
            self.min_x_index = 0
            self.max_x_index = width
            logger.info(f"compression reduced the total width by {width - old_width} (i.e. from {old_width} to {width})")
        else:
            _, _, _, self.position_to_person_map = self._check_compressed_x_position(
                False)
        # for collision in collisions:
        #     if collision[1] is None:
        #         print("collision of " + " ".join(collision[0].name))
        #     else:
        #         print("collision of " + " ".join(collision[0].name) + " with " + " ".join(collision[1].name))

    def clear_svg_items(self):
        """
        clear all graphical items to render the graph with different settings
        """
        self.additional_graphical_items = {}
        self.additional_graphical_items['grid'] = []
        for graphical_individual_representation in self.graphical_individual_representations:
            graphical_individual_representation.items.clear()

    def define_svg_items(self):
        """
        generate graphical item information used for rendering the image.
        """
        logger.debug('start creating graphical items')

        self.additional_graphical_items = {}
        self.additional_graphical_items['grid'] = []

        font_size = self._formatting['font_size_description']*self._formatting['relative_line_thickness']*self._formatting['vertical_step_size']

        # setup grid
        max_y = max(self._map_y_position(self.min_ordinal),
                    self._map_y_position(self.max_ordinal))
        min_y = min(self._map_y_position(self.min_ordinal),
                    self._map_y_position(self.max_ordinal))
        min_x_index = self.min_x_index
        max_x_index = self.max_x_index
        for index in range(600):
            year = 1000 + 2*index
            year_pos = self._map_y_position(
                datetime.date(year, 1, 1).toordinal())
            if year_pos > 0 and year_pos < max_y:
                if year % 10 == 0:
                    self.additional_graphical_items['grid'].append({
                        'type': 'path',
                                'config': {'type': 'Line', 'arguments': (0 + year_pos*1j, self.get_full_width() + year_pos*1j)},
                                'color': [210]*3,
                                'stroke_width': 1
                    }
                    )
                    self.additional_graphical_items['grid'].append({
                        'type': 'text',
                                'config': {
                                    'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                                    'text': str(year),
                                    'text-anchor': 'end',
                                    # 'align' : 'center',
                                    'insert': (self.get_full_width() - self._formatting['vertical_step_size']*0.1, year_pos),
                                },
                        'font_size': font_size,
                        'font_name': self._formatting['font_name'],
                    }
                    )
                else:
                    self.additional_graphical_items['grid'].append({
                        'type': 'path',
                                'config': {'type': 'Line', 'arguments': (0 + year_pos*1j, self.get_full_width() + year_pos*1j)},
                                'color': [210]*3,
                                'stroke_width': 0.1
                    }
                    )
        for index in range(1000):
            x_position = index*100
            if x_position > min_x_index and x_position < max_x_index:
                svg_path = Path(
                    Line(x_position + min_y*1j, x_position + max_y*1j))
                if index % 20 == 0:
                    for index2 in range(600):
                        year = 1000 + 2*index2
                        year_pos = self._map_y_position(
                            datetime.date(year, 1, 1).toordinal())
                        if year_pos > 0 and year_pos < max_y:
                            if year % 10 == 0:
                                self.additional_graphical_items['grid'].append({
                                    'type': 'text',
                                            'config': {
                                                'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                                                'text': str(year),
                                                'text-anchor': 'end',
                                                # 'align' : 'center',
                                                'insert': (x_position-5, year_pos),
                                            },
                                    'font_size': font_size,
                                    'font_name': self._formatting['font_name'],
                                }
                                )
                if index % 10 == 0:
                    self.additional_graphical_items['grid'].append({
                        'type': 'path',
                                'config': {'type': 'Line', 'arguments': (x_position + min_y*1j, x_position + max_y*1j)},
                                'color': [210]*3,
                                'stroke_width': 1
                    }
                    )
                else:
                    self.additional_graphical_items['grid'].append({
                        'type': 'path',
                                'config': {'type': 'Line', 'arguments': (x_position + min_y*1j, x_position + max_y*1j)},
                                'color': [210]*3,
                                'stroke_width': 0.1
                    }
                    )

        min_x_index = 9e99
        max_x_index = -9e99
        for graphical_individual_representation in self.graphical_individual_representations:
            x_positions = graphical_individual_representation.get_x_position()
            for _, x_position in x_positions.items():
                min_x_index = min(min_x_index, x_position[1])
                max_x_index = max(max_x_index, x_position[1])
        self.min_x_index = min_x_index  # -1000
        self.max_x_index = max_x_index + 1  # +200

        for graphical_individual_representation in self.graphical_individual_representations:
            birth_label = graphical_individual_representation.birth_label
            death_label = graphical_individual_representation.death_label
            birth_event = graphical_individual_representation.get_birth_event()
            if not birth_event:
                continue
            death_event = graphical_individual_representation.get_death_event()

            # individual_id = graphical_individual_representation.individual_id
            individual_name = graphical_individual_representation.name
            # positions[individual_id]

            # individual = self._instances[('i',individual_id)]
            x_pos = graphical_individual_representation.get_x_position()
            x_pos_list = sorted([(ov, pos, index, family_id, flag)
                                 for index, (family_id, (ov, pos, f, flag)) in enumerate(x_pos.items())])

            # collect information about marriages
            marriage_ordinals = []
            marriage_ring_indices = []
            marriage_y_positions = []
            marriage_ring_positions = []
            new_x_position_after_marriage = []
            new_x_indices_after_marriage = []
            marriage_labels = []
            if graphical_individual_representation.get_marriages():
                for graphical_representation_marriage_family in graphical_individual_representation.get_marriages():
                    if graphical_representation_marriage_family.marriage is None:
                        continue
                    spouse_representation = graphical_representation_marriage_family.get_spouse(
                        graphical_individual_representation.individual)
                    marriage_x_index = x_pos[graphical_representation_marriage_family.family_id][1]
                    new_x_position_after_marriage.append(
                        self._map_x_position(marriage_x_index))
                    new_x_indices_after_marriage.append(marriage_x_index)

                    if spouse_representation and spouse_representation.get_x_position() and graphical_representation_marriage_family.marriage:
                        # if there is a spouse, choose the middle between them
                        spouse_x_index = spouse_representation.get_x_position(
                        )[graphical_representation_marriage_family.family_id][1]
                        # spouse_x_position = self._map_x_position(spouse_x_index)
                        marriage_ring_positions.append(self._map_position(
                            (spouse_x_index + marriage_x_index)/2.,
                            graphical_representation_marriage_family.marriage['ordinal_value']))
                        marriage_ring_indices.append(
                            (spouse_x_index + marriage_x_index)/2.)
                    else:
                        # if no spouse is visible, place over the children
                        child_x_indices = []
                        for _, (_, _, visible_child) in graphical_representation_marriage_family.visible_children.items():
                            try:
                                child_x_indices.append(visible_child.graphical_representations[0].get_x_position()[
                                                       graphical_representation_marriage_family.family_id][1])
                            except:
                                logger.error('something went wrong with ' + "".join(visible_child.name) +
                                      ". The position family 0 is not equal to the placement...")
                        if len(child_x_indices) > 0:
                            # calculate the middle over the children
                            marriage_ring_positions.append(self._map_position(
                                sum(child_x_indices)/len(child_x_indices),
                                graphical_representation_marriage_family.marriage['ordinal_value']))
                            marriage_ring_indices.append(
                                sum(child_x_indices)/len(child_x_indices))
                        else:
                            # place at the individual line... no spouse, no children, what is this information good for?
                            marriage_ring_positions.append(self._map_position(
                                x_pos[graphical_representation_marriage_family.family_id][1],
                                graphical_representation_marriage_family.marriage['ordinal_value']))
                            marriage_ring_indices.append(
                                x_pos[graphical_representation_marriage_family.family_id][1])

                    marriage_y_positions.append(self._map_y_position(
                        graphical_representation_marriage_family.marriage['ordinal_value']))
                    marriage_ordinals.append(
                        graphical_representation_marriage_family.marriage['ordinal_value'])
                    marriage_labels.append(
                        str(graphical_representation_marriage_family.label))


            # generate event node information
            knots = []
            _birth_original_location = (
                x_pos_list[0][1], birth_event['ordinal_value'])
            _death_original_location = (
                x_pos_list[-1][1], death_event['ordinal_value'])
            _birth_position = self._map_position(*_birth_original_location)
            _death_position = self._map_position(*_death_original_location)
            knots.append((x_pos_list[0][1], birth_event['ordinal_value']))
            images = []
            import os
            for index, (marriage_ring_index, marriage_ordinal, new_x_index_after_marriage, label) in enumerate(zip(marriage_ring_indices, marriage_ordinals, new_x_indices_after_marriage, marriage_labels)):
                if not self._formatting['no_ring']:
                    ring_position = self._map_position(
                        marriage_ring_index, marriage_ordinal)
                    images.append(
                        {
                            'type': 'image',
                            'config': {
                                'insert': (
                                    ring_position[0] - self._formatting['relative_line_thickness'] *
                                    self._formatting['vertical_step_size']*1,
                                    ring_position[1] - self._formatting['relative_line_thickness']*self._formatting['vertical_step_size']*1),
                                'size': (
                                    self._formatting['relative_line_thickness'] *
                                    self._formatting['vertical_step_size']*2,
                                    self._formatting['relative_line_thickness']*self._formatting['vertical_step_size']*2),
                            },
                            'filename': os.path.join(os.path.dirname(__file__), "ringe.png")
                        }
                    )
                if self._formatting['marriage_label_active']:
                    dy_line = self._inverse_y_position(
                        self._formatting['relative_line_thickness']*self._formatting['vertical_step_size']) - self._inverse_y_position(0)
                    for index, line in enumerate(label.split('\n')):
                        position = self._map_position(marriage_ring_index, marriage_ordinal + dy_line)
                        position = (position[0], position[1] + (index + 0.2) * font_size * 1.2)
                        images.append({
                                'type': 'text',
                                'config': {
                                    'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                                    'text': line,
                                    'text-anchor': 'middle',
                                    # 'align' : 'center',
                                    'insert': position,
                                },
                                'font_size': font_size,
                                'font_name': self._formatting['font_name'],
                            })
                knots.append((marriage_ring_index, marriage_ordinal))
                if len(marriage_ordinals) > index + 1:
                    # zwischenpunkt zur ursprungsposition
                    knots.append(
                        (new_x_index_after_marriage, marriage_ordinals[index]/2+marriage_ordinals[index+1]/2))
            knots.append((x_pos_list[-1][1], death_event['ordinal_value']))

            Path_types = {
                'Line': Line,
                'CubicBezier':CubicBezier
            }
            # for ov, filename in graphical_individual_representation.individual.images.items():
            #     foto_size = self._formatting['individual_foto_relative_size'] * self._formatting['relative_line_thickness'] * self._formatting['vertical_step_size']
            #     images.append(
            #             {
            #                 'type': 'image',
            #                 'config': {
            #                     'insert': (
            #                         _birth_position[0] - foto_size/2,
            #                         self._map_y_position(ov) - foto_size/2),
            #                     'size': (foto_size,foto_size),
            #                 },
            #                 'filename': filename
            #             }
            #         )

            # generate spline paths
            def marriage_bezier(images, data, knots, flip=False):
                """
                tranlate event information to bezier splines

                Args:
                    data (list): data container to place the data
                    knots (list): list of event nodes
                    flip (bool, optional): flip shape of the spline. Defaults to False.
                """
                def coordinate_transformation(x, y):
                    new_x, new_y = self._map_position(x, y)
                    return new_x + new_y*1j
                if flip:
                    t = 1
                else:
                    t = 0
                if len(knots) == 2:
                    data.append(
                        ({'type': 'Line', 'arguments': (
                            coordinate_transformation(
                                knots[0][0], knots[0][1]),
                            coordinate_transformation(
                                knots[0+1][0], knots[0+1][1]),
                        )},
                            # ((knots[0][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value'])-_birth_position[1]), (knots[0+1][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value'])-_birth_position[1])),
                            (_birth_position[1], self._map_y_position(
                                self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value']))
                        )
                    )
                    if len(graphical_individual_representation.individual.images) > 0:
                        index = 0
                        svg_path = Path_types[data[-1][0]['type']](*data[-1][0]['arguments'])
                        for ov, filename in graphical_individual_representation.individual.images.items():
                            if ov >= knots[index][1] and ov <= knots[index + 1][1]:
                                foto_size = self._formatting['individual_foto_relative_size'] * self._formatting['relative_line_thickness'] * self._formatting['vertical_step_size']
                                foto_size_y = self._map_y_position(self._inverse_x_position(foto_size))
                                # xpos = svg_path.intersect(Line(coordinate_transformation(min(knots[index][0],knots[index + 1][0])-1, ov), coordinate_transformation(max(knots[index][0],knots[index + 1][0])+1, ov)))[0]
                                # xpos = svg_path.point(xpos[0])
                                if type(svg_path) == Line:
                                    xpos = svg_path.start.real + self._map_y_position(ov)*1j
                                else:
                                    coeffs = svg_path.poly()
                                    coeffs2 = (coeffs[0].imag, coeffs[1].imag, coeffs[2].imag, coeffs[3].imag - self._map_y_position(ov))
                                    roots = Cardano(*coeffs2)
                                    root = [root.real for root in roots if abs(root.imag) < 1e-10][0]
                                    if len(root) > 0:
                                        xpos = svg_path.point(root[0])
                                    else:
                                        xpos = svg_path.point(roots[1])
                                images.append(
                                        {
                                            'type': 'image',
                                            'config': {
                                                'insert': (
                                                    xpos.real - foto_size/2,
                                                    xpos.imag - foto_size/2),
                                                'size': (foto_size,foto_size),
                                            },
                                            'filename': filename
                                        }
                                    )
                    # for ov, filename in graphical_individual_representation.individual.images.items():
                    #     if ov > knots[0][1] and ov < knots[1][1]:
                    #         foto_size = self._formatting['individual_foto_relative_size'] * self._formatting['relative_line_thickness'] * self._formatting['vertical_step_size']
                    #         images.append(
                    #                 {
                    #                     'type': 'image',
                    #                     'config': {
                    #                         'insert': (
                    #                             _birth_position[0] - foto_size/2,
                    #                             self._map_y_position(ov) - foto_size/2),
                    #                         'size': (foto_size,foto_size),
                    #                     },
                    #                     'filename': filename
                    #                 }
                    #             )
                else:
                    for index in range(len(knots)-1):
                        def interp(*val):
                            return (knots[index][0]*(1-val[0]) + knots[index+1][0]*val[0],
                                    knots[index][1]*(1-val[1]) + knots[index+1][1]*val[1])
                        if (index + t) % 2 == 0:
                            data.append(
                                ({'type': 'CubicBezier', 'arguments': (
                                    coordinate_transformation(*interp(0, 0)),
                                    coordinate_transformation(*interp(0, 1)) if self._formatting['family_shape'] == 0 else coordinate_transformation(*interp(0.0, 0.7)),
                                    coordinate_transformation(*interp(0, 1)) if self._formatting['family_shape'] == 0 else coordinate_transformation(*interp(0.5, 0.9)),
                                    coordinate_transformation(*interp(1, 1)),
                                )},
                                    # ((knots[index][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value'])-_birth_position[1]), (knots[index+1][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value'])-_birth_position[1])),
                                    (_birth_position[1], self._map_y_position(
                                        self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value']))
                                )
                            )
                        else:
                            data.append(
                                ({'type': 'CubicBezier', 'arguments': (
                                    coordinate_transformation(*interp(0, 0)),
                                    coordinate_transformation(*interp(1, 0)) if self._formatting['family_shape'] == 0 else coordinate_transformation(*interp(0.8, 0)),
                                    coordinate_transformation(*interp(1, 0)) if self._formatting['family_shape'] == 0 else coordinate_transformation(*interp(1, 0.2)),
                                    coordinate_transformation(*interp(1, 1)),
                                )},
                                    # ((knots[index][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value'])-_birth_position[1]), (knots[index+1][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value'])-_birth_position[1])),
                                    (_birth_position[1], self._map_y_position(
                                        self._formatting['fade_individual_color_black_age']*365+birth_event['ordinal_value']))
                                )
                            )
                        if len(graphical_individual_representation.individual.images) > 0:
                            svg_path = Path_types[data[-1][0]['type']](*data[-1][0]['arguments'])
                            for ov, filename in graphical_individual_representation.individual.images.items():
                                if ov > knots[index][1] and ov < knots[index + 1][1]:
                                    foto_size = self._formatting['individual_foto_relative_size'] * self._formatting['relative_line_thickness'] * self._formatting['vertical_step_size']
                                    foto_size_y = self._map_y_position(self._inverse_x_position(foto_size))
                                    # xpos = svg_path.intersect(Line(coordinate_transformation(min(knots[index][0],knots[index + 1][0])-1, ov), coordinate_transformation(max(knots[index][0],knots[index + 1][0])+1, ov)))[0]
                                    # xpos = svg_path.point(xpos[0])
                                    if type(svg_path) == Line:
                                        xpos = svg_path.start.real + self._map_y_position(ov)*1j
                                    else:
                                        coeffs = svg_path.poly()
                                        coeffs2 = (coeffs[0].imag, coeffs[1].imag, coeffs[2].imag, coeffs[3].imag - self._map_y_position(ov))
                                        #coeffs2 = (coeffs[0] - self._map_y_position(ov)*1j, coeffs[1], coeffs[2], coeffs[3])
                                        roots = Cardano(*coeffs2)
                                        root = [root.real for root in roots if abs(root.imag) < 1e-10 and root.real >= 0 and root.real <= 1]
                                        if len(root) > 0:
                                            xpos = svg_path.point(root[0])
                                        else:
                                            xpos = svg_path.point(roots[1])
                                    images.append(
                                            {
                                                'type': 'image',
                                                'config': {
                                                    'insert': (
                                                        xpos.real - foto_size/2,
                                                        xpos.imag - foto_size/2),
                                                    'size': (foto_size,foto_size),
                                                },
                                                'filename': filename
                                            }
                                        )
            life_line_bezier_paths = []
            marriage_bezier(images, life_line_bezier_paths, knots)

            # create item setup
            for path, color_pos in life_line_bezier_paths:
                graphical_individual_representation.items.append({
                    'type': 'path',
                    'config': path,
                    'color': graphical_individual_representation.color,
                    'color_pos': color_pos,
                    'stroke_width': self._formatting['relative_line_thickness']*self._formatting['vertical_step_size']
                }
                )
            if self._formatting['birth_label_active']:
                if self._formatting['birth_label_along_path']:
                    graphical_individual_representation.items.append(
                        {
                            'type': 'textPath',
                            'config': {
                                'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                                'text': '',
                                # 'transform':'rotate(90,%s, %s)' % _birth_position,
                                # 'insert' : _birth_position,
                                'dy': [str(float(font_size)/2.7)+'px'],
                            },
                            'spans': [
                                (individual_name[0], {
                                 'dx': [str(font_size*float(self._formatting['birth_label_letter_x_offset']))]}),
                                (individual_name[1], {
                                 'style': 'font-weight: bold'}),
                                (birth_label, {})
                            ],
                            'path': life_line_bezier_paths[0][0],
                            'font_size': font_size,
                            'font_name': self._formatting['font_name'],
                        })
                else:
                    graphical_individual_representation.items.append(
                        {
                            'type': 'text',
                            'config': {
                                'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                                'text': individual_name[0] + ' ' + individual_name[1] + birth_label,
                                'transform': 'rotate(%s,%s, %s)' % (-90+self._orientation_angle(*_birth_original_location), *_birth_position),
                                'insert': _birth_position,
                                'dx': [str(font_size*float(self._formatting['birth_label_letter_x_offset']))],
                                'dy': [str(float(font_size)/2.7)+'px'],
                            },
                            'font_size': font_size,
                            'font_name': self._formatting['font_name'],
                        })
            if self._formatting['death_label_active']:
                graphical_individual_representation.items.append(
                    {
                        'type': 'text',
                        'config': {
                            'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                            'text': death_label,
                            'transform': 'rotate(%g,%s, %s)' % (self._formatting['death_label_rotation']+self._orientation_angle(*_death_original_location), *_death_position),
                            'insert': _death_position,
                            'dy': [str(float(font_size)/2.7)+'px'],
                            'dx': [str(font_size*float(self._formatting['death_label_letter_x_offset']))],
                        },
                        'font_size': font_size,
                        'font_name': self._formatting['font_name'],

                    }
                )
            graphical_individual_representation.items += images
    def paint_and_save(self, individual_id, filename=None):
        """
        setup svg file and save it.

        Args:
            individual_id (BaseIndividual): root person used for filename
            filename (str, optional): user defined filename. Defaults to None.
        """

        logger.debug('start creating document')
        max_y = max(self._map_y_position(self.min_ordinal),
                    self._map_y_position(self.max_ordinal))
        min_y = min(self._map_y_position(self.min_ordinal),
                    self._map_y_position(self.max_ordinal))

        # drawing = svg2rlg("file.svg")
        if filename is None:
            filename = 'ancestors_of_' + \
                "".join(self._instances[('i', individual_id)].name).replace(
                    ' ', '')
            if self._positioning['flip_to_optimize']:
                filename += '_flipped'
            if self._positioning['compress']:
                filename += '_compressed'
            if self._positioning['fathers_have_the_same_color']:
                filename += '_fathersSameColor'
            if self._formatting['fade_individual_color']:
                filename += '_fadeIndividualColor'
            filename += '.svg'
        # print(filename)
        svg_document = svgwrite.Drawing(filename=filename,
                                        size=(
                                            str(self.get_full_width()),
                                            str(self.get_full_height())))

        from PIL import Image
        import base64
        import os

        image_defs = {}
        additional_items = []
        for key, value in self.additional_graphical_items.items():
            additional_items += value
        sorted_individuals = [(gr.get_birth_event()['ordinal_value'], index, gr)
                              for index, gr in enumerate(self.graphical_individual_representations)]
        sorted_individuals.sort()
        sorted_individual_items = []
        for _, index, graphical_individual_representation in sorted_individuals:
            sorted_individual_items += graphical_individual_representation.items

        for item in additional_items + sorted_individual_items:
                if item['type'] == 'text':
                    args = item['config']
                    # args = deepcopy(item['config'])
                    # args['insert'] = (args['insert'][0], args['insert'][1])
                    svg_text = svg_document.text(
                        **args)
                    x = svg_document.add(svg_text)
                elif item['type'] == 'path':
                    arguments = deepcopy(item['config']['arguments'])
                    arguments = [individual_id for individual_id in arguments]
                    if item['config']['type'] == 'Line':
                        constructor_function = Line
                    elif item['config']['type'] == 'CubicBezier':
                        constructor_function = CubicBezier
                    svg_path = Path(constructor_function(*arguments))

                    if self._formatting['fade_individual_color'] and 'color_pos' in item:
                        fill = svg_document.linearGradient(("0", str(
                            item['color_pos'][0])+""), ("0", str(item['color_pos'][1])+""), gradientUnits='userSpaceOnUse')
                        fill.add_stop_color(
                            0, "rgb({},{},{})".format(*item['color']))
                        fill.add_stop_color(1, 'black')
                        # fill.add_stop_color(0, "rgb({},{},{})".format(*item['colors'][1]))
                        # fill.add_stop_color(1, "rgb({},{},{})".format(*item['colors'][0]))
                        svg_document.defs.add(fill)
                        svg_document.add(svg_document.path(d=svg_path.d(), stroke=fill.get_paint_server(
                            default='currentColor'), fill='none', stroke_width=item['stroke_width']))
                    else:
                        # arguments['fill'] = fill
                        # graphical_individual_representation.color
                        svg_document.add(svg_document.path(d=svg_path.d(), stroke="rgb({},{},{})".format(
                            *item['color']), fill='none', stroke_width=item['stroke_width']))
                elif item['type'] == 'textPath':
                    args_path = item['path']
                    args_text = item['config']
                    svg_text = svg_document.text(
                        **args_text)
                    if args_path['type'] == 'Line':
                        constructor_function = Line
                    elif args_path['type'] == 'CubicBezier':
                        constructor_function = CubicBezier
                    svg_path = Path(constructor_function(
                        *args_path['arguments']))
                    y = svg_document.path(svg_path.d(), fill='none')
                    svg_document.add(y)
                    # x = svg_document.add(svg_text)
                    x = svg_document.add(svgwrite.text.Text(
                        '', dy=[args_text['dy']], style=args_text['style']))
                    t = svgwrite.text.TextPath(y, text=args_text['text'])
                    for span in item['spans']:
                        t.add(svg_document.tspan(span[0], **span[1]))
                    x.add(t)

                elif item['type'] == 'image':
                    # marriage_pos and 'spouse' in positions[individual_id]['marriage']:
                    # m_pos_x = (positions[positions[individual_id]['marriage']['spouse']]['x_position'] + x_pos)/2
                    # image_data = img.tobytes()# img.make_blob(format='png')
                    this_def = {}
                    pos_x = item['config']['insert'][0]
                    pos_y = item['config']['insert'][1]
                    width = item['config']['size'][0]
                    height = item['config']['size'][1]
                    key = 'image_' + str(width) + '_' + str(height) + item['filename']
                    if key in image_defs:
                        this_def = image_defs[key]
                    else:
                        image_defs[key] = this_def
                        this_def['image_data'] = open(
                            item['filename'], 'rb').read()
                        this_def['encoded'] = base64.b64encode(
                            this_def['image_data']).decode()
                        this_def['pngdata'] = 'data:image/png;base64,{}'.format(
                            this_def['encoded'])
                        image = Image.open(item['filename'])
                        this_def['size'] = image.size
                        this_def['image_content'] = svg_document.image(
                            href=(this_def['pngdata']), preserveAspectRatio='xMidYMid', size=(1, 1))
                        this_def['image_def'] = svg_document.defs.add(
                            this_def['image_content'])
                    # factor_w = width/this_def['size'][0]
                    # factor_h = height/this_def['size'][1]
                    # factor = min(factor_w, factor_h)
                    # width = this_def['size'][0]*factor
                    # height = this_def['size'][1]*factor

                    svg_document.add(svg_document.use(this_def['image_def'].get_iri(
                    ), transform=f"translate({pos_x-width/2*0},{pos_y - height/2*0}) scale({width},{height})"))
                    pass

                elif item['type'] == 'rect':
                    this_rect = svg_document.rect(**item['config'])

                    # insert=(rect[0], rect[1]), size = (rect[2]-rect[0], rect[3]-rect[1]), fill = 'none')
                    svg_document.add(this_rect)

        logger.debug('start saving document')
        svg_document.save(True)
