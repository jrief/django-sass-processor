from urllib.parse import quote, urljoin
import os
import json
import logging
import subprocess

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.template import Context
from django.templatetags.static import PrefixNode
from django.utils.encoding import force_bytes
from sass_processor.utils import get_custom_functions

from .storage import SassFileStorage, find_file
from .apps import APPS_INCLUDE_DIRS

try:
    import sass
except ImportError:
    sass = None

logger = logging.getLogger('sass-processor')


class SassProcessor:
    storage = SassFileStorage()
    include_paths = list(getattr(settings, 'SASS_PROCESSOR_INCLUDE_DIRS', []))
    try:
        sass_precision = int(settings.SASS_PRECISION)
    except (AttributeError, TypeError, ValueError):
        sass_precision = None
    sass_output_style = getattr(
        settings,
        'SASS_OUTPUT_STYLE',
        'nested' if settings.DEBUG else 'compressed')
    processor_enabled = getattr(settings, 'SASS_PROCESSOR_ENABLED', settings.DEBUG)
    sass_extensions = ('.scss', '.sass')
    node_npx_path = getattr(settings, 'NODE_NPX_PATH', 'npx')

    def __init__(self, path=None):
        self._path = path
        nmd = [d[1] for d in getattr(settings, 'STATICFILES_DIRS', [])
               if isinstance(d, (list, tuple)) and d[0] == 'node_modules']
        self.node_modules_dir = nmd[0] if len(nmd) else None

    def __call__(self, path):
        basename, ext = os.path.splitext(path)
        filename = find_file(path)
        if filename is None:
            raise FileNotFoundError("Unable to locate file {path}".format(path=path))

        if ext not in self.sass_extensions:
            # return the given path, since it ends neither in `.scss` nor in `.sass`
            return path

        # compare timestamp of sourcemap file with all its dependencies, and check if we must recompile
        css_filename = basename + '.css'
        if not self.processor_enabled:
            return css_filename
        sourcemap_filename = css_filename + '.map'
        base = os.path.dirname(filename)
        if find_file(css_filename) and self.is_latest(sourcemap_filename, base):
            return css_filename

        # with offline compilation, raise an error, if css file could not be found.
        if sass is None:
            msg = "Offline compiled file `{}` is missing and libsass has not been installed."
            raise ImproperlyConfigured(msg.format(css_filename))

        # otherwise compile the SASS/SCSS file into .css and store it
        filename_map = filename.replace(ext, '.css.map')
        compile_kwargs = {
            'filename': filename,
            'source_map_filename': filename_map,
            'include_paths': self.include_paths + APPS_INCLUDE_DIRS,
            'custom_functions': get_custom_functions(),
        }
        if self.sass_precision:
            compile_kwargs['precision'] = self.sass_precision
        if self.sass_output_style:
            compile_kwargs['output_style'] = self.sass_output_style
        content, sourcemap = sass.compile(**compile_kwargs)
        content, sourcemap = force_bytes(content), force_bytes(sourcemap)

        # autoprefix CSS files using postcss in external JavaScript process
        if self.node_npx_path and os.path.isdir(self.node_modules_dir or ''):
            os.environ['NODE_PATH'] = self.node_modules_dir
            try:
                options = [self.node_npx_path, 'postcss', '--use', 'autoprefixer']
                if not settings.DEBUG:
                    options.append('--no-map')
                proc = subprocess.Popen(options, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                proc.stdin.write(content)
                proc.stdin.close()
                autoprefixed_content = proc.stdout.read()
                proc.wait()
            except (FileNotFoundError, BrokenPipeError) as exc:
                logger.warning("Unable to postcss {}. Reason: {}".format(filename, exc))
            else:
                if len(autoprefixed_content) >= len(content):
                    content = autoprefixed_content

        if self.storage.exists(css_filename):
            self.storage.delete(css_filename)
        self.storage.save(css_filename, ContentFile(content))
        if self.storage.exists(sourcemap_filename):
            self.storage.delete(sourcemap_filename)
        self.storage.save(sourcemap_filename, ContentFile(sourcemap))
        return css_filename

    def resolve_path(self, context=None):
        if context is None:
            context = Context()
        return self._path.resolve(context)

    def is_sass(self):
        _, ext = os.path.splitext(self.resolve_path())
        return ext in self.sass_extensions

    def is_latest(self, sourcemap_filename, base):
        sourcemap_file = find_file(sourcemap_filename)
        if not sourcemap_file or not os.path.isfile(sourcemap_file):
            return False
        sourcemap_mtime = os.stat(sourcemap_file).st_mtime
        with open(sourcemap_file, 'r') as fp:
            sourcemap = json.load(fp)
        for srcfilename in sourcemap.get('sources'):
            srcfilename = os.path.join(base, srcfilename)
            if not os.path.isfile(srcfilename) or os.stat(srcfilename).st_mtime > sourcemap_mtime:
                # at least one of the source is younger that the sourcemap referring it
                return False
        return True

    @classmethod
    def handle_simple(cls, path):
        if apps.is_installed('django.contrib.staticfiles'):
            from django.contrib.staticfiles.storage import staticfiles_storage
            return staticfiles_storage.url(path)
        else:
            return urljoin(PrefixNode.handle_simple('STATIC_URL'), quote(path))

_sass_processor = SassProcessor()
def sass_processor(filename):
    path = _sass_processor(filename)
    return SassProcessor.handle_simple(path)
