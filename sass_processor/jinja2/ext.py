from jinja2 import lexer, nodes
from jinja2.ext import Extension

from ..processor import SassProcessor


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
        processor = SassProcessor(source_file)
        return processor.get_css_url(path)
