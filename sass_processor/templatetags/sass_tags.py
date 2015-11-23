# -*- coding: utf-8 -*-
import os
import json
try:
    import sass
except ImportError:
    sass = None
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ImproperlyConfigured
from django.template import Library, Context
from django.template.base import Node, TemplateSyntaxError
from django.utils.encoding import iri_to_uri, force_bytes
from django.utils.six.moves.urllib.parse import urljoin
from sass_processor.utils import get_setting
from ..storage import SassFileStorage, find_file

register = Library()


class SassSrcNode(Node):
    def __init__(self, path):
        self.storage = SassFileStorage()
        self.include_paths = list(getattr(settings, 'SASS_PROCESSOR_INCLUDE_DIRS', []))
        self.prefix = iri_to_uri(getattr(settings, 'STATIC_URL', ''))
        precision = getattr(settings, 'SASS_PRECISION', None)
        self.sass_precision = int(precision) if precision else None
        self.sass_output_style = getattr(
            settings,
            'SASS_OUTPUT_STYLE',
            'nested' if settings.DEBUG else 'compressed')
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
        if filename is None:
            msg = "Unable to locate file {0} while rendering template {1}".format(path, self.source[0].name)
            raise TemplateSyntaxError(msg)
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

        # with offline compilation, raise an error, if css file could not be found.
        if sass is None:
            raise ImproperlyConfigured("Offline compiled file `{}` is missing and libsass has not been installed.".format(css_filename))

        # add a functions to be used from inside SASS
        custom_functions = {'get-setting': get_setting}

        # otherwise compile the SASS/SCSS file into .css and store it
        sourcemap_url = self.storage.url(sourcemap_filename)
        compile_kwargs = {
            'filename': filename,
            'source_map_filename': sourcemap_url,
            'include_paths': self.include_paths,
            'custom_functions': custom_functions,
        }
        if self.sass_precision:
            compile_kwargs['precision'] = self.sass_precision
        if self.sass_output_style:
            compile_kwargs['output_style'] = self.sass_output_style
        content, sourcemap = sass.compile(**compile_kwargs)
        content = force_bytes(content)
        sourcemap = force_bytes(sourcemap)
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
