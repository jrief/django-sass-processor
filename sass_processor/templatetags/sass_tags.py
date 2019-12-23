from django.template import Library
from django.template.base import Node, TemplateSyntaxError
from sass_processor.processor import SassProcessor

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

register = Library()


class SassSrcNode(Node):
    def __init__(self, path):
        self.sass_processor = SassProcessor(path)

    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        if len(bits) != 2:
            raise TemplateSyntaxError("'{0}' takes a URL to a CSS file as its only argument".format(*bits))
        path = parser.compile_filter(bits[1])
        return cls(path)

    @property
    def path(self):
        return self.sass_processor.resolve_path()

    @property
    def is_sass(self):
        return self.sass_processor.is_sass()

    def render(self, context):
        try:
            path = self.sass_processor(self.sass_processor.resolve_path(context))
        except AttributeError as e:
            msg = "No sass/scss file specified while rendering tag 'sass_src' in template {} ({})"
            raise TemplateSyntaxError(msg.format(context.template_name, e))
        except FileNotFoundError as e:
            msg = str(e) + " while rendering tag 'sass_src' in template {}"
            raise TemplateSyntaxError(msg.format(context.template_name))
        return SassProcessor.handle_simple(path)


@register.tag(name='sass_src')
def render_sass_src(parser, token):
    return SassSrcNode.handle_token(parser, token)
