# -*- coding: utf-8 -*-
import os
import sass
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template  # noqa Leave this in to preload template locations
from django.utils.importlib import import_module
from django.utils.encoding import force_bytes
from compressor.offline.django import DjangoParser
from compressor.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from sass_processor.templatetags.sass_tags import SassSrcNode
from sass_processor.storage import find_file


class Command(BaseCommand):
    help = "Compile SASS/SCSS into CSS outside of the request/response cycle"
    option_list = BaseCommand.option_list + (make_option('--delete-files', action='store_true',
        dest='delete_files', default=False, help='Delete generated `*.css` files instead of creating them.'),)

    def __init__(self):
        self.parser = DjangoParser(charset=settings.FILE_CHARSET)
        self.template_exts = getattr(settings, 'SASS_TEMPLATE_EXTS', ['.html'])
        self.output_style = getattr(settings, 'SASS_OUTPUT_STYLE', 'compact')
        super(Command, self).__init__()

    def handle(self, *args, **options):
        self.verbosity = int(options['verbosity'])
        self.delete_files = options['delete_files']
        self.compiled_files = []
        templates = self.find_templates()
        for template_name in templates:
            self.parse_template(template_name)
        if self.verbosity > 0:
            if self.delete_files:
                self.stdout.write('Successfully deleted {0} previously generated `*.css` files.'.format(len(self.compiled_files)))
            else:
                self.stdout.write('Successfully compiled {0} referred SASS/SCSS files.'.format(len(self.compiled_files)))

    def find_templates(self):
        paths = set()
        for loader in self.get_loaders():
            try:
                module = import_module(loader.__module__)
                get_template_sources = getattr(module, 'get_template_sources', loader.get_template_sources)
                paths.update(list(get_template_sources('')))
            except (ImportError, AttributeError):
                pass
        if not paths:
            raise CommandError("No template paths found. None of the configured template loaders provided template paths")
        templates = set()
        for path in paths:
            for root, _, files in os.walk(path):
                templates.update(os.path.join(root, name)
                    for name in files if not name.startswith('.') and
                        any(name.endswith(ext) for ext in self.template_exts))
        if not templates:
            raise CommandError("No templates found. Make sure your TEMPLATE_LOADERS and TEMPLATE_DIRS settings are correct.")
        return templates

    def get_loaders(self):
        try:
            from django.template.loader import (
                find_template as finder_func)
        except ImportError:
            from django.template.loader import (find_template_source as finder_func)
        try:
            # Force Django to calculate template_source_loaders from
            # TEMPLATE_LOADERS settings, by asking to find a dummy template
            finder_func('test')
        # Had to transform this Exception, because otherwise even if there
        # was a try catch it was crashing, this is a broad Exception but at
        # it does what the try catch does by not crashing the command line
        # execution.
        except Exception, e:
            pass
        loaders = []
        # At the top when you first import template_source_loaders it is set
        # to None, because in django that is what it is set too. While it
        # executes the finder_func it is setting the template_source_loaders
        # I needed to re-import the value of it at this point because it was
        # still None and importing it again made it filled with the proper
        # django default values.
        from django.template.loader import template_source_loaders
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
            nodes = list(self.walk_nodes(template))
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
        content = sass.compile(include_paths=node.include_paths, filename=sass_filename, output_style=self.output_style)
        basename, _ = os.path.splitext(sass_filename)
        destpath = basename + '.css'
        with open(destpath, 'w') as fh:
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
        basename, _ = os.path.splitext(sass_filename)
        destpath = basename + '.css'
        if os.path.isfile(destpath):
            os.remove(destpath)
            self.compiled_files.append(sass_filename)
            if self.verbosity > 1:
                self.stdout.write("Deleted '{0}'\n".format(destpath))

    def walk_nodes(self, node):
        """
        Iterate over the nodes recursively yielding the templatetag 'sass_src'
        """
        for node in self.parser.get_nodelist(node):
            if isinstance(node, SassSrcNode):
                if node.is_sass:
                    yield node
            else:
                for node in self.walk_nodes(node):
                    yield node
