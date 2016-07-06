# -*- coding: utf-8 -*-

from django.template import Context, Library
from django.template.base import Node, TemplateSyntaxError
from ..processor import SassProcessor

register = Library()


class SassSrcNode(Node):
    def __init__(self, path, jinja2_template_file=None):
        self.sass_processor = SassProcessor(path)
        self.jinja2_template_file = jinja2_template_file

    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        if len(bits) != 2:
            raise TemplateSyntaxError("'{0}' takes a URL to a CSS file as its only argument".format(*bits))
        path = parser.compile_filter(bits[1])
        return cls(path)

    @property
    def path(self):
        context = Context()
        return self.sass_processor.resolve_path(context)

    @property
    def is_sass(self):
        return self.sass_processor.is_sass()

    def render(self, context, path=None):
        if path is None:
            path = self.sass_processor.resolve_path(context)
        try:
            url = self.sass_processor.get_css_url(path)
        except FileNotFoundError as e:
            msg = str(e) + " while rendering template {}"
            if self.jinja2_template_file is None:
                template_name = self.source[0].name
            else:
                template_name = self.jinja2_template_file
            raise TemplateSyntaxError(msg.format(template_name))
        return url


@register.tag(name='sass_src')
def render_sass_src(parser, token):
    return SassSrcNode.handle_token(parser, token)
