from jinja2 import lexer, nodes
from jinja2.ext import Extension

from ..templatetags.sass_tags import SassSrcNode


class SassSrc(Extension):
    tags = set(['sass_src'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        token = parser.stream.expect(
            lexer.TOKEN_STRING
        )
        path = nodes.Const(token.value)

        call = self.call_method(
            '_sass_src_support',
            [
                path,
                nodes.Const(parser.filename)
            ]
        )
        return nodes.Output(
            [call],
            lineno=lineno
        )

    def _sass_src_support(self, path, source_file):
        node = SassSrcNode(path, source_file)
        return node.render(None, path)
