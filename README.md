# django-sass-processor

Processors to compile files from markup languages such as SASS/SCSS, if referenced by the special
templatetag ``sass_src``, which behavies similar to the built-in tag ``static``.

Additionally, **django-sass-processors** is shipped with a management command, which can convert
the content of all occurrences inside the templatetag ``sass_src`` as an offline operation. Hence
the **libsass** compiler is not required in a production environment.

During development, a [sourcemap](https://developer.chrome.com/devtools/docs/css-preprocessors) is
generated along side with the compiled ``*.css`` file. This allows to debug style sheet errors much
easier.

With this tool, you can safely remove your Ruby projects “Compass” and “SASS”.

## Installation

```
pip install libsass django-compressor django-sass-processor
```

``django-compressor`` is required only for offline compilation, when using the command
``manage.py compilescss``

``libsass`` is not required on the production environment, ff SASS/SCSS files have been precompiled
and deployed using offline compilation.

## Configuration

In ``settings.py``:

```python
INSTALLED_APPS = (
    ...
    'sass_processors',
    ...
)
```

Optionally, add a list of additional search pathes, the SASS compiler may examine when using the
``@import "...";`` tag in SASS files:

```python
import os

SASS_PROCESSOR_INCLUDE_DIRS = (
    os.path.join(PROJECT_PATH, 'styles/scss'),
    os.path.join(PROJECT_PATH, 'node_modules'),
)
```

During development, the compiled file is placed into the folder referenced by ``SASS_PROCESSOR_ROOT``.
If unset, this setting defaults to ``STATIC_ROOT``. It prevents to pollute your local
``static/css/...`` folders with auto-generated files.
Therefore assure, that in ``settings.py``, ``SASS_PROCESSOR_ROOT`` (or, if unset ``STATIC_ROOT``)
points onto an writable directory.

During development, assure that generated ``*.css`` can be found in the folder referred by
``SASS_PROCESSOR_ROOT``. Therefore **django-sass-processor** is shipped with a special finder for
that purpose, just add it to your ``settings.py``: 

```
STATICFILES_FINDERS = (
    ...
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
    ...
)
```

## Preprocessing SASS

**django-sass-processor** is shipped with a built-in preprocessor to convert ``*.scss`` or
``*.sass`` files into ``*.css`` while rendering the template. For performance reasons
this is done only once, but the preprocessor keeps track on the timestamps and recompiles only, if
any of the imported SASS/SCSS files is younger than the corresponding generated CSS file.


### In your Django templates

```html
{% load sass_tags %}

<link href="{% sass_src 'myapp/css/mystyle.scss' %}" rel="stylesheet" type="text/css" />
```

## Offline compilation

If you want to precompile all occurences of your SASS/SCSS files, on the command line invoke:

```
./manage.py compilescss
```

This is useful for preparing production environments, where SASS/SCSS files can't be compiled on
the fly. To simplify the deployment, the compiled ``*.css`` files are stored side-by-side with their
corresponding SASS/SCSS files; just run ``./manage.py collectstatic`` the usual way. In case you
don't want to expose the SASS/SCSS files in a production environment, deploy with
``./manage.py collectstatic --ignore=.scss``.

In case you want to get rid of the compiled ``*.css`` files in your static directories, simply
reverse the above command:

```
./manage.py compilescss --delete-files
```

will remove all occurrences of previously generated ``*.css`` files.
