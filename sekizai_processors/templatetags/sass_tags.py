# -*- coding: utf-8 -*-
import os
import json
import sass
from django.conf import settings
from django.contrib.staticfiles.finders import get_finders
from django.core.files.base import ContentFile
from django.template import Library
from django.template.base import Node, TemplateSyntaxError
from django.utils.encoding import iri_to_uri
from django.utils.six.moves.urllib.parse import urljoin
from ..sass_preprocessor import SassFileStorage

register = Library()


class SassSrcNode(Node):
    def __init__(self, path):
        self.include_paths = list(getattr(settings, 'SEKIZAI_PROCESSOR_INCLUDE_DIRS', []))
        self.prefix = iri_to_uri(getattr(settings, 'STATIC_URL', ''))
        self.storage = SassFileStorage()
        self.sass_exts = ('.scss', '.sass')
        self.path = path

    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        if len(bits) < 2:
            raise TemplateSyntaxError("'{0}' takes a path to file as argument".format(*bits))
        path = parser.compile_filter(bits[1])
        return cls(path)

    def find(self, path):
        for finder in get_finders():
            result = finder.find(path)
            if result:
                return result

    def is_latest(self, sourcemap_filename):
        sourcemap_file = self.find(sourcemap_filename)
        if not sourcemap_file or not os.path.isfile(sourcemap_file):
            return False
        sourcemap_mtime = os.stat(sourcemap_file).st_mtime
        with open(sourcemap_file, 'r') as fp:
            sourcemap = json.load(fp)
        for srcfilename in sourcemap.get('sources'):
            components = os.path.normpath(srcfilename).split(os.path.sep)
            srcfilename = ''.join([os.path.sep + c for c in components if c != os.path.pardir])
            if not os.path.isfile(srcfilename) or os.stat(srcfilename).st_mtime > sourcemap_mtime:
                # at least one of the source is younger that the sourcemap referring it
                return False
        return True

    def render(self, context):
        path = self.path.resolve(context)
        basename, ext = os.path.splitext(path)
        filename = self.find(path)
        if not filename or ext not in self.sass_exts:
            # return the given path
            return urljoin(self.prefix, path)

        # compare timestamp of sourcemap file with all its dependencies, and check if we must recompile
        css_filename = basename + '.css'
        url = urljoin(self.prefix, css_filename)
        sourcemap_filename = css_filename + '.map'
        if self.is_latest(sourcemap_filename):
            return url

        # otherwise compile the .scss file into .css and store it
        sourcemap_url = self.storage.url(sourcemap_filename)
        content, sourcemap = sass.compile(filename=filename,
            source_map_filename=sourcemap_url, include_paths=self.include_paths)
        if self.storage.exists(css_filename):
            self.storage.delete(css_filename)
        self.storage.save(css_filename, ContentFile(content))
        if self.storage.exists(sourcemap_filename):
            self.storage.delete(sourcemap_filename)
        self.storage.save(sourcemap_filename, ContentFile(sourcemap))
        return url


@register.tag(name='sass_src')
def render_sass_src(parser, token):
    return SassSrcNode.handle_token(parser, token)
