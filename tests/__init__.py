from sass_processor.types import SassNumber, SassColor

def get_width():
    return SassNumber(5)

def get_margins(top, right, bottom, left):
    return "{}px {}px {}px {}px".format(top.value, right.value, bottom.value, left.value)

def get_plain_color(r, g, b):
    return SassColor(r.value, g.value, b.value, 1)
