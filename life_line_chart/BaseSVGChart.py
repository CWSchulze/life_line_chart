import os
import logging
import datetime
import svgwrite
from copy import deepcopy
from collections import defaultdict
from math import floor, ceil, pi, e

from .SimpleSVGItems import Line, Path, CubicBezier
from .Exceptions import LifeLineChartCannotMoveIndividual, LifeLineChartCollisionDetected
from .BaseChart import BaseChart
from .IntermediateGraphicalItems import new_text_item, new_image_item, new_path_item

logger = logging.getLogger("life_line_chart")

cardano_instance = None


class Cardano:
    """
    Cardano Singleton
    """
    J = None
    Jc = None
    def __init__(self):
        self.J = e**(2j*pi/3)
        self.Jc = 1/self.J

    def solve(self, a, b, c, d):
        z0 = b/3/a
        a2, b2 = a*a, b*b
        p = -b2/3/a2 + c/a
        q = (b/27*(2*b2/a2-9*c/a)+d)/a
        D = -4*p*p*p-27*q*q
        r = (-D/27+0j)**0.5
        u = ((-q-r)/2)**0.33333333333333333333333
        v = ((-q+r)/2)**0.33333333333333333333333
        w = u*v
        w0 = abs(w+p/3)
        w1 = abs(w*self.J+p/3)
        w2 = abs(w*self.Jc+p/3)
        if w0 < w1:
            if w2 < w0:
                v *= self.Jc
        elif w2 < w1:
            v *= self.Jc
        else:
            v *= self.J
        return u+v-z0, u*self.J+v*self.Jc-z0, u*self.Jc+v*self.J-z0

def cardano(a,b,c,d):
    """
    Use cardano class with singleton.

    Args:
        a (float): a
        b (float): b
        c (float): c
        d (float): d

    Returns:
        list: list of roots
    """
    global cardano_instance
    if cardano_instance == None:
        cardano_instance = Cardano()
    return cardano_instance.solve(a,b,c,d)

def intersection_polynomial(coeffs, y_pos):
    """
    calculate the intersection of the polynomial

    Args:
        coeffs (list): List of coefficients for polynomial. I don't remember the order.
        y_pos (float): y_position in the chart

    Returns:
        float: relative root position
    """
    coeffs2 = (
        coeffs[0].imag, coeffs[1].imag, coeffs[2].imag, coeffs[3].imag - y_pos)
    roots = cardano(*coeffs2)
    root = [root.real for root in roots if abs(
        root.imag) < 1e-5 and root.real >= 0 and root.real <= 1]
    if len(root) > 0:
        return root[0]
    else:
        return roots[1]


