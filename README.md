# django-sass-processor

Annoyed having to run a Compass, Grunt or Gulp daemon while developing Django projects?

Well, then this app is for you! Compile SASS/SCSS files on the fly without having to manage
third party services nor special IDE plugins.

[![Build Status](https://travis-ci.org/jrief/django-sass-processor.svg)](https://travis-ci.org/jrief/django-sass-processor)
[![PyPI](https://img.shields.io/pypi/pyversions/django-sass-processor.svg)]()
[![PyPI version](https://img.shields.io/pypi/v/django-sass-processor.svg)](https://pypi.python.org/pypi/django-sass-processor)
[![PyPI](https://img.shields.io/pypi/l/django-sass-processor.svg)]()
[![Downloads](https://img.shields.io/pypi/dm/django-sass-processor.svg)](https://pypi.python.org/pypi/django-sass-processor)
[![Twitter Follow](https://img.shields.io/twitter/follow/shields_io.svg?style=social&label=Follow&maxAge=2592000)](https://twitter.com/jacobrief)

**Version 0.7.5 will be the latest version to support Python-2.7** 

The master branch of **django-sass-processor** already supports Django-3.0. However,
[django-compressor](https://django-compressor.readthedocs.io/en/stable/) (which it depends on)
[does not yet support Django-3.0](https://github.com/django-compressor/django-compressor/issues/980),
hence I have to wait until a new version of django-compressor is available on PyPI.
Until then, please use the master branch if you need Django-3.0.


## Other good reasons for using this library

* Refer SASS/SCSS files directly from your sources, instead of referring a compiled CSS file,
having to rely on another utility which creates them from SASS/SCSS files, hidden in
your source tree.
* Use Django's `settings.py` for the configuration of paths, box sizes etc., instead of having another
SCSS specific file (typically `_variables.scss`), to hold these.
* Extend your SASS functions by calling Python functions directly out of your Django project.
* View SCSS errors directly in the debug console of your Django's development server.

**django-sass-processor** converts `*.scss` or `*.sass` files into `*.css` while rendering
templates. For performance reasons this is done only once, since the preprocessor keeps track on
the timestamps and only recompiles, if any of the imported SASS/SCSS files is younger than the
corresponding generated CSS file.

## Introduction

This Django app provides a templatetag `{% sass_src 'path/to/file.scss' %}`, which can be used
instead of the built-in templatetag `static`. This templatetag also works inside Jinja2 templates.

If SASS/SCSS files shall be referenced through the `Media` class, or `media` property, the SASS
processor can be used directly.

Additionally, **django-sass-processor** is shipped with a management command, which can convert
the content of all occurrences inside the templatetag `sass_src` as an offline operation. Hence
the **libsass** compiler is not required in a production environment.

During development, a [sourcemap](https://developer.chrome.com/devtools/docs/css-preprocessors) is
generated along side with the compiled `*.css` file. This allows to debug style sheet errors much
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

`django-compressor` is required only for offline compilation, when using the command
`manage.py compilescss`.

`libsass` is not required on the production environment, if SASS/SCSS files have been precompiled
and deployed using offline compilation.

## Configuration

In `settings.py` add to:

```python
INSTALLED_APPS = [
    ...
    'sass_processor',
    ...
]
```

**django-sass-processor** is shipped with a special finder, to locate the generated `*.css` files
in the directory referred by `SASS_PROCESSOR_ROOT` (or, if unset `STATIC_ROOT`). Just add it to
your `settings.py`. If there is no `STATICFILES_FINDERS` in your `settings.py` don't forget
to include the **Django** [default finders](https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-STATICFILES_FINDERS).

If the directory referred by `SASS_PROCESSOR_ROOT` does not exist, then **django-sass-processor**
creates it. This does not apply, if `SASS_PROCESSOR_ROOT` is unset and hence defaults to
`STATIC_ROOT`. Therefore it is a good idea to otherwise use `SASS_PROCESSOR_ROOT = STATIC_ROOT`
in your `settings.py`.

```python
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
    ...
]
```

Optionally, add a list of additional search paths, the SASS compiler may examine when using the
`@import "...";` statement in SASS/SCSS files:

```python
import os

SASS_PROCESSOR_INCLUDE_DIRS = [
    os.path.join(PROJECT_PATH, 'extra-styles/scss'),
    os.path.join(PROJECT_PATH, 'node_modules'),
]
```

Additionally, **django-sass-processor** will traverse all installed Django apps (`INSTALLED_APPS`)
and look into their static folders. If any of them contain a file matching the regular expression
pattern `^_.+\.(scss|sass)$` (read: filename starts with an underscore and is of type `scss` or
`sass`), then that app specific static folder is added to the **libsass** include dirs. This
feature can be disabled in your settings with:

```python
SASS_PROCESSOR_AUTO_INCLUDE = False
```

If inside of your SASS/SCSS files, you also want to import (using `@import "path/to/scssfile";`)
files which do not start with an underscore, then you can configure another Regex pattern in your
settings, for instance:

```python
SASS_PROCESSOR_INCLUDE_FILE_PATTERN = r'^.+\.scss$'
```

will look for all files of type `scss`. Remember that SASS/SCSS files which start with an
underscore, are intended to be imported by other SASS/SCSS files, while files starting with a
letter or number are intended to be included by the HTML tag
`<link href="{% sass_src 'path/to/file.scss' %}" ...>`.

During development, or when `SASS_PROCESSOR_ENABLED = True`, the compiled file is placed into the
folder referenced by `SASS_PROCESSOR_ROOT` (if unset, this setting defaults to `STATIC_ROOT`).
Having a location outside of the working directory prevents to pollute your local `static/css/...`
directories with auto-generated files. Therefore assure, that this directory is writable by the
Django runserver.


#### Fine tune SASS compiler parameters in `settings.py`.

Integer `SASS_PRECISION` sets floating point precision for output css. libsass'
default is `5`. Note: **bootstrap-sass** requires `8`, otherwise various
layout problems _will_ occur.

```python
SASS_PRECISION = 8
```

`SASS_OUTPUT_STYLE` sets coding style of the compiled result, one of `compact`,
`compressed`, `expanded`, or `nested`. Default is `nested` for `DEBUG`
and `compressed` in production.

Note: **libsass-python** 0.8.3 has [problem encoding result while saving on
Windows](https://github.com/dahlia/libsass-python/pull/82), the issue is already
fixed and will be included in future `pip` package release, in the meanwhile
avoid `compressed` output style.

```python
SASS_OUTPUT_STYLE = 'compact'
```

### Jinja2 support

`sass_processor.jinja2.ext.SassSrc` is a Jinja2 extension. Add it to your Jinja2 environment to enable the tag `sass_src`, there is no need for a `load` tag. Example of how to add your Jinja2 environment to Django:

In `settings.py`:

```python
TEMPLATES = [{
    'BACKEND': 'django.template.backends.jinja2.Jinja2',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'environment': 'yourapp.jinja2.environment'
    },
    ...
}]
```

Make sure to add the default template backend, if you're still using Django templates elsewhere.
This is covered in the [Upgrading templates documentation](https://docs.djangoproject.com/en/stable/ref/templates/upgrading/).

In `yourapp/jinja2.py`:

```python
# Include this for Python 2.
from __future__ import absolute_import

from jinja2 import Environment


def environment(**kwargs):
    extensions = [] if 'extensions' not in kwargs else kwargs['extensions']
    extensions.append('sass_processor.jinja2.ext.SassSrc')
    kwargs['extensions'] = extensions

    return Environment(**kwargs)
```

If you want to make use of the `compilescss` command, then you will also have to add the following to your settings:

```python
from yourapp.jinja2 import environment

COMPRESS_JINJA2_GET_ENVIRONMENT = environment
```

## Usage

### In your Django templates

```django
{% load sass_tags %}

<link href="{% sass_src 'myapp/css/mystyle.scss' %}" rel="stylesheet" type="text/css" />
```

The above template code will be rendered as HTML

```html
<link href="/static/myapp/css/mystyle.css" rel="stylesheet" type="text/css" />
```

You can safely use this templatetag inside a [Sekizai](https://django-sekizai.readthedocs.io/)'s
`{% addtoblock "css" %}` statement.

### In Media classes or properties

In Python code, you can access the API of the SASS processor directly. This for instance is useful
in Django's admin or form framework.

```python
from sass_processor.processor import sass_processor

class SomeAdminOrFormClass(...):
    ...
    class Media:
        css = {
            'all': [sass_processor('myapp/css/mystyle.scss')],
        }
```

## Add vendor prefixes to CSS rules using values from https://caniuse.com/

Writing SCSS shall be fast and easy and you should not have to care, whether to add vendor specific
prefixes to your CSS directives. Unfortunately there is no pure Python package to solve this, but
with a few node modules, we can add this to our process chain.

As superuser install

```shell
npm install -g npx
```

and inside your project root, install

```shell
npm install postcss-cli autoprefixer
```

Check that the path of `node_modules` corresponds to its entry in the settings directive
`STATICFILES_DIRS` (see below).

In case `npx` can not be found in your system path, use the settings directive
`NODE_NPX_PATH = /path/to/npx` to point to that executable.

If everything is setup correctly, **django-sass-processor** adds all required vendor prefixes to
the compiled CSS files. For further information, refer to the
[Autoprefixer](https://github.com/postcss/autoprefixer) package.

To disable autoprefixing, set `NODE_NPX_PATH = None`.

**Important note**: If `npx` is installed, but `postcss` and/or `autoprefixer` are missing
in the local `node_modules`, setting `NODE_NPX_PATH` to `None` is manadatory, otherwise
**django-sass-processor** does not know how to postprocess the generated CSS files.

## Offline compilation

If you want to precompile all occurrences of your SASS/SCSS files for the whole project, on the
command line invoke:

```shell
./manage.py compilescss
```

This is useful for preparing production environments, where SASS/SCSS files can't be compiled on
the fly.

To simplify the deployment, the compiled `*.css` files are stored side-by-side with their
corresponding SASS/SCSS files. After compiling the files run

```shell
./manage.py collectstatic
```

as you would in a normal deployment.

In case you don't want to expose the SASS/SCSS files in a production environment,
deploy with:

```shell
./manage.py collectstatic --ignore=*.scss
```

To get rid of the compiled `*.css` files in your local static directories, simply reverse the
above command:

```shell
./manage.py compilescss --delete-files
```

This will remove all occurrences of previously generated `*.css` files.

Or you may compile results to the `SASS_PROCESSOR_ROOT` directory directy (if not specified - to
`STATIC_ROOT`):

```shell
./manage.py compilescss --use-processor-root
```

Combine with `--delete-files` switch to purge results from there.

If you use an alternative templating engine set its name in `--engine` argument. Currently
`django` and `jinja2` are supported, see
[django-compressor documentation](http://django-compressor.readthedocs.org/en/latest/) on how to
set up `COMPRESS_JINJA2_GET_ENVIRONMENT` to configure jinja2 engine support.

During offline compilation **django-sass-processor** parses all Python files and looks for
invocations of `sass_processor('path/to/sassfile.scss')`. Therefore the string specifying
the filename must be hard coded and shall not be concatenated or being somehow generated.

### Alternative templates

By default, **django-sass-processor** will locate SASS/SCSS files from .html templates,
but you can extend or override this behavior in your settings with:

```python
SASS_TEMPLATE_EXTS = ['.html','.jade']
```

## Configure SASS variables through settings.py

In SASS, a nasty problem is to set the correct include paths for icons and fonts. Normally this is
done through a `_variables.scss` file, but this inhibits a configuration through your projects
`settings.py`.

To avoid the need for duplicate configuration settings, **django-sass-processor** offers a SASS
function to fetch any arbitrary configuration directive from the project's `settings.py`. This
is specially handy to set the include path of your Glyphicons font directory. Assume, Bootstrap-SASS
has been installed using:

```shell
npm install bootstrap-sass
```

then locate the directory named `node_modules` and add it to your settings, so that your fonts are
accessible through the Django's `django.contrib.staticfiles.finders.FileSystemFinder`:

```python
STATICFILES_DIRS = [
    ...
    ('node_modules', '/path/to/your/project/node_modules/'),
    ...
]

NODE_MODULES_URL = STATIC_URL + 'node_modules/'
```

With the SASS function `get-setting`, it is possible to override any SASS variable with a value
configured in the project's `settings.py`. For the Glyphicons font search path, add this to your
`_variables.scss`:

```scss
$icon-font-path: unquote(get-setting(NODE_MODULES_URL) + "bootstrap-sass/assets/fonts/bootstrap/");
```

and `@import "variables";` whenever you need Glyphicons. You then can safely remove any font
references, such as `<link href="/path/to/your/fonts/bootstrap/glyphicons-whatever.ttf" ...>`
from you HTML templates.


### Configure SASS variables through Python functions

It is even possible to call Python functions from inside any module. Do this by adding
`SASS_PROCESSOR_CUSTOM_FUNCTIONS` to the project's `settings.py`. This shall contain a mapping
of SASS function names pointing to a Python function name.

Example:

```python
SASS_PROCESSOR_CUSTOM_FUNCTIONS = {
    'get-color': 'myproject.utils.get_color',
}
```

This allows to invoke Python functions out of any `*.scss` file. 

```scss
$color: get-color(250, 10, 120);
```

Here we pass the parameters '250, 10, 120' into the function `def get_color(red, green, blue)`
in Python module `myproject.utils`. Note that this function receives the values as `sass.Number`,
hence extract values using `red.value`, etc.

If one of these customoized functions returns a value, which is not a string, then convert it
either to a Python string or to a value of type `sass.SassNumber`. For other types, refer to their
documentation.

Such customized functions must accept parameters explicilty, otherwise `sass_processor` does not
know how to map them. Variable argument lists therefore can not be used.


## Serving static files with S3

A custom Storage class is provided for use if your deployment serves css files out of S3. You must have Boto 3 installed. To use it, add this to your settings file:
```
STATICFILES_STORAGE = 'sass_processor.storage.SassS3Boto3Storage'
```


## Heroku

If you are deploying to [Heroku](https://www.heroku.com/), use the [heroku-buildpack-django-sass](https://elements.heroku.com/buildpacks/drpancake/heroku-buildpack-django-sass) buildpack to automatically compile scss for you.


## Development

To run the tests locally, clone the repository, create a new virtualenv, activate it and then run
these commands:

```shell
cd django-sass-processor
pip install tox
tox
```
