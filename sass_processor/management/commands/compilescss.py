import os

import ast
from importlib import import_module
import sass
from compressor.exceptions import TemplateDoesNotExist, TemplateSyntaxError

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.template import engines
from django.template.base import Origin
from django.template.loader import \
    get_template  # in order to preload template locations
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _

from sass_processor.apps import APPS_INCLUDE_DIRS
from sass_processor.processor import SassProcessor
from sass_processor.storage import SassFileStorage, find_file
from sass_processor.templatetags.sass_tags import SassSrcNode
from sass_processor.utils import get_custom_functions

__all__ = ['get_template', 'Command']


class FuncCallVisitor(ast.NodeVisitor):

    def __init__(self, func_name):
        self.func_name = func_name
        self.sass_files = []

    def visit_Call(self, node):
        try:
            if node.func.id == self.func_name:
                arg0 = dict((a, b) for a, b in ast.iter_fields(node))['args'][0]
                self.sass_files.append(getattr(arg0, arg0._fields[0]))
        except AttributeError:
            pass
        self.generic_visit(node)


class Command(BaseCommand):
    help = "Compile SASS/SCSS into CSS outside of the request/response cycle"
    storage = SassFileStorage()

    def __init__(self):
        self.parser = None
        self.template_exts = getattr(settings, 'SASS_TEMPLATE_EXTS', ['.html'])
        self.sass_output_style = getattr(settings, 'SASS_OUTPUT_STYLE',
                                         'nested' if settings.DEBUG else 'compressed')
        self.use_storage = False
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-files',
            action='store_true',
            dest='delete_files',
            default=False,
            help=_("Delete generated `*.css` files instead of creating them.")
        )
        parser.add_argument(
            '--use-storage',
            action='store_true',
            dest='use_storage',
            default=False,
            help=_("Store resulting .css in configured storage. "
                   "Default: store each css side-by-side with .scss.")
        )
        parser.add_argument(
            '--engine',
            dest='engine',
            default='django',
            help=_("Set templating engine used (django, jinja2). Default: django.")
        )
        parser.add_argument(
            '--sass-precision',
            dest='sass_precision',
            type=int,
            help=_(
                "Set the precision for numeric computations in the SASS processor. Default: settings.SASS_PRECISION.")
        )

    def get_loaders(self):
        template_source_loaders = []
        for e in engines.all():
            if hasattr(e, 'engine'):
                template_source_loaders.extend(
                    e.engine.get_template_loaders(
                        e.engine.loaders
                    )
                )
        loaders = []
        # If template loader is CachedTemplateLoader, return the loaders
        # that it wraps around. So if we have
        # TEMPLATE_LOADERS = (
        #    ('django.template.loaders.cached.Loader', (
        #        'django.template.loaders.filesystem.Loader',
        #        'django.template.loaders.app_directories.Loader',
        #    )),
        # )
        # The loaders will return django.template.loaders.filesystem.Loader
        # and django.template.loaders.app_directories.Loader
        # The cached Loader and similar ones include a 'loaders' attribute
        # so we look for that.
        for loader in template_source_loaders:
            if hasattr(loader, 'loaders'):
                loaders.extend(loader.loaders)
            else:
                loaders.append(loader)
        return loaders

    def get_parser(self, engine):
        if engine == 'jinja2':
            from compressor.offline.jinja2 import Jinja2Parser
            env = settings.COMPRESS_JINJA2_GET_ENVIRONMENT()
            parser = Jinja2Parser(charset='utf-8', env=env)
        elif engine == 'django':
            from compressor.offline.django import DjangoParser
            parser = DjangoParser(charset='utf-8')
        else:
            raise CommandError(
                "Invalid templating engine '{engine}' specified.".format(
                    engine=engine
                )
            )
        return parser

    def handle(self, *args, **options):
        self.verbosity = int(options['verbosity'])
        self.delete_files = options['delete_files']
        self.use_storage = options['use_storage']

        engines = [e.strip() for e in options.get('engines', [])] or ['django']
        for engine in engines:
            self.parser = self.get_parser(engine)
            try:
                self.sass_precision = int(options['sass_precision'] or settings.SASS_PRECISION)
            except (AttributeError, TypeError, ValueError):
                self.sass_precision = None

            self.processed_files = []

            # find all Python files making up this project; They might invoke `sass_processor`
            for py_source in self.find_sources():
                if self.verbosity > 1:
                    self.stdout.write("Parsing file: {}".format(py_source))
                elif self.verbosity == 1:
                    self.stdout.write(".", ending="")
                try:
                    self.parse_source(py_source)
                except (SyntaxError, IndentationError) as exc:
                    msg = "Syntax error encountered processing {0}: {1}\nAborting compilation."
                    self.stderr.write(msg.format(py_source, exc))
                    raise

            # find all Django/Jinja2 templates making up this project; They might invoke `sass_src`
            templates = self.find_templates()
            for template_name in templates:
                self.parse_template(template_name)
                if self.verbosity > 0:
                    self.stdout.write(".", ending="")

            # summarize what has been done
            if self.verbosity > 0:
                self.stdout.write("")
                if self.delete_files:
                    msg = "Successfully deleted {0} previously generated `*.css` files."
                    self.stdout.write(msg.format(len(self.processed_files)))
                else:
                    msg = "Successfully compiled {0} referred SASS/SCSS files."
                    self.stdout.write(msg.format(len(self.processed_files)))

    def find_sources(self):
        """
        Look for Python sources available for the current configuration.
        """
        app_config = apps.get_app_config('sass_processor')
        if app_config.auto_include:
            app_configs = apps.get_app_configs()
            for app_config in app_configs:
                ignore_dirs = []
                for root, dirs, files in os.walk(app_config.path):
                    if [True for idir in ignore_dirs if root.startswith(idir)]:
                        continue
                    if '__init__.py' not in files:
                        ignore_dirs.append(root)
                        continue
                    for filename in files:
                        basename, ext = os.path.splitext(filename)
                        if ext != '.py':
                            continue
                        yield os.path.abspath(os.path.join(root, filename))

    def parse_source(self, filename):
        """
        Extract the statements from the given file, look for function calls
        `sass_processor(scss_file)` and compile the filename into CSS.
        """
        callvisitor = FuncCallVisitor('sass_processor')
        tree = ast.parse(open(filename, 'rb').read())
        callvisitor.visit(tree)
        for sass_fileurl in callvisitor.sass_files:
            sass_filename = find_file(sass_fileurl)
            if not sass_filename or sass_filename in self.processed_files:
                continue
            if self.delete_files:
                self.delete_file(sass_filename, sass_fileurl)
            else:
                self.compile_sass(sass_filename, sass_fileurl)

    def find_templates(self):
        """
        Look for templates and extract the nodes containing the SASS file.
        """
        paths = set()
        for loader in self.get_loaders():
            try:
                module = import_module(loader.__module__)
                get_template_sources = getattr(
                    module, 'get_template_sources', loader.get_template_sources)
                template_sources = get_template_sources('')
                paths.update([t.name if isinstance(t, Origin) else t for t in template_sources])
            except (ImportError, AttributeError):
                pass
        if not paths:
            raise CommandError(
                "No template paths found. None of the configured template loaders provided template paths")
        templates = set()
        for path in paths:
            for root, _, files in os.walk(str(path)):
                templates.update(os.path.join(root, name)
                                 for name in files if not name.startswith('.') and
                                 any(name.endswith(ext) for ext in self.template_exts))
        if not templates:
            raise CommandError(
                "No templates found. Make sure your TEMPLATE_LOADERS and TEMPLATE_DIRS settings are correct.")
        return templates

    def parse_template(self, template_name):
        try:
            template = self.parser.parse(template_name)
        except IOError:  # unreadable file -> ignore
            if self.verbosity > 0:
                self.stderr.write("\nUnreadable template at: {}".format(template_name))
            return
        except TemplateSyntaxError as e:  # broken template -> ignore
            if self.verbosity > 0:
                self.stderr.write("\nInvalid template {}: {}".format(template_name, e))
            return
        except TemplateDoesNotExist:  # non existent template -> ignore
            if self.verbosity > 0:
                self.stderr.write("\nNon-existent template at: {}".format(template_name))
            return
        except UnicodeDecodeError:
            if self.verbosity > 0:
                self.stderr.write(
                    "\nUnicodeDecodeError while trying to read template {}".format(template_name))
        try:
            nodes = list(self.walk_nodes(template, original=template))
        except Exception as e:
            # Could be an error in some base template
            if self.verbosity > 0:
                self.stderr.write("\nError parsing template {}: {}".format(template_name, e))
        else:
            for node in nodes:
                sass_filename = find_file(node.path)
                if not sass_filename or sass_filename in self.processed_files:
                    continue
                if self.delete_files:
                    self.delete_file(sass_filename, node.path)
                else:
                    self.compile_sass(sass_filename, node.path)

    def compile_sass(self, sass_filename, sass_fileurl):
        """
        Compile the given SASS file into CSS
        """
        compile_kwargs = {
            'filename': sass_filename,
            'include_paths': SassProcessor.include_paths + APPS_INCLUDE_DIRS,
            'custom_functions': get_custom_functions(),
        }
        if self.sass_precision:
            compile_kwargs['precision'] = self.sass_precision
        if self.sass_output_style:
            compile_kwargs['output_style'] = self.sass_output_style
        content = sass.compile(**compile_kwargs)
        self.save_to_destination(content, sass_filename, sass_fileurl)
        self.processed_files.append(sass_filename)
        if self.verbosity > 1:
            self.stdout.write("Compiled SASS/SCSS file: '{0}'\n".format(sass_filename))

    def delete_file(self, sass_filename, sass_fileurl):
        """
        Delete a *.css file, but only if it has been generated through a SASS/SCSS file.
        """
        if self.use_storage:
            destpath = os.path.splitext(sass_fileurl)[0] + '.css'
            if self.storage.exists(destpath):
                self.storage.delete(destpath)
            else:
                return
        else:
            destpath = os.path.splitext(sass_filename)[0] + '.css'
            if os.path.isfile(destpath):
                os.remove(destpath)
            else:
                return
        self.processed_files.append(sass_filename)
        if self.verbosity > 1:
            self.stdout.write("Deleted '{0}'\n".format(destpath))

    def save_to_destination(self, content, sass_filename, sass_fileurl):
        if self.use_storage:
            basename, _ = os.path.splitext(sass_fileurl)
            destpath = basename + '.css'
            if self.storage.exists(destpath):
                self.storage.delete(destpath)
            self.storage.save(destpath, ContentFile(content))
        else:
            basename, _ = os.path.splitext(sass_filename)
            destpath = basename + '.css'
            with open(destpath, 'wb') as fh:
                fh.write(force_bytes(content))

    def walk_nodes(self, node, original):
        """
        Iterate over the nodes recursively yielding the templatetag 'sass_src'
        """
        try:
            # try with django-compressor<2.1
            nodelist = self.parser.get_nodelist(node, original=original)
        except TypeError:
            nodelist = self.parser.get_nodelist(node, original=original, context=None)
        for node in nodelist:
            if isinstance(node, SassSrcNode):
                if node.is_sass:
                    yield node
            else:
                for node in self.walk_nodes(node, original=original):
                    yield node
