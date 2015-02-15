# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.staticfiles.finders import get_finders
from django.core.files.storage import FileSystemStorage


class SassFileStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = getattr(settings, 'SASS_PROCESSOR_ROOT', settings.STATIC_ROOT)
        if base_url is None:
            base_url = settings.STATIC_URL
        super(SassFileStorage, self).__init__(location, base_url, *args, **kwargs)


def find_file(path):
    for finder in get_finders():
        result = finder.find(path)
        if result:
            return result
