# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
from django.conf import settings
from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.storage import FileSystemStorage


class CssFinder(FileSystemFinder):
    """
    Find static *.css files compiled on the fly using templatetag `{% sass_src "" %}`
    and stored below `SASS_PROCESSOR_ROOT`.
    """
    locations = []

    def __init__(self, apps=None, *args, **kwargs):
        location = getattr(settings, 'SASS_PROCESSOR_ROOT', settings.STATIC_ROOT)
        if not os.path.isdir(location):
            return
        self.locations = [
            ('', location),
        ]
        self.storages = OrderedDict()
        filesystem_storage = FileSystemStorage(location=location)
        filesystem_storage.prefix = self.locations[0][0]
        self.storages[location] = filesystem_storage

    def find(self, path, all=False):
        if path.endswith('.css') or path.endswith('.css.map'):
            return super(CssFinder, self).find(path, all)
        return []
