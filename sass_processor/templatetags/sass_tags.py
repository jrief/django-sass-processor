# -*- coding: utf-8 -*-
import os
import json
import sass
from django.conf import settings
from django.core.files.base import ContentFile
from django.template import Library, Context
from django.template.base import Node, TemplateSyntaxError
from django.utils.encoding import iri_to_uri
from django.utils.six.moves.urllib.parse import urljoin
from ..storage import SassFileStorage, find_file

register = Library()


class SassSrcNode(Node):
    def __init__(self, path):
        self.storage = SassFileStorage()
        self.include_paths = list(getattr(settings, 'SASS_PROCESSOR_INCLUDE_DIRS', []))
        self.prefix = iri_to_uri(getattr(settings, 'STATIC_URL', ''))
        self._sass_exts = ('.scss', '.sass')
        self._path = path

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
        return self._path.resolve(context)

    @property
    def is_sass(self):
        _, ext = os.path.splitext(self.path)
        return ext in self._sass_exts

    def is_latest(self, sourcemap_filename):
        sourcemap_file = find_file(sourcemap_filename)
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
        path = self._path.resolve(context)
        basename, ext = os.path.splitext(path)
        filename = find_file(path)
        if ext not in self._sass_exts:
            # return the given path, since it ends neither in `.scss` nor in `.sass`
            return urljoin(self.prefix, path)

        # compare timestamp of sourcemap file with all its dependencies, and check if we must recompile
        css_filename = basename + '.css'
        url = urljoin(self.prefix, css_filename)
        if not getattr(settings, 'SASS_PROCESSOR_ENABLED', settings.DEBUG):
            return url
        sourcemap_filename = css_filename + '.map'
        if self.is_latest(sourcemap_filename):
            return url

        # otherwise compile the SASS/SCSS file into .css and store it
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
