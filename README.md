# django-sass-processor

Processor to compile files from markup languages such as SASS/SCSS.

**django-sass-processor** converts ``*.scss`` or ``*.sass`` files into ``*.css`` while rendering
templates. For performance reasons this is done only once, since the preprocessor keeps track on
the timestamps and only recompiles, if any of the imported SASS/SCSS files is younger than the
corresponding generated CSS file.


## Introduction

This Django app provides a templatetag ``{% sass_src 'path/to/file.scss' %}``, which can be used
instead of the built-in templatetag ``static``. Since version 0.3.4 this also works for Jinja2
templates.

If SASS/SCSS files shall be referenced through the ``Media`` class, or ``media`` property, the SASS
processor can be used directly.

Additionally, **django-sass-processor** is shipped with a management command, which can convert
the content of all occurrences inside the templatetag ``sass_src`` as an offline operation. Hence
the **libsass** compiler is not required in a production environment.

During development, a [sourcemap](https://developer.chrome.com/devtools/docs/css-preprocessors) is
generated along side with the compiled ``*.css`` file. This allows to debug style sheet errors much
easier.

With this tool, you can safely remove your Ruby installations "Compass" and "SASS" from your Django
projects. You neither need any directory "watching" daemons based on node.js.


## Project's Home

On GitHub:

https://github.com/jrief/django-sass-processor

Please use the issue tracker to report bugs or propose new features.


## Installation

```
pip install libsass django-compressor django-sass-processor
```

``django-compressor`` is required only for offline compilation, when using the command
``manage.py compilescss``.

``libsass`` is not required on the production environment, if SASS/SCSS files have been precompiled
and deployed using offline compilation.


## Configuration

In ``settings.py`` add to:

```python
INSTALLED_APPS = (
    ...
    'sass_processor',
    ...
)
```

Optionally, add a list of additional search paths, the SASS compiler may examine when using the
``@import "...";`` statement in SASS/SCSS files:

```python
import os

SASS_PROCESSOR_INCLUDE_DIRS = (
    os.path.join(PROJECT_PATH, 'mystyles/scss'),
    os.path.join(PROJECT_PATH, 'node_modules'),
)
```

During development, or when ``SASS_PROCESSOR_ENABLED`` is set to ``True``, the compiled file is
placed into the folder referenced by ``SASS_PROCESSOR_ROOT`` (if unset, this setting defaults to
``STATIC_ROOT``). Having a location outside of the working directory prevents to pollute your local
``static/css/...`` folders with auto-generated files. Therefore assure, that this directory is
writable by the Django runserver.

**django-sass-processor** is shipped with a special finder, to locate the generated ``*.css`` files
in the folder referred by ``SASS_PROCESSOR_ROOT`` (or, if unset ``STATIC_ROOT``). Just add it to
your ``settings.py``. If there is no ``STATICFILES_FINDERS`` setting in your ``settings.py`` don't
forget to include **django** [default finders](https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-STATICFILES_FINDERS).

```
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
    ...
)
```

You may fine tune sass compiler parameters in your `settings.py`.

Integer `SASS_PRECISION` sets floating point precision for output css. libsass'
default is ``5``. Note: **bootstrap-sass** requires ``8``, otherwise various
layout problems _will_ occur.
```
SASS_PRECISION = 8
```

`SASS_OUTPUT_STYLE` sets coding style of the compiled result, one of ``compact``,
``compressed``, ``expanded``, or ``nested``. Default is ``nested`` for ``DEBUG``
and ``compressed`` in production.

Note: **libsass-python** 0.8.3 has [problem encoding result while saving on
Windows](https://github.com/dahlia/libsass-python/pull/82), the issue is already
fixed and will be included in future `pip` package release, in the meanwhile
avoid ``compressed`` output style.
```
SASS_OUTPUT_STYLE = 'compact'
```

### Jinja2 support

`sass_processor.jinja2.ext.SassSrc` is a Jinja2 extension. Add it to your Jinja2 environment to enable the tag `sass_src`, there is no need for a `load` tag. Example of how to add your Jinja2 environment to Django:

In `settings.py`:
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'yourapp.jinja2.environment'
        }
    }
]
```

Make sure to still add the default template backend if you're still using Django templates elsewhere.
This is covered in the [upgrading to 1.8 documentation](https://docs.djangoproject.com/en/1.9/ref/templates/upgrading/).

In `yourapp/jinja2.py`:
```python
from jinja2 import Environment


def environment(**kwargs):
    extensions = [] if 'extensions' not in kwargs else kwargs['extensions']
    extensions.append('sass_processor.jinja2.ext.SassSrc')
    kwargs['extensions'] = extensions

    return Environment(**kwargs)
```

## Usage

### In your Django templates

```html
{% load sass_tags %}

<link href="{% sass_src 'myapp/css/mystyle.scss' %}" rel="stylesheet" type="text/css" />
```

The above template code will be render as HTML such as
``<link href="/static/myapp/css/mystyle.css" rel="stylesheet" type="text/css" />``

You can safely use this templatetag inside a Sekizai's ``{% addtoblock "css" %}`` statement.


### In Media classes or properties

In Python code, you can access the API of the SASS processor directly. This for instance is useful
in Django's admin or form framework.

```python
from sass_processor import SassProcessor

