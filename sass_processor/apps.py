from pathlib import Path

from django.apps import apps, AppConfig
from django.conf import settings
from django.contrib.staticfiles.finders import AppDirectoriesFinder
from django.core.files.storage import get_storage_class


APPS_INCLUDE_DIRS = []

class SassProcessorConfig(AppConfig):
    name = 'sass_processor'
    verbose_name = "Sass Processor"
    auto_include = getattr(settings, 'SASS_PROCESSOR_AUTO_INCLUDE', True)
    _storage = get_storage_class(import_path=settings.STATICFILES_STORAGE)()
    _pattern = getattr(settings, 'SASS_PROCESSOR_INCLUDE_FILE_PATTERN', '*.s[ac]ss')

    def ready(self):
        if self.auto_include:
            app_configs = apps.get_app_configs()
            for app_config in app_configs:
                static_dir = Path(app_config.path) / AppDirectoriesFinder.source_dir
                if static_dir.is_dir():
                    if static_dir.rglob(self._pattern):
                        APPS_INCLUDE_DIRS.append(static_dir)
