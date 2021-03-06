from life_line_chart import AncestorChart, DescendantChart
from life_line_chart.GedcomInstanceContainer import get_gedcom_instance_container
import pytest
from collections import OrderedDict
import os
try:
    from PIL import Image
    pillow_available = True
except ImportError:
    pillow_available = False


def test_generate_svg_file():
    max_generations = 20
    x_position = 0

    # select individual to show
    gedcom_data = open(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged'),
        'r').read()
    last_individual_pos = gedcom_data.rfind('\n0 @I')
    last_individual_pos = gedcom_data.rfind(' FAMC ', 0, last_individual_pos)
    last_individual_pos = gedcom_data.rfind('\n0 @I', 0, last_individual_pos)
    individual_id = gedcom_data[
        last_individual_pos + 3:gedcom_data.find(' INDI', last_individual_pos+1)]

    chart = AncestorChart(instance_container=get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged')))
    chart.select_individuals(
        chart._instances[('i', individual_id)], generations=max_generations)

    root_individual = chart._instances[('i', individual_id)]
    gr_root_individual = root_individual.graphical_representations[0]
    cof_ids = root_individual.child_of_family_id
    child_of_family = None
    if cof_ids:
        child_of_family = chart._instances[('f', cof_ids[0])]
    chart.place_selected_individuals(
        gr_root_individual, None, child_of_family.graphical_representations[0], x_position)
    x_min, x_max = gr_root_individual.get_ancestor_range(None)
    x_position += x_max - x_min + 1

    chart.modify_layout(individual_id)

    chart.define_svg_items()
    chart.paint_and_save(os.path.join(
        os.path.dirname(__file__), 'output', 'test_svg.svg'))


def test_generate_svg_file_with_two_roots():
    max_generations = 20
    x_position = 0
    last_individual_pos = None
    chart = AncestorChart(instance_container=get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged')))

    # select individual to show
    gedcom_data = open(os.path.join(os.path.dirname(
        __file__), 'autogenerated.ged'), 'r').read()
    last_individual_pos = gedcom_data.rfind(' FAMC ', 0, last_individual_pos)
    last_individual_pos = gedcom_data.rfind('\n0 @I', 0, last_individual_pos)
    individual_id = gedcom_data[last_individual_pos +
                                3:gedcom_data.find(' INDI', last_individual_pos+1)]

    chart.select_individuals(
        chart._instances[('i', individual_id)], generations=max_generations)

    root_individual = chart._instances[('i', individual_id)]
    gr_root_individual = root_individual.graphical_representations[0]
    cof_ids = root_individual.child_of_family_id
    child_of_family = None
    if cof_ids:
        child_of_family = chart._instances[('f', cof_ids[0])]
    #chart.modify_layout(individual_id)

    # select individual to show
    # gedcom_data = open(os.path.join(os.path.dirname(__file__), 'autogenerated.ged'),'r').read()
    last_individual_pos = gedcom_data.rfind(
        ' FAMC ', 0, last_individual_pos-int(len(gedcom_data)*0.2))
    last_individual_pos = gedcom_data.rfind(' FAMC ', 0, last_individual_pos)
    last_individual_pos = gedcom_data.rfind('\n0 @I', 0, last_individual_pos)
    second_individual_id = gedcom_data[last_individual_pos +
                                3:gedcom_data.find(' INDI', last_individual_pos+1)]

    chart.select_individuals(
        chart._instances[('i', second_individual_id)], generations=max_generations)

    chart.place_selected_individuals(
        gr_root_individual, None, child_of_family.graphical_representations[0], x_position)
    x_min, x_max = gr_root_individual.get_ancestor_range(None)
    x_position += x_max - x_min + 1

    second_root_individual = chart._instances[('i', second_individual_id)]
    gr_second_root_individual = second_root_individual.graphical_representations[0]
    cof_ids = second_root_individual.child_of_family_id
    child_of_family = None
    if cof_ids:
        child_of_family = chart._instances[('f', cof_ids[0])]
    chart.place_selected_individuals(
        gr_second_root_individual, None, child_of_family.graphical_representations[0], x_position)
    x_min, x_max = gr_second_root_individual.get_ancestor_range(None)
    x_position += x_max - x_min + 1

    chart.define_svg_items()
    chart.paint_and_save(os.path.join(
        os.path.dirname(__file__), 'output', 'test_svg_two_roots.svg'))


def test_generate_svg_file_ancestor_and_children():
    max_generations = 20
    x_position = 0
    last_individual_pos = None
    chart = AncestorChart(instance_container=get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged')))

    # select individual to show
    gedcom_data = open(os.path.join(os.path.dirname(
        __file__), 'autogenerated.ged'), 'r').read()
    last_individual_pos = gedcom_data.rfind(' FAMC ', 0, last_individual_pos)
    last_individual_pos = gedcom_data.rfind('\n0 @I', 0, last_individual_pos)
    individual_id = gedcom_data[last_individual_pos +
                                3:gedcom_data.find(' INDI', last_individual_pos+1)]

    chart.select_individuals(
        chart._instances[('i', individual_id)], generations=max_generations)

    individual2_id = individual_id
    i = 0
    while i < 4:
        for cof in chart._instances[('i', individual2_id)].child_of_families:
            if cof.husb.has_graphical_representation():
                if cof.husb.child_of_families:
                    individual2_id = cof.husb.individual_id
                    break
            if cof.wife.has_graphical_representation():
                if cof.wife.child_of_families:
                    individual2_id = cof.wife.individual_id
                    break
        chart.select_family_children(
            chart._instances[('f', cof.family_id)].graphical_representations[0])
        i += 1

    root_individual = chart._instances[('i', individual_id)]
    gr_root_individual = root_individual.graphical_representations[0]
    cof_ids = root_individual.child_of_family_id
    child_of_family = None
    if cof_ids:
        child_of_family = chart._instances[('f', cof_ids[0])]
    chart.place_selected_individuals(
        gr_root_individual, None, child_of_family.graphical_representations[0], x_position)
    x_min, x_max = chart._instances[('i', individual_id)
                             ].graphical_representations[0].get_ancestor_range(None)
    x_position += x_max - x_min + 1

    chart.define_svg_items()
    chart.paint_and_save(os.path.join(
        os.path.dirname(__file__), 'output', 'test_svg_ancestor_and_children.svg'))


@pytest.mark.skipif(not pillow_available, reason="only makes sense with pillow")
def test_photos_in_chart():
    max_generations = 3
    x_position = 0
    chart = AncestorChart(instance_container=get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged')),
        formatting={
            'relative_line_thickness': 0.7,
            'horizontal_step_size': 50,
            'total_height': 3000,
            'individual_photo_relative_size': 1.5,
            'individual_photo_active':True})

    individual_id = '@I106@'

    chart.select_individuals(
        chart._instances[('i', individual_id)], generations=max_generations)

    images = OrderedDict()
    import re
    import datetime
    expr = re.compile(r'individual_I6_image_age_(\d+)\.png')
    image_step_size = 365*4.0
    birth_ordinal_value = chart._instances[(
        'i', individual_id)].events['birth_or_christening']['ordinal_value']
    sorted_list = []
    for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'images')):
        match = expr.match(filename)
        if match:
            year = int(match.group(1)) + 1245
            month = 1
            day = 1
            # elif match.group(3) is None::
            #     month = max(1, int(match.group(3)))
            ordinal_value = datetime.date(year, month, day).toordinal()
            sorted_list.append((ordinal_value, year, filename))
    sorted_list.sort()
    for ordinal_value, year, filename in sorted_list:
        if len(images) > 0:
            max_ordinal = max(list(images.keys()))
        else:
            max_ordinal = -1
        if round((ordinal_value-birth_ordinal_value)/image_step_size) > round((max_ordinal-birth_ordinal_value)/image_step_size):
            images[birth_ordinal_value + round((ordinal_value-birth_ordinal_value)/image_step_size)
                    * image_step_size] = {
                        'filename': os.path.join(os.path.dirname(__file__), 'images', filename),
                        'size': Image.open(os.path.join(os.path.dirname(__file__), 'images', filename)).size
                    }

    chart._instances[('i', individual_id)].images.update(images)
    chart._instances[('i', '@I98@')].images.update(images)

    root_individual = chart._instances[('i', individual_id)]
    gr_root_individual = root_individual.graphical_representations[0]
    cof_ids = root_individual.child_of_family_id
    child_of_family = None
    if cof_ids:
        child_of_family = chart._instances[('f', cof_ids[0])]
    chart.place_selected_individuals(
        gr_root_individual, None, child_of_family.graphical_representations[0], x_position)
    x_min, x_max = chart._instances[('i', individual_id)
                             ].graphical_representations[0].get_ancestor_range(None)
    x_position += x_max - x_min + 1
    chart.modify_layout(individual_id)

    chart.define_svg_items()
    chart.paint_and_save(os.path.join(
        os.path.dirname(__file__), 'output', 'test_svg_photos.svg'))


@pytest.mark.skipif(not pillow_available, reason="only makes sense with pillow")
def test_photos_in_chart_selection():
    max_generations = 3
    x_position = 0
    chart = AncestorChart(instance_container=get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged')),
        formatting={
            'relative_line_thickness': 0.7,
            'horizontal_step_size': 50,
            'total_height': 1000,
            'individual_photo_relative_size': 1.5,
            'individual_photo_active':True})

    individual_id = '@I106@'

    chart.select_individuals(
        chart._instances[('i', individual_id)], generations=max_generations)

    images = OrderedDict()
    import re
    import datetime
    expr = re.compile(r'individual_I6_image_age_(\d+)\.png')
    birth_ordinal_value = chart._instances[(
        'i', individual_id)].events['birth_or_christening']['ordinal_value']
    sorted_list = []
    original_images = OrderedDict()
    for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'images')):
        match = expr.match(filename)
        if match:
            year = int(match.group(1)) + 1245
            month = 1
            day = 1
            # elif match.group(3) is None::
            #     month = max(1, int(match.group(3)))
            ordinal_value = datetime.date(year, month, day).toordinal()
            sorted_list.append((ordinal_value, year, filename))
            original_images[ordinal_value] = {
                            'filename': os.path.join(os.path.dirname(__file__), 'images', filename),
                            'size': Image.open(os.path.join(os.path.dirname(__file__), 'images', filename)).size
                        }
    sorted_list.sort()

    root_individual = chart._instances[('i', individual_id)]
    gr_root_individual = root_individual.graphical_representations[0]
    cof_ids = root_individual.child_of_family_id
    child_of_family = None
    if cof_ids:
        child_of_family = chart._instances[('f', cof_ids[0])]
    chart.place_selected_individuals(
        gr_root_individual, None, child_of_family.graphical_representations[0], x_position)
    x_min, x_max = chart._instances[('i', individual_id)
                             ].graphical_representations[0].get_ancestor_range(None)
    x_position += x_max - x_min + 1
    chart.modify_layout(individual_id)

    chart.define_svg_items()


    def get_filtered_photos(self, original_images):
        images = OrderedDict()
        photo_width = self._formatting['relative_line_thickness'] * self._formatting['individual_photo_relative_size'] * self._formatting['horizontal_step_size'] # * (1 + self.max_x_index - self.min_x_index)
        # photo_index_width = self._formatting['relative_line_thickness'] * self._formatting['individual_photo_relative_size']
        # photo_fraction_of_total_width = photo_index_width / (self.max_x_index - self.min_x_index)
        aspect_ratio = (self.max_x_index - self.min_x_index)/ (self.max_ordinal - self.min_ordinal) #  * self._formatting['horizontal_step_size']
        photo_height = photo_width #/ aspect_ratio
        #photo_ov_height = photo_height / (self._formatting['total_height']) * (self.chart_max_ordinal-self.chart_min_ordinal)
        photo_ov_height = abs(self._inverse_y_delta(photo_height))
        # photo_ov_height = aspect_ratio / aspect_ratio
        #(self.max_ordinal - self.min_ordinal) / (self._formatting['total_height']) * (photo_width)/(self.max_x_index - self.min_x_index)
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

    images = chart.get_filtered_photos(birth_ordinal_value, original_images)
    chart._instances[('i', individual_id)].images.update(images)
    chart._instances[('i', '@I98@')].images.update(images)

    chart.define_svg_items()

    chart.paint_and_save(os.path.join(
        os.path.dirname(__file__), 'output', 'test_svg_photos_selection.svg'))



