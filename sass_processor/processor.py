# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.template import Context
from django.utils.encoding import force_bytes, iri_to_uri
from django.utils.six.moves.urllib.parse import urljoin
from sass_processor.utils import get_setting

from .storage import SassFileStorage, find_file

try:
    import sass
except ImportError:
    sass = None


class SassProcessor(object):
    def __init__(self, path=None):
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

    def __call__(self, path):
        basename, ext = os.path.splitext(path)
        filename = find_file(path)
        if filename is None:
            raise FileNotFoundError("Unable to locate file {path}".format(path=path))

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
            msg = "Offline compiled file `{}` is missing and libsass has not been installed."
            raise ImproperlyConfigured(msg.format(css_filename))

        # add a function to be used from inside SASS
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

    def resolve_path(self, context=None):
        if context is None:
            context = Context()
        return self._path.resolve(context)

    def is_sass(self):
        _, ext = os.path.splitext(self.resolve_path())
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
