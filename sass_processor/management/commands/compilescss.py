# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import django
import sass
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template  # noqa Leave this in to preload template locations
from importlib import import_module
from django.template.base import Origin
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _
from compressor.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from sass_processor.templatetags.sass_tags import SassSrcNode
from sass_processor.storage import find_file
from sass_processor.utils import get_setting


class Command(BaseCommand):
    help = "Compile SASS/SCSS into CSS outside of the request/response cycle"

    def __init__(self):
        self.parser = None
        self.template_exts = getattr(settings, 'SASS_TEMPLATE_EXTS', ['.html'])
        self.sass_output_style = getattr(settings, 'SASS_OUTPUT_STYLE',
            'nested' if settings.DEBUG else 'compressed')
        precision = getattr(settings, 'SASS_PRECISION', None)
        self.sass_precision = int(precision) if precision else None
        self.use_static_root = False
        self.static_root = ''
        super(Command, self).__init__()

    def add_arguments(self, parser):
        parser.add_argument('--delete-files',
            action='store_true',
            dest='delete_files',
            default=False,
            help=_("Delete generated `*.css` files instead of creating them.")
        )
        parser.add_argument('--use-processor-root',
            action='store_true',
            dest='use_processor_root',
            default=False,
            help=_("Store resulting .css in settings.SASS_PROCESSOR_ROOT folder. "
                   "Default: store each css side-by-side with .scss.")
        )
        parser.add_argument('--engine',
            dest='engine',
            default='django',
            help=_("Set templating engine used (django, jinja2). Default: django.")
        )

    def handle(self, *args, **options):
        self.verbosity = int(options['verbosity'])
        self.delete_files = options['delete_files']
        self.use_static_root = options['use_processor_root']
        if self.use_static_root:
            self.static_root = getattr(settings, 'SASS_PROCESSOR_ROOT', settings.STATIC_ROOT)
        self.parser = self.get_parser(options['engine'])
        self.compiled_files = []
        templates = self.find_templates()
        for template_name in templates:
            self.parse_template(template_name)
        if self.verbosity > 0:
            if self.delete_files:
                self.stdout.write('Successfully deleted {0} previously generated `*.css` files.'.format(len(self.compiled_files)))
            else:
                self.stdout.write('Successfully compiled {0} referred SASS/SCSS files.'.format(len(self.compiled_files)))

    def get_parser(self, engine):
        if engine == "jinja2":
            from compressor.offline.jinja2 import Jinja2Parser
            env = settings.COMPRESS_JINJA2_GET_ENVIRONMENT()
            parser = Jinja2Parser(charset=settings.FILE_CHARSET, env=env)
        elif engine == "django":
            from compressor.offline.django import DjangoParser
            parser = DjangoParser(charset=settings.FILE_CHARSET)
        else:
            raise CommandError("Invalid templating engine '{}' specified.".format(engine))

        return parser

    def find_templates(self):
        paths = set()
        for loader in self.get_loaders():
            try:
                module = import_module(loader.__module__)
                get_template_sources = getattr(module, 'get_template_sources', loader.get_template_sources)
                template_sources = get_template_sources('')
                paths.update([t.name if isinstance(t, Origin) else t for t in template_sources])
            except (ImportError, AttributeError):
                pass
        if not paths:
            raise CommandError("No template paths found. None of the configured template loaders provided template paths")
        templates = set()
        for path in paths:
            for root, _, files in os.walk(str(path)):
                templates.update(os.path.join(root, name)
                    for name in files if not name.startswith('.') and
                        any(name.endswith(ext) for ext in self.template_exts))
        if not templates:
            raise CommandError("No templates found. Make sure your TEMPLATE_LOADERS and TEMPLATE_DIRS settings are correct.")
        return templates

    def get_loaders(self):
        if django.VERSION < (1, 8):
            from django.template.base import TemplateDoesNotExist as DjangoTemplateDoesNotExist
            from django.template.loader import template_source_loaders
            if template_source_loaders is None:
                try:
                    from django.template.loader import (
                        find_template as finder_func)
                except ImportError:
                    from django.template.loader import (
                        find_template_source as finder_func)  # noqa
                try:
                    # Force django to calculate template_source_loaders from
                    # TEMPLATE_LOADERS settings, by asking to find a dummy template
                    source, name = finder_func('test')
                except DjangoTemplateDoesNotExist:
                    pass
                # Reload template_source_loaders now that it has been calculated ;
                # it should contain the list of valid, instanciated template loaders
                # to use.
                from django.template.loader import template_source_loaders
        else:
            from django.template import engines
            template_source_loaders = []
            for e in engines.all():
                template_source_loaders.extend(e.engine.get_template_loaders(e.engine.loaders))
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

    def parse_template(self, template_name):
        try:
            template = self.parser.parse(template_name)
        except IOError:  # unreadable file -> ignore
            self.stdout.write("Unreadable template at: %s\n" % template_name)
            return
        except TemplateSyntaxError as e:  # broken template -> ignore
            self.stdout.write("Invalid template %s: %s\n" % (template_name, e))
            return
        except TemplateDoesNotExist:  # non existent template -> ignore
            self.stdout.write("Non-existent template at: %s\n" % template_name)
            return
        except UnicodeDecodeError:
            self.stdout.write("UnicodeDecodeError while trying to read template %s\n" % template_name)
        try:
            nodes = list(self.walk_nodes(template, original=template))
        except Exception as e:
            # Could be an error in some base template
            self.stdout.write("Error parsing template %s: %s\n" % (template_name, e))
        else:
            for node in nodes:
                if self.delete_files:
                    self.delete_file(node)
                else:
                    self.compile(node)

    def compile(self, node):
        sass_filename = find_file(node.path)
        if not sass_filename or sass_filename in self.compiled_files:
            return

        # add a functions to be used from inside SASS
        custom_functions = {'get-setting': get_setting}

        compile_kwargs = {
            'filename': sass_filename,
            'include_paths': node.include_paths,
            'custom_functions': custom_functions,
        }
        if self.sass_precision:
            compile_kwargs['precision'] = self.sass_precision
        if self.sass_output_style:
            compile_kwargs['output_style'] = self.sass_output_style
        content = sass.compile(**compile_kwargs)
        destpath = self.get_destination(sass_filename)
        with open(destpath, 'wb') as fh:
            fh.write(force_bytes(content))
        self.compiled_files.append(sass_filename)
        if self.verbosity > 1:
            self.stdout.write("Compiled SASS/SCSS file: '{0}'\n".format(node.path))

    def delete_file(self, node):
        """
        Delete a *.css file, but only if it has been generated through a SASS/SCSS file.
        """
        sass_filename = find_file(node.path)
        if not sass_filename:
            return
        destpath = self.get_destination(sass_filename)
        if os.path.isfile(destpath):
            os.remove(destpath)
            self.compiled_files.append(sass_filename)
            if self.verbosity > 1:
                self.stdout.write("Deleted '{0}'\n".format(destpath))

    def get_destination(self, source):
        if not self.use_static_root:
            basename, _ = os.path.splitext(source)
            destpath = basename + '.css'
        else:
            basename, _ = os.path.splitext(os.path.basename(source))
            destpath = os.path.join(self.static_root, basename + '.css')

        return destpath

    def walk_nodes(self, node, original):
        """
        Iterate over the nodes recursively yielding the templatetag 'sass_src'
        """
        for node in self.parser.get_nodelist(node, original=original):
            if isinstance(node, SassSrcNode):
                if node.is_sass:
                    yield node
            else:
                for node in self.walk_nodes(node, original=original):
                    yield node
