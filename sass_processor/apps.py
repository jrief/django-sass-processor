# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.apps import apps, AppConfig
from django.conf import settings
from django.core.files.storage import get_storage_class


APPS_INCLUDE_DIRS = []

class SassProcessorConfig(AppConfig):
    name = 'sass_processor'
    verbose_name = "Sass Processor"
    _sass_exts = ('.scss', '.sass')
    _storage = get_storage_class(import_path=settings.STATICFILES_STORAGE)()

    def ready(self):
        app_configs = apps.get_app_configs()
        for app_config in app_configs:
            static_dir = os.path.join(app_config.path, self._storage.base_url.strip(os.path.sep))
            if os.path.isdir(static_dir):
                self.traverse_tree(static_dir)

    @classmethod
    def traverse_tree(cls, static_dir):
        """traverse the static folders an look for at least one file ending in .scss/.sass"""
        for root, dirs, files in os.walk(static_dir):
            for filename in files:
                basename, ext = os.path.splitext(filename)
                if basename.startswith('_') and ext in cls._sass_exts:
                    APPS_INCLUDE_DIRS.append(static_dir)
                    return
