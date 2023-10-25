from django.conf import settings
from django.contrib.staticfiles.finders import get_finders
from django.core.files.storage import FileSystemStorage
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string


class SassFileStorage(LazyObject):
    def _setup(self):
        staticfiles_storage_backend = settings.STORAGES.get("staticfiles", {}).get("BACKEND")
        sass_processor_storage = settings.STORAGES.get("sass_processor", {})

        storage_path = sass_processor_storage.get("BACKEND") or staticfiles_storage_backend
        storage_options = sass_processor_storage.get("OPTIONS") or {}
        storage_class = import_string(storage_path)

        if storage_path == staticfiles_storage_backend and issubclass(storage_class, FileSystemStorage):
            storage_options['location'] = storage_options.get("ROOT") or settings.STATIC_ROOT
            storage_options['base_url'] = settings.STATIC_URL

        self._wrapped = storage_class(**storage_options)


def find_file(path):
    for finder in get_finders():
        result = finder.find(path)
        if result:
            return result
