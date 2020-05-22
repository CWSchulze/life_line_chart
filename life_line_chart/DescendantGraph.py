import os
from .SimpleSVGItems import Line, Path, CubicBezier
import logging
import hashlib
import datetime
import svgwrite
from copy import deepcopy
from .BaseGraph import BaseGraph, get_gedcom_instance_container
from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected
#from cmath import sqrt, exp, pi
from math import floor, ceil, sqrt, exp, pi

logger = logging.getLogger("life_line_chart")

J = 2#exp(2j*pi/3)
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


class DescendantGraph(BaseGraph):
    """
    Descendant Graph
    ==============

    # The ancestor graph shows the ancestors of one or more root individuals.
    # The parents only enclose direct children. Both, father and mother are
    # visible. Usually ancestors are visible, optionally all children of a
    # visible family can be added.
#
    # Each individual appears once. So in case of a second marriage, the
    # individual is connected across the chart to the second spouse. Because
    # of that, ancestor collapse is visualized.
    """

    def __init__(self, positioning=None, formatting=None, instance_container=get_gedcom_instance_container):
        BaseGraph.__init__(self, positioning, formatting, instance_container)
        self.x_pos = 0

        # configuration of this graph
        self._chart_configuration.update(self.get_default_chart_configuration())
        # self._graphical_family_class = ancestor_graph_family # TODO: necessary if other graphs are implemented
        # self._graphical_individual_class = ancestor_graph_individual # TODO: necessary if other graphs are implemented

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

    def select_descendants(self, individual, generations=None, color=None, filter=None):

        if filter and filter(individual):
            return None

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

        for marriage in individual.marriages:
            if marriage.has_graphical_representation():
                continue

            #individual_representation.visible_parent_family = gr_marriage
            if generations > 0 or generations < 0:
                gr_marriage = self._create_family_graphical_representation(
                    marriage)
                # parents = individual.get_father_and_mother()

                spouse = marriage.get_spouse(individual.individual_id)
                if spouse is not None and not spouse.has_graphical_representation():
                    if filter is None or filter(spouse) == False:
                        spouse_representation = self._create_individual_graphical_representation(
                            spouse)

                        if spouse_representation is not None:
                            if color is None:
                                i = int(hashlib.sha1(" ".join(spouse_representation.name).encode(
                                    'utf8')).hexdigest(), 16) % (10 ** 8)
                                c = (i*23 % 255, i*41 % 255, (i*79 % 245) + 10)
                                f = 255/max(c)
                                c = [int(x*f) for x in c]
                                f = min(1, 500/sum(c))
                                c = [int(x*f) for x in c]
                                spouse_representation.color = c
                            else:
                                spouse_representation.color = color

                for child in marriage.children:
                    self.select_descendants(
                        child, generations - 1, filter=filter)
                    if child.has_graphical_representation():
                        gr_marriage.add_visible_children(child)
                        child.graphical_representations[0].visible_parent_family = gr_marriage
                cofs = individual.get_child_of_family()
                if len(cofs) > 0:
                    gr_marriage.visual_placement_parent_family = individual.get_child_of_family()[0]

    def select_family_children(self, family, filter=None):
        """
        Select children of a family. This is done by creating instances of graphical representations.

        Args:
            individual (BaseIndividual): starting point for selection
            filter (lambda, optional): lambda(BaseIndividual) : return Boolean. Defaults to None.
        """

        if not family.has_graphical_representation():
            gfr = self._create_family_graphical_representation(
                family)
        for child in family.get_children():
            if filter and filter(child):
                continue

            if not child.has_graphical_representation():
                individual_representation = self._create_individual_graphical_representation(
                    child)

                if individual_representation is None:
                    return

                i = int(hashlib.sha1(" ".join(individual_representation.name).encode(
                    'utf8')).hexdigest(), 16) % (10 ** 8)
                c = (i*23 % 255, i*41 % 255, (i*79 % 245) + 10)
                f = 255/max(c)
                c = [int(x*f) for x in c]
                f = min(1, 500/sum(c))
                c = [int(x*f) for x in c]
                individual_representation.color = c

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
        if not individual.has_graphical_representation():
            return
        x_position = x_offset
        graphical_individual_representation = individual.graphical_representations[0]
        graphical_individual_representation.x_start = x_position
        self.min_x_index = min(self.min_x_index, x_position)

        visible_marriages = \
            [marriage for marriage in individual.marriages \
                if marriage.has_graphical_representation() and (child_of_family is None or \
                    marriage.graphical_representations[0].visual_placement_parent_family.family_id == child_of_family.family_id)]


        if len(visible_marriages) == 0:
            graphical_individual_representation.set_x_position(
                    x_position, child_of_family, True)
            x_position += 1

        for marriage_index, marriage in enumerate(reversed(visible_marriages)):
            if not marriage.has_graphical_representation():
                continue

            if marriage_index == len(visible_marriages) - 1:
                if graphical_individual_representation.get_x_position() is None or \
                        child_of_family is not None and child_of_family.family_id not in graphical_individual_representation.get_x_position():
                    graphical_individual_representation.set_x_position(
                        x_position, child_of_family)

            if graphical_individual_representation.get_x_position() is None or \
                    marriage.family_id not in graphical_individual_representation.get_x_position():
                graphical_individual_representation.set_x_position(
                    x_position, marriage)
                x_position += 1
            # parents = individual.get_father_and_mother()


            for child in marriage.children:
                self.place_selected_individuals(
                    child, None, None, marriage, x_position,
                    discovery_cache=discovery_cache)
                if child.has_graphical_representation():
                    width = child.graphical_representations[0].get_width2(
                        marriage)
                    x_position += width

            spouse = marriage.get_spouse(individual.individual_id)
            if spouse is not None and spouse.has_graphical_representation():
                spouse_representation = spouse.graphical_representations[0]
                if not spouse.graphical_representations[0].get_x_position() or marriage.family_id not in spouse.graphical_representations[0].get_x_position():
                    spouse_representation.set_x_position(
                        x_position, marriage)
                    x_position += 1

        self.max_x_index = max(self.max_x_index, x_position)

        # recalculate
        birth_ordinal_value = graphical_individual_representation.get_birth_date_ov()
        death_ordinal_value = graphical_individual_representation.get_death_date_ov()
        if self.min_ordinal is not None and self.max_ordinal is not None:
            self.min_ordinal = min(self.min_ordinal, birth_ordinal_value)
            self.max_ordinal = max(self.max_ordinal, death_ordinal_value)
        elif death_ordinal_value and birth_ordinal_value:
            self.min_ordinal = birth_ordinal_value
            self.max_ordinal = death_ordinal_value

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
                ###################
                # if value[3]:
                #     continue

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

    def modify_layout(self, root_individual_id):
        """
        improvement of individual placement.

        Args:
            root_individual_id (str): root individual id used as root node for compression
        """
        self.check_unique_x_position()

    def clear_graphical_representations(self):
        """
        clear all graphical representations to rebuild the chart
        """
        self.min_x_index = 0
        self.max_x_index = 0
        self.clear_svg_items()
        self._instances.ancestor_width_cache.clear()
        BaseGraph.clear_graphical_representations(self)

    def define_svg_items(self):
        """
        generate graphical item information used for rendering the image.
        """
        logger.debug('start creating graphical items')

        self.additional_graphical_items.clear()

        font_size = self._formatting['font_size_description'] * \
            self._formatting['relative_line_thickness'] * \
            self._formatting['vertical_step_size']

        if len(self.graphical_individual_representations) == 0:
            # settings for empty graphs
            self.min_x_index = 0
            self.max_x_index = 1
            self.min_ordinal = datetime.date(1900,1,1).toordinal()
            self.max_ordinal = datetime.date(2000,1,1).toordinal()

        # calculate outer chart bounds
        min_year = datetime.date.fromordinal(self.min_ordinal).year - self._formatting['margin_year_min']
        min_year = int(floor(min_year/10.)*10)
        self.chart_min_ordinal = datetime.date(min_year - 5, 1, 1).toordinal()
        max_year = datetime.date.fromordinal(self.max_ordinal).year + self._formatting['margin_year_max']
        max_year = int(ceil(max_year/10.)*10)
        self.chart_max_ordinal = datetime.date(max_year + 5, 1, 1).toordinal()

        # setup grid
        min_x_index = self.min_x_index
        max_x_index = self.max_x_index
        if 'grid' not in self.additional_graphical_items:
            self.additional_graphical_items['grid'] = []
        if 'axis' not in self.additional_graphical_items:
            self.additional_graphical_items['axis'] = []
        for year in range(min_year, max_year + 2, 2):
            year_pos = self._map_y_position(
                datetime.date(year, 1, 1).toordinal())
            if year % 10 == 0:
                # add bold line and number every 10 years
                self.additional_graphical_items['grid'].append({
                    'type': 'path',
                            'config': {'type': 'Line', 'arguments': (0 + year_pos*1j, self.get_full_width() + year_pos*1j)},
                            'color': [210]*3,
                            'stroke_width': 1
                }
                )
                self.additional_graphical_items['axis'].append({
                    'type': 'text',
                            'config': {
                                'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                                'text': str(year),
                                'text-anchor': 'end',
                                # 'align' : 'center',
                                'insert': (self.get_full_width() - self._formatting['vertical_step_size']*0.01, year_pos),
                            },
                    'font_size': font_size,
                    'font_name': self._formatting['font_name'],
                }
                )
            else:
                # add thin line
                self.additional_graphical_items['grid'].append({
                    'type': 'path',
                            'config': {'type': 'Line', 'arguments': (0 + year_pos*1j, self.get_full_width() + year_pos*1j)},
                            'color': [210]*3,
                            'stroke_width': 0.1
                }
                )

        min_x_index = 9e99
        max_x_index = -9e99
        for graphical_individual_representation in self.graphical_individual_representations:
            x_positions = graphical_individual_representation.get_x_position()
            if x_positions is None:
                logger.error(graphical_individual_representation.individual.plain_name + ' has a graphical representation, but was not placed!')
                continue
            for _, x_position in x_positions.items():
                min_x_index = min(min_x_index, x_position[1])
                max_x_index = max(max_x_index, x_position[1])
        if len(self.graphical_individual_representations) == 0:
            min_x_index = 0
            max_x_index = 0
        self.min_x_index = min_x_index  # -1000
        self.max_x_index = max_x_index + 1  # +200

        for graphical_individual_representation in self.graphical_individual_representations:
            birth_date_ov = graphical_individual_representation.get_birth_date_ov()
            if not birth_date_ov:
                continue
            death_event = graphical_individual_representation.get_death_event()

            # individual_id = graphical_individual_representation.individual_id
            individual_name = graphical_individual_representation.name
            # positions[individual_id]

            # individual = self._instances[('i',individual_id)]
            x_pos = graphical_individual_representation.get_x_position()
            if x_pos is None:
                # logger.error(graphical_individual_representation.individual.plain_name + ' has a graphical representation, but was not placed!')
                continue
            x_pos_list = sorted([(ov, pos, index, family_id, flag)
                                 for index, (family_id, (ov, pos, f, flag)) in enumerate(x_pos.items())])
            birth_label = graphical_individual_representation.birth_label
            death_label = graphical_individual_representation.death_label

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
                    if graphical_representation_marriage_family.family_id not in x_pos:
                        logger.error(graphical_representation_marriage_family.family_id + ' has a graphical representation, but was not placed!')
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
                x_pos_list[0][1], birth_date_ov)
            _death_original_location = (
                x_pos_list[-1][1], death_event['ordinal_value'])
            _birth_position = self._map_position(*_birth_original_location)
            _death_position = self._map_position(*_death_original_location)
            knots.append((x_pos_list[0][1], birth_date_ov))
            images = []
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
                            'filename': os.path.join(os.path.dirname(__file__), "ringe.png"),
                            'size': (119,75)
                        }
                    )
                if self._formatting['marriage_label_active']:
                    dy_line = self._inverse_y_position(
                        self._formatting['relative_line_thickness']*self._formatting['vertical_step_size']) - self._inverse_y_position(0)
                    for index2, line in enumerate(label.split('\n')):
                        position = self._map_position(
                            marriage_ring_index, marriage_ordinal + dy_line)
                        position = (position[0], position[1] +
                                    (index2 + 0.2) * font_size * 1.2)
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
                'CubicBezier': CubicBezier
            }

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
                            # ((knots[0][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_date_ov)-_birth_position[1]), (knots[0+1][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_date_ov)-_birth_position[1])),
                            (_birth_position[1], self._map_y_position(
                                self._formatting['fade_individual_color_black_age']*365+birth_date_ov))
                        )
                    )
                    if self._formatting['individual_photo_active'] and len(graphical_individual_representation.individual.images) > 0:
                        index = 0
                        svg_path = Path_types[data[-1][0]
                                              ['type']](*data[-1][0]['arguments'])
                        for ov, image_dict in graphical_individual_representation.individual.images.items():
                            image_filename = image_dict['filename']
                            image_size = image_dict['size']
                            if ov >= knots[index][1] and ov <= knots[index + 1][1]:
                                photo_size = self._formatting['individual_photo_relative_size'] * \
                                    self._formatting['relative_line_thickness'] * \
                                    self._formatting['vertical_step_size']
                                if type(svg_path) == Line:
                                    xpos = svg_path.start.real + \
                                        self._map_y_position(ov)*1j
                                else:
                                    coeffs = svg_path.poly()
                                    coeffs2 = (
                                        coeffs[0].imag, coeffs[1].imag, coeffs[2].imag, coeffs[3].imag - self._map_y_position(ov))
                                    roots = Cardano(*coeffs2)
                                    root = [root.real for root in roots if abs(
                                        root.imag) < 1e-5 and root.real >= 0 and root.real <= 1]
                                    if len(root) > 0:
                                        xpos = svg_path.point(root[0])
                                    else:
                                        xpos = svg_path.point(roots[1])
                                images.append(
                                    {
                                        'type': 'image',
                                        'config': {
                                                'insert': (
                                                    xpos.real - photo_size/2,
                                                    xpos.imag - photo_size/2),
                                                'size': (photo_size, photo_size),
                                        },
                                        'filename': image_filename,
                                        'size': image_size
                                    }
                                )
                else:
                    for index in range(len(knots)-1):
                        def interp(*val):
                            return (knots[index][0]*(1-val[0]) + knots[index+1][0]*val[0],
                                    knots[index][1]*(1-val[1]) + knots[index+1][1]*val[1])
                        if (index + t) % 2 == 0:
                            data.append(
                                ({'type': 'CubicBezier', 'arguments': (
                                    coordinate_transformation(*interp(0, 0)),
                                    coordinate_transformation(
                                        *interp(0, 1)) if self._formatting['family_shape'] == 0 else coordinate_transformation(*interp(0.0, 0.7)),
                                    coordinate_transformation(
                                        *interp(0, 1)) if self._formatting['family_shape'] == 0 else coordinate_transformation(*interp(0.5, 0.9)),
                                    coordinate_transformation(*interp(1, 1)),
                                )},
                                    # ((knots[index][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_date_ov)-_birth_position[1]), (knots[index+1][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_date_ov)-_birth_position[1])),
                                    (_birth_position[1], self._map_y_position(
                                        self._formatting['fade_individual_color_black_age']*365+birth_date_ov))
                                )
                            )
                        else:
                            data.append(
                                ({'type': 'CubicBezier', 'arguments': (
                                    coordinate_transformation(*interp(0, 0)),
                                    coordinate_transformation(
                                        *interp(1, 0)) if self._formatting['family_shape'] == 0 else coordinate_transformation(*interp(0.8, 0)),
                                    coordinate_transformation(
                                        *interp(1, 0)) if self._formatting['family_shape'] == 0 else coordinate_transformation(*interp(1, 0.2)),
                                    coordinate_transformation(*interp(1, 1)),
                                )},
                                    # ((knots[index][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_date_ov)-_birth_position[1]), (knots[index+1][1]-_birth_position[1])/(self._map_y_position(self._formatting['fade_individual_color_black_age']*365+birth_date_ov)-_birth_position[1])),
                                    (_birth_position[1], self._map_y_position(
                                        self._formatting['fade_individual_color_black_age']*365+birth_date_ov))
                                )
                            )
                        if self._formatting['individual_photo_active'] and len(graphical_individual_representation.individual.images) > 0:
                            svg_path = Path_types[data[-1][0]
                                                  ['type']](*data[-1][0]['arguments'])
                            for ov, image_dict in graphical_individual_representation.individual.images.items():
                                image_filename = image_dict['filename']
                                image_size = image_dict['size']
                                if ov > knots[index][1] and ov < knots[index + 1][1]:
                                    photo_size = self._formatting['individual_photo_relative_size'] * \
                                        self._formatting['relative_line_thickness'] * \
                                        self._formatting['vertical_step_size']
                                    if type(svg_path) == Line:
                                        xpos = svg_path.start.real + \
                                            self._map_y_position(ov)*1j
                                    else:
                                        coeffs = svg_path.poly()
                                        coeffs2 = (
                                            coeffs[0].imag, coeffs[1].imag, coeffs[2].imag, coeffs[3].imag - self._map_y_position(ov))
                                        # coeffs2 = (coeffs[0] - self._map_y_position(ov)*1j, coeffs[1], coeffs[2], coeffs[3])
                                        roots = Cardano(*coeffs2)
                                        root = [root.real for root in roots if abs(
                                            root.imag) < 1e-5 and root.real >= 0 and root.real <= 1]
                                        if len(root) > 0:
                                            xpos = svg_path.point(root[0])
                                        else:
                                            xpos = svg_path.point(roots[1])
                                    images.append(
                                        {
                                            'type': 'image',
                                            'config': {
                                                    'insert': (
                                                        xpos.real - photo_size/2,
                                                        xpos.imag - photo_size/2),
                                                    'size': (photo_size, photo_size),
                                            },
                                            'filename': image_filename,
                                            'size': image_size
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
                    birth_label_text = " ".join(individual_name + [birth_label])
                    if self._formatting['birth_label_wrapping_active']:
                        birth_label_text = birth_label_text.strip().replace(' ', '\n')
                    graphical_individual_representation.items.append(
                        {
                            'type': 'text',
                            'config': {
                                'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                                'text': birth_label_text,
                                'text-anchor': self._formatting['birth_label_anchor'],
                                'transform': 'rotate(%s,%s, %s)' % (self._formatting['birth_label_rotation']+self._orientation_angle(*_birth_original_location), *_birth_position),
                                'insert': _birth_position,
                                'dx': [str(font_size*float(self._formatting['birth_label_letter_x_offset']))],
                                'dy': [str(float(font_size)/2.7 + font_size*float(self._formatting['birth_label_letter_y_offset']))+'px'],
                            },
                            'font_size': font_size,
                            'font_name': self._formatting['font_name'],
                        })
            if self._formatting['death_label_active']:
                if self._formatting['death_label_wrapping_active']:
                    death_label = death_label.strip().replace(' ', '\n')
                graphical_individual_representation.items.append(
                    {
                        'type': 'text',
                        'config': {
                            'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                            'text': death_label,
                            'text-anchor': self._formatting['death_label_anchor'],
                            'transform': 'rotate(%g,%s, %s)' % (self._formatting['death_label_rotation']+self._orientation_angle(*_death_original_location), *_death_position),
                            'insert': _death_position,
                            'dy': [str(float(font_size)/2.7 + font_size*float(self._formatting['death_label_letter_y_offset']))+'px'],
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

        import base64

        image_defs = {}
        additional_items = []
        for key, value in self.additional_graphical_items.items():
            additional_items += value
        sorted_individuals = [(gr.get_birth_date_ov(), index, gr)
                              for index, gr in enumerate(self.graphical_individual_representations)]
        sorted_individuals.sort()
        sorted_individual_items = []
        for _, _, graphical_individual_representation in sorted_individuals:
            sorted_individual_items += graphical_individual_representation.items

        for item in additional_items + sorted_individual_items:
                if item['type'] == 'text':
                    if '\n' in item['config']['text']:
                        font_size = item['font_size']
                        if 'dy' in item['config']:
                            dy = float(item['config']['dy'][0][:-2])
                        else:
                            dy = 0
                        for index, line in enumerate([v for v in item['config']['text'].split('\n') if v]):
                            args = deepcopy(item['config'])
                            args['text'] = line
                            args['dy'] = [str(dy + 1.2*index*font_size) + 'px']
                            svg_text = svg_document.text(
                                **args)
                            svg_document.add(svg_text)
                    else:
                        args = item['config']
                        svg_text = svg_document.text(
                            **args)
                        svg_document.add(svg_text)
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
                    key = 'image_' + str(width) + '_' + \
                        str(height) + item['filename']
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
                        this_def['size'] = item['size']
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
