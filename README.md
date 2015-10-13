# django-sass-processor

Processor to compile files from markup languages such as SASS/SCSS, if referenced using the
templatetag ``{% sass_src 'path/to/file.scss' %}``. This special templatetag can be used instead of
the built-in tag ``static``.

Additionally, **django-sass-processor** is shipped with a management command, which can convert
the content of all occurrences inside the templatetag ``sass_src`` as an offline operation. Hence
the **libsass** compiler is not required in a production environment.

During development, a [sourcemap](https://developer.chrome.com/devtools/docs/css-preprocessors) is
generated along side with the compiled ``*.css`` file. This allows to debug style sheet errors much
easier.

With this tool, you can safely remove your Ruby installations “Compass” and “SASS” from your Django
projects.


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
your ``settings.py``: 

```
STATICFILES_FINDERS = (
    ...
    'sass_processor.finders.CssFinder',
    ...
)
```

## Preprocessing SASS

**django-sass-processor** is shipped with a built-in preprocessor to convert ``*.scss`` or
``*.sass`` files into ``*.css`` while rendering the template. For performance reasons
this is done only once, but the preprocessor keeps track on the timestamps and recompiles, if
any of the imported SASS/SCSS files is younger than the corresponding generated CSS file.


### In your Django templates

```html
{% load sass_tags %}

<link href="{% sass_src 'myapp/css/mystyle.scss' %}" rel="stylesheet" type="text/css" />
```

You can safely use this templatetag inside a Sekizai's ``{% addtoblock "css" %}`` statement.


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


## Configure SASS variables through settings.py

In SASS, a nasty problem is to set the correct include paths for icons and fonts. Normally this is
done through a ``_variables.scss`` file, but this inhibits a configuration through your projects
``settings.py``.

Starting with version 0.2.5 **django-sass-processor** offers a SASS function to fetch any arbitrary
configuration from ``settings.py``. This is specially handy for setting the include path of your
Glyphicons font directory. Assume you installed Bootstrap SASS files using
``npm install bootstrap-sass``, then locate your ``node_modules`` folder and add this to your
``settings.py``:

```
NODE_MODULES_PATH = '/path/to/your/projects/node_modules/'
```

Now you can override the any SASS variable with a configurable value. For the Glyphicons font search
path, add this to your ``_variables.scss``:

```
$icon-font-path: unquote(get-setting(NODE_MODULES_URL) + "bootstrap-sass/assets/fonts/bootstrap/");
```

and ``@import "variables";`` whenever you need Glyphicons. You then can safely remove any
font references, such as ``<link href="/path/to/your/fonts/bootstrap/glyphicons-whatever.ttf" ...>``
from you HTML templates.


## Changelog

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
