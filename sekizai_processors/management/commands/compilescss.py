# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.templatetags.static import StaticNode
from django.utils.importlib import import_module
from sekizai.templatetags.sekizai_tags import Addtoblock, import_processor
from compressor.offline.django import DjangoParser
from compressor.exceptions import TemplateDoesNotExist, TemplateSyntaxError


class Command(BaseCommand):
    help = "Compile SASS into CSS outside of the request/response cycle"

    def __init__(self):
        self.parser = DjangoParser(charset=settings.FILE_CHARSET)
        super(Command, self).__init__()

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity'))
        templates = self.find_templates()
        for template_name in templates:
            self.parse_template(template_name)
        if self.verbosity > 0:
            self.stdout.write('Successfully compiled all referred .scss files.')

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
            for root, dirs, files in os.walk(path):
                templates.update(os.path.join(root, name)
                    for name in files if not name.startswith('.') and name.endswith('.html'))
        if not templates:
            raise CommandError("No templates found. Make sure your TEMPLATE_LOADERS and TEMPLATE_DIRS settings are correct.")
        return templates

    def get_loaders(self):
        from django.template.loader import template_source_loaders
        if template_source_loaders is None:
            try:
                from django.template.loader import (
                    find_template as finder_func)
            except ImportError:
                from django.template.loader import (find_template_source as finder_func)
            try:
                # Force django to calculate template_source_loaders from
                # TEMPLATE_LOADERS settings, by asking to find a dummy template
                source, name = finder_func('test')
            except TemplateDoesNotExist:
                pass
        loaders = []
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
                name = node.kwargs['name'].literal
                name = name and name.strip('"')
                preprocessor = node.kwargs['preprocessor'].literal or settings.SEKIZAI_PREPROCESSORS.get(name)
                path = [n.path.var for n in node.nodelist if isinstance(n, StaticNode)]
                if preprocessor and path:
                    srcpath = path[0]
                    processor = import_processor(preprocessor.strip('"'))
                    func = getattr(processor, 'compile_offline', None)
                    if callable(func):
                        destpath = func(srcpath)
                        if destpath and self.verbosity > 1:
                            self.stdout.write("Compiled %s\n" % srcpath)

    def walk_nodes(self, node):
        """
        Iterate over the nodes recursively yielding the templatetag 'addtoblock'
        """
        for node in self.parser.get_nodelist(node):
            if isinstance(node, Addtoblock):
                if node.kwargs['preprocessor'].literal:
                    yield node
                name = node.kwargs['name'].literal
                if name and name.strip('"') in settings.SEKIZAI_PREPROCESSORS:
                    yield node
            else:
                for node in self.walk_nodes(node):
                    yield node