def test_generate_svg_update_interface():
    chart = AncestorChart(instance_container=get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged')))

    # select individual to show
    #chart.set_positioning({'compress':True, 'flip_to_optimize':True})
    chart.set_chart_configuration({'root_individuals':[
        {'individual_id':'@I25@', 'generations':5},
        {'individual_id':'@I69@', 'generations':2},
        ]})
    chart.update_chart()

    chart.paint_and_save(os.path.join(
        os.path.dirname(__file__), 'output', 'test_svg_ancestor_configuration.svg'))


def test_generate_svg_update_interface_descendant():
    chart = DescendantChart(instance_container=get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged')))

    # select individual to show
    chart.set_chart_configuration({'root_individuals':[
        {'individual_id':'@I25@', 'generations':5},
        {'individual_id':'@I30@', 'generations':2},
        ]})
    chart.update_chart()

    chart.paint_and_save(os.path.join(
        os.path.dirname(__file__), 'output', 'test_svg_descendant_configuration.svg'))


def test_generate_svg_update_interface_parent_placement():
    chart = AncestorChart(instance_container=get_gedcom_instance_container(
        os.path.join(os.path.dirname(__file__), 'autogenerated.ged')))

    # select individual to show
    #chart.set_positioning({'compress':True, 'flip_to_optimize':True})
    chart.set_chart_configuration({'root_individuals':[
        {'individual_id':'@I450@', 'generations':8},
        #{'individual_id':'@I69@', 'generations':2},
        ],
        'ancestor_placement': {
            (0, '@F68@'): ((0, '@F137@'),(0, '@I236@')),
            (0, '@F67@'): ((0, '@F136@'),(0, '@I233@'))
        }
    })
    chart.update_chart()

    chart.paint_and_save(os.path.join(
        os.path.dirname(__file__), 'output', 'test_svg_ancestor_configuration_parent_placement.svg'))





# import life_line_chart, logging
# life_line_chart.logger.setLevel(logging.DEBUG)
# test_photos_in_chart()
# test_generate_svg_file_ancestor_and_children()
# test_generate_svg_update_interface()
# test_generate_svg_update_interface_descendant()
# test_generate_svg_update_interface_parent_placement()
# test_photos_in_chart_selection()
