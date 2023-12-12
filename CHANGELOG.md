# Changes for django-sass-processor

- 1.4
* Drop support for Python 3.7.
* Add support for Python 3.12.
* Drop support for Django 4.0 and 4.1.
* Add support for Django 5.0.

- 1.3
* Add support for Django-4.2.
* Update settings for Django >= 4.2.* to use `STORAGES `, instead of `STATICFILES_STORAGE`.
* Remove usage of deprecated `get_storage_class` for Django >= 4.2.*.

- 1.2.2
* Revert regression introduced in version 1.1: Remove compatibility layer to support
  Django's `ManifestStaticFilesStorage`.

- 1.2.1
* In newer versions of Django `default_app_config`is deprecated.

- 1.2
* Stringify directory settings, since they might use Python's `pathlib.Path` class.
* Add support for Django-4.0.

- 1.1
* Add compatibility layer to support Django's `ManifestStaticFilesStorage`.

- 1.0.1
* Fix storage options for non-filesystem static storages (thanks to TheRandomDog for finding)
* Dev: Move to setup.cfg configuration

- 1.0.0
* Management command `compilescss` now uses the same storage as the template tags.
* Any storage can now be used as destination.
* Breaking change: The argument `--use-processor-root` to `compilescss` was replaced
  with `--use-storage`.
* Breaking change: `SassS3Boto3Storage` was removed. Use the `S3Boto3Storage` from
  django-storages directly.
* Breaking change: Suppor for Django <2.2 was dropped
* Dev: Migrated setup meta-data to setup.cfg
* Dev: Enabled tests on Python 3.9

- 0.8.2
* Fixes: Management command `find_sources` does not ignore `SASS_PROCESSOR_AUTO_INCLUDE`.

- 0.8.1
* Add support for Django-3.1.

- 0.8
* Add support for Django-3.0.
* Drop support for Python<3.

- 0.7.5
* Latest version to support Python-2.7. Tested with Django-1.9, Django-1.10, Django-1.11, Django-2.0
  Django-2.1 and Django-2.2 using Python-3.5...3.7.

- 0.7.4
* Prevent the warnings about `Found another file with the destination path ...`, while
  running `./manage.py collectstatic`.

- 0.7.3
* In managment command `compilescss`, also catch `IndentionError` of parsed files.

- 0.7.2
* Prevent empty content when using autoprefixer.

* Source Map is now using relative paths. This fixes the path naming problems on Windows platforms.
- 0.7.1

* Source Map is now using relative paths. This fixes the path naming problems on Windows platforms.


- 0.7

* Allow to call directly into Python functions.

- 0.6

* Add autoprefixing via external postcss.

- 0.5.8

* _Potentially Breaking_: `libsass` is not autoinstalled as the dependency anymore.
* Add support for Django-2.0.

- 0.5.7

* Fixed: Catch exception if s3boto is not installed.

- 0.5.6

* Added compatibility layer to work with AWS S3 Storage.

- 0.5.5

* Create directory `SASS_PROCESSOR_ROOT` if it does not exist.

- 0.5.4

* Added unit tests and continuous integration to the project.

- 0.5.3

* Fixed compilescss: Did not find calls of sass_processor within a dict, list or tuple

- 0.5.2

* Fixed Python 3 incompatibility. Open files as binaries, since they may contain unicode characters.

- 0.5.1

* Add `APPS_INCLUDE_DIRS` to the SASS include path.

- 0.5.0

* SASS/SCSS files can also be referenced in pure Python files, for instance in `Media` class or
  `media` property definitions.
* The SASS processor will look for potential include directories, so that the `@import "..."`
  statement also works for SASS files located in other Django apps.

- 0.4.0 - 0.4.4

* Refactored the sass processor into a self-contained class `SassProcessor`, which can be accessed
  through an API, the Jinja2 template engine and the existing templatetag.

- 0.3.5

* Added Jinja2 support, see [Jinja2 support](#jinja2-support).

- 0.3.4

* Fixed: `get_template_sources()` in Django-1.9 returns Objects rather than strings.
* In command, use `ArgumentParser` rather than `OptionParser`.

- 0.3.1...0.3.3

* Changed the build process in `setup.py`.

- 0.3.0

* Compatible with Django 1.8+.
* bootstrap3-sass ready: appropriate floating point precision (8) can be set in `settings.py`.
* Offline compilation results may optionally be stored in `SASS_PROCESSOR_ROOT`.

- 0.2.6

* Hotfix: added SASS function `get-setting` also to offline compiler.

- 0.2.5

* Compatible with Python3
* Replaced `SortedDict` with `OrderedDict` to be prepared for Django-1.9
* Raise a `TemplateSyntax` error, if a SASS `@include "..."` fails to find the file.
* Added SASS function `get-setting` to fetch configuration directives from `settings.py`.

- 0.2.4

* Forcing compiled unicode to bytes, since 'Font Awesome' uses Unicode Private Use Area (PUA)
  and hence implicit conversion on `fh.write()` failed.

- 0.2.3

* Allow for setting template extensions and output style.
* Force Django to calculate template_source_loaders from TEMPLATE_LOADERS settings, by asking to find a dummy template.

- 0.2.0

* Removed dependency to **django-sekizai** and **django-classy-tags**. It now can operate in
  stand-alone mode. Therefore the project has been renamed to **django-sass-processor**.

- 0.1.0

* Initial revision named **django-sekizai-processors**, based on a preprocessor for the Sekizai
  template tags `{% addtoblock %}`.
