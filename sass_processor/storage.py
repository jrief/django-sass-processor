from django.conf import settings
from django.contrib.staticfiles.finders import get_finders
from django.core.files.storage import FileSystemStorage, get_storage_class
from django.utils.functional import LazyObject


class SassFileStorage(LazyObject):
    def _setup(self):
        storage_path = getattr(settings, 'SASS_PROCESSOR_STORAGE', settings.STATICFILES_STORAGE)
        storage_options = getattr(settings, 'SASS_PROCESSOR_STORAGE_OPTIONS', {})
        storage_class = get_storage_class(storage_path)

        if storage_path == settings.STATICFILES_STORAGE and issubclass(storage_class, FileSystemStorage):
            storage_options['location'] = getattr(settings, 'SASS_PROCESSOR_ROOT', settings.STATIC_ROOT)
            storage_options['base_url'] = settings.STATIC_URL

        self._wrapped = storage_class(**storage_options)


def find_file(path):
    for finder in get_finders():
        result = finder.find(path)
        if result:
            return result
