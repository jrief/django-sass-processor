# -*- coding: utf-8 -*-
from classytags.arguments import Flag
from classytags.core import Tag, Options
from classytags.parser import Parser
from django import template
from .. import sass_preprocessor


register = template.Library()


class ProcessorParser(Parser):
    def parse_blocks(self):
        self.blocks['nodelist'] = self.parser.parse(
            ('sassprocessor', 'endsassprocessor')
        )
        self.parser.delete_first_token()


class SassProcessor(Tag):
    name = 'sassprocessor'
    processor = sass_preprocessor.SCSSProcessor()

    options = Options(
        Flag('strip', default=False, true_values=['strip']),
        parser_class=ProcessorParser,
    )

    def render_tag(self, context, strip, nodelist):
        rendered_contents = nodelist.render(context)
        if strip:
            rendered_contents = rendered_contents.strip()
        rendered_contents = self.processor(context, rendered_contents)
        return rendered_contents

register.tag(SassProcessor)
