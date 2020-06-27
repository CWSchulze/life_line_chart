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

def new_text_item(self, text, pos_x, pos_y, font_size, color=None, text_anchor='middle', **kwargs):
    if color:
        color = "rgb({},{},{})".format(*color)
    data = {
            'type': 'text',
            'config': {
                    'style': f"font-size:{font_size}px;font-family:{self._formatting['font_name']}",
                    'text': text,
                    'fill': color,
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
    data['config'].update(kwargs)
    return data