sass_processor = SassProcessor()

class SomeAdminOrFormClass(...):
    ...
    class Media:
         css = {
            'all': (sass_processor('myapp/css/mystyle.scss'),)
        }
```

This feature is available since version 0.4.0.


## Offline compilation

If you want to precompile all occurrences of your SASS/SCSS files for the whole project, on the
command line invoke:

```
./manage.py compilescss
```

This is useful for preparing production environments, where SASS/SCSS files can't be compiled on
the fly. To simplify the deployment, the compiled ``*.css`` files are stored side-by-side with their
corresponding SASS/SCSS files; just run ``./manage.py collectstatic`` afterwards. In case you
don't want to expose the SASS/SCSS files in a production environment, deploy with
``./manage.py collectstatic --ignore=.scss``.

In case you want to get rid of the compiled ``*.css`` files in your local static directories, simply
reverse the above command:

```
./manage.py compilescss --delete-files
```
This will remove all occurrences of previously generated ``*.css`` files.

Or you may direct compile results to the ``SASS_PROCESSOR_ROOT`` directory (if not specified - to
``STATIC_ROOT``):

```
./manage.py compilescss --use-processor-root
```
Combine with ``--delete-files`` switch to purge results from there.

If you use an alternative templating engine (django 1.8+) set its name in ``--engine`` argument.
``django`` and ``jinja2`` is supported, see
[django-compressor documentation](http://django-compressor.readthedocs.org/en/latest/) on how to
set up ``COMPRESS_JINJA2_GET_ENVIRONMENT`` to configure jinja2 engine support.


### Alternative templates

By default, **django-sass-processor** will locate SASS/SCSS files from .html templates,
but you can extend or override this behavior. Just use the following syntax in ``settings.py``:

```
SASS_TEMPLATE_EXTS = ['.html','.jade']
```


## Configure SASS variables through settings.py

In SASS, a nasty problem is to set the correct include paths for icons and fonts. Normally this is
done through a ``_variables.scss`` file, but this inhibits a configuration through your projects
``settings.py``.

To avoid the need for duplicate configuration settings, **django-sass-processor** offers a SASS
function to fetch any arbitrary configuration from the project's ``settings.py``. This is specially
handy for setting the include path of your Glyphicons font directory. Assume you installed Bootstrap
SASS files using

```npm install bootstrap-sass```

then locate your ``node_modules`` folder and add it to your ``settings.py``, so that your fonts are
accessible through the Django's ``django.contrib.staticfiles.finders.FileSystemFinder``:

```
STATICFILES_DIRS = (
    ...
    ('node_modules', '/path/to/your/project/node_modules/'),
    ...
)

NODE_MODULES_URL = STATIC_URL + 'node_modules/'

```

With the SASS function ``get-setting``, you now can override any SASS variable with a configurable
value. For the Glyphicons font search path, add this to your ``_variables.scss``:

```
$icon-font-path: unquote(get-setting(NODE_MODULES_URL) + "bootstrap-sass/assets/fonts/bootstrap/");
```

and ``@import "variables";`` whenever you need Glyphicons. You then can safely remove any
font references, such as ``<link href="/path/to/your/fonts/bootstrap/glyphicons-whatever.ttf" ...>``
from you HTML templates.


## Changelog

* 0.4.0
- Refactored the sass processor into a self-contained class ``SassProcessor``, which can be accessed
  through an API, the Jinja2 template engine and the existing templatetag.

* 0.3.5
 - Added Jinja2 support, see [Jinja2 support](#jinja2-support).

* 0.3.4
 - Fixed: ``get_template_sources()`` in Django-1.9 returns Objects rather than strings.
 - In command, use ``ArgumentParser`` rather than ``OptionParser``.

* 0.3.1...0.3.3
 - Changed the build process in ``setup.py``.

* 0.3.0
 - Compatible with Django 1.8+.
 - bootstrap3-sass ready: appropriate floating point precision (8) can be set in ``settings.py``.
 - Offline compilation results may optionally be stored in ``SASS_PROCESSOR_ROOT``.

* 0.2.6
 - Hotfix: added SASS function ``get-setting`` also to offline compiler.

* 0.2.5
 - Compatible with Python3
 - Replaced ``SortedDict`` with ``OrderedDict`` to be prepared for Django-1.9
 - Raise a ``TemplateSyntax`` error, if a SASS ``@include "..."`` fails to find the file.
 - Added SASS function ``get-setting`` to fetch configuration directives from ``settings.py``.

* 0.2.4
 - Forcing compiled unicode to bytes, since 'Font Awesome' uses Unicode Private Use Area (PUA)
   and hence implicit conversion on ``fh.write()`` failed.

* 0.2.3
 - Allow for setting template extensions and output style.
 - Force Django to calculate template_source_loaders from TEMPLATE_LOADERS settings, by asking to find a dummy template.

* 0.2.0
 - Removed dependency to **django-sekizai** and **django-classy-tags**. It now can operate in
   stand-alone mode. Therefore the project has been renamed to **django-sass-processor**.

* 0.1.0
 - Initial revision named **django-sekizai-processors**, based on a preprocessor for the Sekizai
   template tags ``{% addtoblock %}``.
