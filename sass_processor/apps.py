import re
import os
from django.apps import apps, AppConfig
from django.conf import settings
from django.contrib.staticfiles.finders import AppDirectoriesFinder


APPS_INCLUDE_DIRS = []

class SassProcessorConfig(AppConfig):
    name = 'sass_processor'
    verbose_name = "Sass Processor"
    auto_include = getattr(settings, 'SASS_PROCESSOR_AUTO_INCLUDE', True)
    _pattern = re.compile(getattr(settings, 'SASS_PROCESSOR_INCLUDE_FILE_PATTERN', r'^_.+\.(scss|sass)$'))

    def ready(self):
        if self.auto_include:
            app_configs = apps.get_app_configs()
            for app_config in app_configs:
                static_dir = os.path.join(app_config.path, AppDirectoriesFinder.source_dir)
                if os.path.isdir(static_dir):
                    self.traverse_tree(static_dir)

    @classmethod
    def traverse_tree(cls, static_dir):
        """traverse the static folders an look for at least one file ending in .scss/.sass"""
        for root, dirs, files in os.walk(static_dir):
            for filename in files:
                if cls._pattern.match(filename):
                    APPS_INCLUDE_DIRS.append(static_dir)
                    return
