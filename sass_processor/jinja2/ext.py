# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from jinja2 import nodes
from jinja2.ext import Extension
from sass_processor.processor import SassProcessor


class SassSrc(Extension):
    tags = set(['sass_src'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        path = parser.parse_expression()

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
        return SassProcessor.handle_simple(sass_processor(path))
