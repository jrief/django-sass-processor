import os
from collections import OrderedDict
from django.conf import settings
from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage


class CssFinder(FileSystemFinder):
    """
    Find static *.css files compiled on the fly using templatetag `{% sass_src "" %}`
    and stored below `SASS_PROCESSOR_ROOT`.
    """
    locations = []

    def __init__(self, apps=None, *args, **kwargs):
        location = getattr(settings, 'SASS_PROCESSOR_ROOT', settings.STATIC_ROOT)
        if not location:
            msg = "Neither 'SASS_PROCESSOR_ROOT' nor 'STATIC_ROOT' has been declared in project settings."
            raise ImproperlyConfigured(msg)
        if not os.path.isdir(location):
            try:
                location = getattr(settings, 'SASS_PROCESSOR_ROOT')
                os.makedirs(location)
            except (AttributeError, OSError):
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
            return super().find(path, all)
        return []

    def list(self, ignore_patterns):
        """
        Do not list the contents of the configured storages, since this has already been done by
        the other finder of type FileSystemFinder.
        This prevents the warning ``Found another file with the destination path ...``, while
        issuing ``./manage.py collectstatic``.
        """
        if False:
            yield
