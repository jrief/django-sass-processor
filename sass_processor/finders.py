from django.contrib.staticfiles.finders import BaseStorageFinder
from .storage import SassFileStorage


class CssFinder(BaseStorageFinder):
    """
    Find static *.css files compiled on the fly using templatetag `{% sass_src "" %}`
    and stored in configured storage.
    """
    storage = SassFileStorage()

    def list(self, ignore_patterns):
        """
        Do not list the contents of the configured storages, since this has already been done by
        other finders.
        This prevents the warning ``Found another file with the destination path ...``, while
        issuing ``./manage.py collectstatic``.
        """
        if False:
            yield
