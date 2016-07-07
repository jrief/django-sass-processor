# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from jinja2 import lexer, nodes
from jinja2.ext import Extension
from sass_processor.processor import SassProcessor


class SassSrc(Extension):
    tags = set(['sass_src'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        token = parser.stream.expect(
            lexer.TOKEN_STRING
        )
        path = nodes.Const(token.value)

        call = self.call_method(
            '_sass_src_support', [
                path,
                nodes.Const(parser.filename)
            ]
        )
        return nodes.Output(
            [call],
            lineno=lineno
        )

    def _sass_src_support(self, path, source_file):
        sass_processor = SassProcessor(source_file)
        return sass_processor(path)