class BaseSVGChart(BaseChart):
    """
    Base SVG Chart
    ==============

    Class which provides basic methods to generate and handle svg items and save the file.
    """

    def __init__(self, positioning=None, formatting=None, instance_container=None):
        BaseChart.__init__(self, positioning, formatting, instance_container)

    def check_unique_x_position(self, always_has_child_of_family=True):
        """
        Check if every individual position has a unique horizontal slot.

        Raises:
            RuntimeError: overlap was found

        Returns:
            tuple: (list of failures, min_x_index, max_x_index)
        """
        failed = []
        v = {}
        for gr_individual in self.gr_individuals:
            x_pos = gr_individual.get_position_dict()
            x_index = None
            for value in x_pos.values():

                if x_index == value[1]:
                    # ignore if x doesnt change
                    continue
                x_index = value[1]

                if x_index not in v:
                    v[x_index] = gr_individual.individual_id
                elif (always_has_child_of_family or v[x_index] != gr_individual.individual_id):
                    failed.append(x_index)
                    # value = index_map[x_index]
                    logger.error(
                        "check_unique_x_position failed, index was used more than once: " + str((x_index, value[2].family_id, gr_individual.individual.plain_name, v[x_index])))
                    # raise RuntimeError((x_index, key, gr_individual.individual.plain_name))
        full_index_list = list(sorted(v.keys()))
        for i in range(max(full_index_list)):
            if i not in full_index_list:
                if self._formatting['debug_visualize_ambiguous_placement']:
                    gr_individual.items.append(((99, 'layer_debug'),{
                        'type': 'rect',
                        'config': {
                            'insert': (self._map_x_position(i), 0),
                            'size': (self._formatting['relative_line_thickness']*self._formatting['horizontal_step_size'], self._formatting['total_height']),
                            'fill': 'black',
                            'fill-opacity': "0.5"
                        }
                    }))
                failed.append(('missing', i))
        return failed, full_index_list[0], full_index_list[-1]

    def clear_graphical_representations(self):
        """
        Clear all graphical representations to rebuild the chart.
        """
        self.min_x_index = 0
        self.max_x_index = 0
        self.clear_svg_items()
        self._instances.ancestor_width_cache.clear()
        BaseChart.clear_graphical_representations(self)

    def define_svg_items(self):
        """
        Generate graphical item information used for rendering the image.
        """
        logger.debug('start creating graphical items')

        self.additional_graphical_items.clear()

        line_thickness = self._formatting['relative_line_thickness'] * \
            self._formatting['horizontal_step_size']
        font_size = self._formatting['font_size_description'] * line_thickness

        if len(self.gr_individuals) == 0:
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
                self.additional_graphical_items['grid'].append(
                    new_path_item(
                        self, 'Line',
                        (0 + year_pos*1j, self.get_full_width() + year_pos*1j),
                        self._colors['grid_line'], 1
                    )
                )
                self.additional_graphical_items['axis'].append(
                    new_text_item(
                        self=self,
                        text=str(year),
                        pos_x=self.get_full_width() - self._formatting['horizontal_step_size']*0.01,
                        pos_y=year_pos,
                        text_anchor='end',
                    )
                )
            else:
                # add thin line
                self.additional_graphical_items['grid'].append(
                    new_path_item(
                        self, 'Line',
                        (0 + year_pos*1j, self.get_full_width() + year_pos*1j),
                        self._colors['grid_line'], 0.1
                    )
                )

        min_x_index = 9e99
        max_x_index = -9e99
        for gr_individual in self.gr_individuals:
            x_positions = gr_individual.get_position_dict()
            if x_positions is None:
                logger.error(gr_individual.individual.plain_name + ' has a graphical representation, but was not placed!')
                continue
            for _, x_position in x_positions.items():
                min_x_index = min(min_x_index, x_position[1])
                max_x_index = max(max_x_index, x_position[1])
        if len(self.gr_individuals) == 0:
            min_x_index = 0
            max_x_index = 0
        self.min_x_index = min_x_index  # -1000
        self.max_x_index = max_x_index + 1  # +200

        cactus_chart = (str(type(self)) == "<class 'life_line_chart.DescendantChart.DescendantChart'>" and self._positioning['chart_layout'] == 'cactus')
        line_bend_orientation = 0 if cactus_chart else 1

        for gr_individual in self.gr_individuals:
            debug_items = []
            birth_date_ov = gr_individual.birth_date_ov
            if not birth_date_ov:
                continue
            death_event = gr_individual.get_death_event()
            individual_name = gr_individual.get_name()

            x_pos = gr_individual.get_position_dict()
            if x_pos is None:
                # logger.error(gr_individual.individual.plain_name + ' has a graphical representation, but was not placed!')
                continue
            x_pos_list = list(x_pos.values())
            birth_label = gr_individual.birth_label
            death_label = gr_individual.death_label

            # collect information about marriages
            marriage_ordinals = []
            marriage_ring_positions = []
            marriage_families = []
            # ring is only added to one spouse
            marriage_has_ring = []
            marriage_is_crossconnected = []
            new_x_indices_after_marriage = []
            marriage_labels = []

            def coordinate_transformation(x, y):
                new_x, new_y = self._map_position(x, y)
                return new_x + new_y*1j
            def calculate_ring_position(gr_family):
                h_pos = gr_family.gr_husb.get_position_dict(gr_family) if gr_family.gr_husb else None
                w_pos = gr_family.gr_wife.get_position_dict(gr_family) if gr_family.gr_wife else None
                if (str(type(self)) == "<class 'life_line_chart.DescendantChart.DescendantChart'>" and self._positioning['chart_layout'] == 'cactus'):
                    if h_pos and not w_pos:
                        return (h_pos[1],
                            gr_family.marriage['ordinal_value'])
                    if w_pos and not h_pos:
                        return (w_pos[1],
                            gr_family.marriage['ordinal_value'])
                if h_pos is None or w_pos is None:
                    vcs = gr_family.visible_children
                    if vcs:
                        vcs_pos = [vc.get_position_dict(gr_family)[1] for vc in vcs]
                        return (
                                sum(vcs_pos)/len(vcs_pos),
                                gr_family.marriage['ordinal_value'])
                else:
                    return (
                            (h_pos[1] + w_pos[1])/2,
                            gr_family.marriage['ordinal_value'])
                return None
            gr_cof = gr_individual.connected_parent_families[0] if gr_individual.connected_parent_families else None
            gr_most_recently_handled_family = gr_cof
            for gr_marriage_family in gr_individual.visible_marriages:
                if gr_marriage_family.marriage is None:
                    logger.warning("Found family without marriage date. The family should not have been instantiated")
                    continue
                if gr_marriage_family.g_id not in x_pos:
                    # Maybe not an error. This might also happen, if the first and second marriage of one person
                    # reunite in later generations. If the number of the generations is not the same, then one
                    # marriage might be added, while the other is not (due to max generations)
                    # logger.error(gr_marriage_family.family_id + ' has a graphical representation, but was not placed!')
                    continue

                ring_pos = calculate_ring_position(gr_marriage_family)
                if ring_pos is None:
                    continue

                marriage_is_crossconnected.append(gr_individual.is_cross_connection(gr_marriage_family, gr_most_recently_handled_family))
                gr_most_recently_handled_family = gr_marriage_family

                gr_spouse = gr_marriage_family.get_gr_spouse(
                    gr_individual)
                marriage_x_index = x_pos[gr_marriage_family.g_id][1]
                new_x_indices_after_marriage.append(marriage_x_index)

                marriage_ring_positions.append(ring_pos)

                marriage_families.append(gr_marriage_family)
                marriage_has_ring.append(gr_marriage_family.gr_husb == gr_individual or gr_marriage_family.gr_husb is None)
                marriage_ordinals.append(
                    gr_marriage_family.marriage['ordinal_value'])
                marriage_labels.append(
                    str(gr_marriage_family.marriage_label))


            if self._formatting['debug_visualize_connections']:
                # show items to help debugging the algorithms
                individual_connections = self._instances.connection_container['i'][gr_individual.g_id]
                for f_g_id, connections in individual_connections.items():
                    marriage_ring_index, marriage_ordinal = calculate_ring_position(self._instances[('f',f_g_id[1])].graphical_representations[f_g_id[0]])
                    for connection in connections:
                        if connection == 'weak_child':
                            thickness = 0.5*self._formatting['horizontal_step_size']*0.1
                            color = (175, 225, 175)
                        elif connection == 'strong_child':
                            thickness = 0.5*self._formatting['horizontal_step_size']*0.3
                            color = (25, 25, 25)
                        elif connection == 'gr_wife':
                            thickness = 0.5*self._formatting['horizontal_step_size']*0.2
                            color = (225, 25, 25)
                        elif connection == 'gr_husb':
                            thickness = 0.5*self._formatting['horizontal_step_size']*0.2
                            color = (25, 25, 225)
                        elif connection == 'strong_marriage':
                            thickness = 0.5*self._formatting['horizontal_step_size']*0.3
                            color = (25, 225, 25)
                        else:
                            thickness = 0.5*self._formatting['horizontal_step_size']*1
                            color = (25, 25, 25)
                        l_i = gr_individual
                        x_p_list = list(l_i.get_position_dict().values())
                        x_p = x_p_list[0][1]
                        new_marriage_ordinal = marriage_ordinal
                        if x_p == marriage_ring_index:
                            if l_i.birth_date_ov > marriage_ordinal:
                                new_marriage_ordinal = min(l_i.birth_date_ov-5*365, marriage_ordinal)
                            else:
                                new_marriage_ordinal = max(l_i.birth_date_ov, marriage_ordinal+5*365)
                        debug_items.append((
                            (99, 'layer_debug'),
                            new_path_item(
                                self, 'Line',
                                points=[coordinate_transformation(
                                            marriage_ring_index, new_marriage_ordinal),
                                        coordinate_transformation(
                                            x_p, l_i.birth_date_ov)],
                                color=color, stroke_width=thickness
                            )
                        ))

            # generate event node information
            knots = []
            _birth_original_location = (
                x_pos_list[0][1], birth_date_ov)
            _death_original_location = (
                x_pos_list[-1][1], death_event['ordinal_value'])
            _birth_position = self._map_position(*_birth_original_location)
            _death_position = self._map_position(*_death_original_location)
            knots.append((x_pos_list[0][1], birth_date_ov, None))
            for index, ((marriage_ring_index, marriage_ordinal), new_x_index_after_marriage, label, gr_family, has_ring, is_cross_connected) in enumerate(zip(marriage_ring_positions, new_x_indices_after_marriage, marriage_labels, marriage_families, marriage_has_ring, marriage_is_crossconnected)):
                if cactus_chart:
                    spouse_index =  (new_x_index_after_marriage-marriage_ring_index)*(-1) + marriage_ring_index
                    marriage_ring_index = new_x_index_after_marriage
                    if spouse_index != marriage_ring_index:
                        stroke_width = line_thickness*0.1
                        if has_ring:
                            gr_individual.items.append((
                                (0, 'layer_marriage_connections'),
                                new_path_item(
                                    self, 'Line',
                                    (coordinate_transformation(
                                        spouse_index, marriage_ordinal),
                                    coordinate_transformation(
                                        marriage_ring_index, marriage_ordinal)),
                                    self._colors['descendant_chart_marriage_lines'],
                                    stroke_width,
                                    stroke_dasharray=f"{stroke_width*5},{stroke_width*5}",
                                )
                            ))
                        has_ring = True
                if not self._formatting['no_ring'] and has_ring:
                    ring_position = self._map_position(
                        marriage_ring_index, marriage_ordinal)
                    gr_individual.items.append((
                        (2, 'layer_ring_image'),
                        new_image_item(
                            self=self,
                            pos_x = ring_position[0] - line_thickness*1,
                            pos_y = ring_position[1] - line_thickness*1,
                            size_x = line_thickness*2,
                            size_y = line_thickness*2,
                            filename = os.path.join(os.path.dirname(__file__), "ringe.png"),
                            original_size = (119,75),
                            gir = gr_individual,
                            gfr = gr_family
                        )
                    ))
                if self._formatting['marriage_label_active']:
                    dy_line = self._inverse_y_position(
                        line_thickness) - self._inverse_y_position(0)
                    for index2, line in enumerate(label.split('\n')):
                        position = self._map_position(
                            marriage_ring_index, marriage_ordinal + dy_line)
                        gr_individual.items.append((
                            (5, 'layer_marriage_label'),
                            new_text_item(
                                self=self,
                                text=line,
                                pos_x=position[0],
                                pos_y=position[1] + (index2 + 0.2)*font_size*1.2,
                            )
                        ))

                if cactus_chart:
                    if index == 0:
                        knots.append((new_x_index_after_marriage, marriage_ordinal, False))
                else:
                    knots.append((marriage_ring_index, marriage_ordinal, is_cross_connected))
                    if index + 1 < len(marriage_ordinals):
                        # zwischenpunkt zur ursprungsposition
                        knots.append(
                            (new_x_index_after_marriage, marriage_ordinals[index]/2+marriage_ordinals[index+1]/2, False))
            knots.append((x_pos_list[-1][1], death_event['ordinal_value'], False))

            Path_types = {
                'Line': Line,
                'CubicBezier': CubicBezier
            }

            # generate spline paths
            def marriage_bezier(data, knots, flip=False):
                """
                Tranlate event information to bezier splines.

                Args:
                    data (list): data container to place the data
                    knots (list): list of event nodes
                    flip (bool, optional): flip shape of the spline. Defaults to False.
                """
                if flip:
                    t = 1
                else:
                    t = 0

                if self._formatting['individual_photo_active'] and len(gr_individual.individual.images) > 0:
                    photo_dict = self.get_filtered_photos(birth_date_ov, gr_individual.individual.images)

                if len(knots) == 2 and ('chart_layout' not in self._positioning or self._positioning['chart_layout'] != 'cactus'):
                    data.append(
                        ({'type': 'Line', 'arguments': (
                            coordinate_transformation(
                                knots[0][0], knots[0][1]),
                            coordinate_transformation(
                                knots[0+1][0], knots[0+1][1]),
                        )},
                            (_birth_position[1], self._map_y_position(
                                self._formatting['fade_individual_color_black_age']*365+birth_date_ov)),
                        False # not cross connected
                        )
                    )
                    if self._formatting['individual_photo_active'] and len(gr_individual.individual.images) > 0:
                        index = 0
                        svg_path = Path_types[data[-1][0]
                                              ['type']](*data[-1][0]['arguments'])
                        for ov, image_dict in photo_dict.items():
                            image_filename = image_dict['filename']
                            image_size = image_dict['size']
                            if ov >= knots[index][1] and ov <= knots[index + 1][1]:
                                photo_size = self._formatting['individual_photo_relative_size'] * \
                                    line_thickness
                                if type(svg_path) == Line:
                                    xpos = svg_path.start.real + \
                                        self._map_y_position(ov)*1j
                                else:
                                    coeffs = svg_path.poly()
                                    root = intersection_polynomial(coeffs, self._map_y_position(ov))
                                    xpos = svg_path.point(root)

                                gr_individual.items.append((
                                    (4, 'layer_photos'),
                                    new_image_item(
                                        self=self,
                                        pos_x = xpos.real - photo_size/2,
                                        pos_y = xpos.imag - photo_size/2,
                                        size_x = photo_size,
                                        size_y = photo_size,
                                        filename = image_filename,
                                        original_size = image_size
                                    )
                                ))
                else:
                    # self._formatting['family_shape'] = 2
                    for index in range(len(knots)-1):
                        def interp(*val):
                            if (index + t) % 2 == line_bend_orientation:
                                val = [val[1], val[0]]
                            return (knots[index][0]*(1-val[0]) + knots[index+1][0]*val[0],
                                    knots[index][1]*(1-val[1]) + knots[index+1][1]*val[1])
                        def interp_trans(*val):
                            return coordinate_transformation(*interp(*val))
                        if self._formatting['family_shape'] == 0:
                            relative_spline_handles = [(0, 0), (0, 1), (0, 1), (1, 1)]
                        elif self._formatting['family_shape'] == 1:
                            relative_spline_handles = [(0, 0), (0, 0.7), (0.5, 0.9), (1, 1)]
                        else:#if self._formatting['family_shape'] == 2:
                            relative_spline_handles = [(0, 0), (0.1, 0.3), (0.3, 1), (1, 1)]

                        data.append(
                            ({'type': 'CubicBezier', 'arguments': (
                                interp_trans(*relative_spline_handles[0]),
                                interp_trans(*relative_spline_handles[1]),
                                interp_trans(*relative_spline_handles[2]),
                                interp_trans(*relative_spline_handles[3]),
                            )},
                                (_birth_position[1], self._map_y_position(
                                    self._formatting['fade_individual_color_black_age']*365+birth_date_ov)),
                            # connection to this knot is relevant
                            knots[index+1][2]# and index + 1 < len(knots) or knots[index + 1][2]
                            )
                        )

                        if self._formatting['individual_photo_active'] and len(gr_individual.individual.images) > 0:
                            svg_path = Path_types[data[-1][0]
                                                  ['type']](*data[-1][0]['arguments'])
                            for ov, image_dict in photo_dict.items():
                                image_filename = image_dict['filename']
                                image_size = image_dict['size']
                                if ov > knots[index][1] and ov < knots[index + 1][1]:
                                    photo_size = self._formatting['individual_photo_relative_size'] * \
                                        line_thickness
                                    if type(svg_path) == Line:
                                        xpos = svg_path.start.real + \
                                            self._map_y_position(ov)*1j
                                    else:
                                        coeffs = svg_path.poly()
                                        root = intersection_polynomial(coeffs, self._map_y_position(ov))
                                        xpos = svg_path.point(root)
                                    gr_individual.items.append((
                                        (4, 'layer_photos'),
                                        new_image_item(
                                            self=self,
                                            pos_x = xpos.real - photo_size/2,
                                            pos_y = xpos.imag - photo_size/2,
                                            size_x = photo_size,
                                            size_y = photo_size,
                                            filename = image_filename,
                                            original_size = image_size
                                        )
                                    ))
            life_line_bezier_paths = []
            marriage_bezier(life_line_bezier_paths, knots)

            # create item setup
            for path, color_pos, is_cross_connection in life_line_bezier_paths:
                if True:
                    priority = 0 if is_cross_connection else 1
                else:
                    priority = 3 if is_cross_connection else 0
                gr_individual.items.append(((priority, 'layer_life_lines'),{
                    'type': 'path',
                    'config': path,
                    'color': gr_individual.color,
                    'color_pos': color_pos,
                    'stroke_width': line_thickness*gr_individual.weight,
                    'gir':gr_individual
                }))
            if self._formatting['birth_label_active']:
                if self._formatting['birth_label_along_path']:
                    gr_individual.items.append((
                        (5, 'layer_birth_label'),
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
                        }))
                else:
                    birth_label_text = " ".join(individual_name + [birth_label])
                    if self._formatting['birth_label_wrapping_active']:
                        birth_label_text = birth_label_text.strip().replace(' ', '\n')
                    gr_individual.items.append((
                        (5, 'layer_birth_label'),
                        new_text_item(
                            self=self,
                            text=birth_label_text,
                            pos_x=_birth_position[0],
                            pos_y=_birth_position[1],
                            text_anchor=self._formatting['birth_label_anchor'],
                            transform=
                                'rotate(%s,%s, %s)' % (self._formatting['birth_label_rotation']+self._orientation_angle(*_birth_original_location), *_birth_position)
                                if self._formatting['birth_label_rotation'] != 0 else None,
                            insert=_birth_position,
                            dx=[str(font_size*float(self._formatting['birth_label_letter_x_offset']))],
                            dy=[str(float(font_size)/2.7 + font_size*float(self._formatting['birth_label_letter_y_offset']))+'px'],
                        )
                    ))
            if self._formatting['death_label_active']:
                if self._formatting['death_label_wrapping_active']:
                    death_label = death_label.strip().replace(' ', '\n')
                gr_individual.items.append((
                    (5, 'layer_death_label'),
                    new_text_item(
                        self=self,
                        text=death_label,
                        pos_x=_death_position[0],
                        pos_y=_death_position[1],
                        text_anchor=self._formatting['death_label_anchor'],
                        transform=
                            'rotate(%g,%s, %s)' % (self._formatting['death_label_rotation']+self._orientation_angle(*_death_original_location), *_death_position)
                            if self._formatting['death_label_rotation'] != 0 else None,
                        dy=[str(float(font_size)/2.7 + font_size*float(self._formatting['death_label_letter_y_offset']))+'px'],
                        dx=[str(font_size*float(self._formatting['death_label_letter_x_offset']))],
                    )
                ))
            gr_individual.items += debug_items
        if self._formatting['debug_visualize_connections']:
            for gr_family in self.gr_families:
                # show items to help debugging the algorithms
                gr_spouse = None
                if gr_family.gr_husb:
                    gr_spouse = gr_family.gr_husb
                elif gr_family.gr_wife:
                    gr_spouse = gr_family.gr_wife
                if gr_spouse:
                    individual_connections = self._instances.connection_container['f'][gr_family.g_id]
                    for f_g_id, connections in individual_connections.items():
                        for connection in connections:
                            if connection == 'gr_strong_parent_family':
                                thickness = 0.5*self._formatting['horizontal_step_size']*0.3
                                color = (175, 225, 255)
                            else:
                                continue
                                thickness = 0.5*self._formatting['horizontal_step_size']*1
                                color = (25, 25, 25)
                            gr_other_family = self._instances[('f',f_g_id[1])].graphical_representations[f_g_id[0]]
                            if gr_other_family is None:
                                continue
                            marriage_pos_a = calculate_ring_position(gr_family)
                            marriage_pos_b = calculate_ring_position(gr_other_family)
                            if marriage_pos_b is None:
                                continue

                            gr_spouse.items.append((
                                (99, 'layer_debug'),
                                new_path_item(
                                    self, 'Line',
                                    points=[coordinate_transformation(*marriage_pos_a),
                                            coordinate_transformation(*marriage_pos_b)],
                                    color=color, stroke_width=thickness
                                )
                            ))


    def paint_and_save(self, filename):
        """
        Setup svg file and save it.

        Args:
            filename (str): user defined filename.
        """

        logger.debug('start creating document')

        svgwrite.utils.AutoID._nextid = 1
        svg_document = svgwrite.Drawing(filename=filename,
                                        debug=False,
                                        size=(
                                            str(self.get_full_width()),
                                            str(self.get_full_height())))

        import base64

        image_defs = {}
        additional_items = []
        for key, value in self.additional_graphical_items.items():
            additional_items += value
        sorted_individuals = [(gr.birth_date_ov, index, gr)
                              for index, gr in enumerate(self.gr_individuals)]
        sorted_individuals.sort()
        sorted_individual_dict = defaultdict(list)
        for _, _, gr_individual in sorted_individuals:
            for key, item in gr_individual.items:
                sorted_individual_dict[key].append(item)
        sorted_individual_flat_item_list = []
        for key in sorted(sorted_individual_dict.keys()):
            sorted_individual_flat_item_list += sorted_individual_dict[key]

        for item in additional_items + sorted_individual_flat_item_list:
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
                    stroke_dasharray = None
                    if 'stroke_dasharray' in item:
                        stroke_dasharray = item['stroke_dasharray']
                    svg_path = Path(constructor_function(*arguments))

                    if self._formatting['fade_individual_color'] and 'color_pos' in item:
                        fill = svg_document.linearGradient(("0", str(
                            item['color_pos'][0])+""), ("0", str(item['color_pos'][1])+""), gradientUnits='userSpaceOnUse')
                        fill.add_stop_color(
                            0, "rgb({},{},{})".format(*item['color']))
                        fill.add_stop_color(1, "rgb({},{},{})".format(*self._colors['fade_to_death']))
                        # fill.add_stop_color(0, "rgb({},{},{})".format(*item['colors'][1]))
                        # fill.add_stop_color(1, "rgb({},{},{})".format(*item['colors'][0]))
                        svg_document.defs.add(fill)
                        svg_document.add(svg_document.path(d=svg_path.d(), stroke=fill.get_paint_server(
                            default='currentColor'), fill='none', stroke_width=item['stroke_width'], stroke_dasharray=stroke_dasharray))
                    else:
                        # arguments['fill'] = fill
                        # gr_individual.color
                        svg_document.add(svg_document.path(d=svg_path.d(), stroke="rgb({},{},{})".format(
                            *item['color']), fill='none', stroke_width=item['stroke_width'], stroke_dasharray=stroke_dasharray))
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
