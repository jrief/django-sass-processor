from django.conf import settings
from django.contrib.staticfiles.finders import get_finders
from django.core.files.storage import FileSystemStorage
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string


class SassFileStorage(LazyObject):
    def _setup(self):
        if not (sass_processor_storage := settings.STORAGES.get('sass_processor')):
            sass_processor_storage = settings.STORAGES.get('staticfiles', {})
        storage_path = sass_processor_storage.get('BACKEND')
        storage_options = sass_processor_storage.get('OPTIONS') or {}
        storage_class = import_string(storage_path)
        if issubclass(storage_class, FileSystemStorage):
            storage_options['location'] = storage_options.pop('ROOT', None) or settings.STATIC_ROOT
            storage_options['base_url'] = settings.STATIC_URL

        self._wrapped = storage_class(**storage_options)

    def __repr__(self):
        return repr(self._wrapped)


def find_file(path):
    for finder in get_finders():
        result = finder.find(path)
        if result:
            return result
