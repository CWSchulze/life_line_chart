"""
This is a set of functions generation graphical item information dicts
"""


def new_image_item(self, pos_x, pos_y, size_x, size_y, filename, original_size, **kwargs):
    data = {
                'type': 'image',
                'config': {
                    'insert': (pos_x, pos_y),
                    'size': (size_x, size_y)
                },
                'filename': filename,
                'size': original_size
            }
    data.update(kwargs)
    return data

def new_text_item(self, text, pos_x, pos_y, font_size=None, color="default", text_anchor='middle', **kwargs):
    line_thickness = self._formatting['relative_line_thickness'] * \
        self._formatting['horizontal_step_size']
    if font_size is None:
        font_size = self._formatting['font_size_description'] * line_thickness
    if color=='default':
        if self._colors['text_label'] == (0, 0, 0):
            color = None
        else:
            color = self._colors['text_label']
    data = {
            'type': 'text',
            'config': {
                    'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                    'text': text,
                    'text_anchor': text_anchor,
                    # 'align' : 'center',
                    'insert': (
                        pos_x,
                        pos_y
                    ),
            },
            'font_size': font_size,
            'font_name': self._formatting['font_name'],
        }
    if 'transform' in kwargs and kwargs['transform'] is None:
        kwargs.pop('transform')
    if color:
        data['config']['fill'] = "rgb({},{},{})".format(*color)
        data['fill'] = color
    data['config'].update(kwargs)
    return data

def new_path_item(self, path_type, points, color, stroke_width, **kwargs):
    data = {
            'type': 'path',
            'config': {'type': path_type, 'arguments': points},
            'color': color,
            'stroke_width': stroke_width
            }
    data.update(kwargs)
    return data
