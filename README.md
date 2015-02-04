# django-sekizai-processors

Processors to compile files from markup languages such as SASS/SCSS, using the ``preprocessor``
option on Sekizai's templatetag ``addtoblock``. In the future other markup languages and the
``postprocessor`` option for Sekizai's templatetag  ``render_block`` will also be supported.

Additionally, **django-sekizai-processors** is shipped with a management command, which can convert
the content of all occurrences inside the templatetag ``addtoblock`` as an offline operation. Hence
the **libsass** compiler is not required in a production environment.

During development, a [sourcemap](https://developer.chrome.com/devtools/docs/css-preprocessors) is
generated along side with the compiled ``*.css`` file. This allows to debug style sheet errors much
easier.

By using this preprocessor, you can safely remove your Ruby projects “Compass” and “SASS”.

## Installation

```
pip install libsass django-sekizai django-sekizai-processors django-compressor
```

If using offline compilation, ``libsass`` is not required on the production environment.

In ``settings.py``:

```python
INSTALLED_APPS = (
    ...
    'sekizai',
    'sekizai_processors',
    ...
)
```

Optionally, add a list of additional search pathes, the SASS compiler may examine when using the
``@import "...";`` tag in SASS files:

```python
import os

SEKIZAI_PROCESSOR_INCLUDE_DIRS = (
    os.path.join(PROJECT_PATH, 'styles/scss'),
    os.path.join(PROJECT_PATH, 'node_modules/compass-mixins/lib'),
    os.path.join(PROJECT_PATH, 'node_modules/bootstrap-sass/assets/stylesheets'),
)
```

Annotation: For this example, you are encouraged to install the dependencies for Compass and/or
Bootstrap-SASS, using ``npm install compass-mixins bootstrap-sass``.

During development, the compiled file is placed into the ``STATIC_ROOT`` folder in order to not
pollute your local ``static/css/...`` folders with auto-generated files.
Therefore assure, that in ``settings.py``, ``STATIC_ROOT`` points to an writable directory.

Since **django-sekizai-processors** depends on **django-compressor**, just add the
``CompressorFinder`` to your ``settings.py``: 

```
STATICFILES_FINDERS = (
    ...
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
```

In the future this addtional dependency will be removed.

## Preprocessing SASS

**django-sekizai-processors** is shipped with a built-in preprocessor to convert
``*.scss`` or ``*.sass`` files into ``*.css`` while rendering the template. For performance reasons
this is done only once, but the preprocessor keeps track on the timestamps and recompiles only, if
any of the imported SASS files is younger than the corresponding generated CSS file.


### In your Django templates

```html
{% load sekizai_tags %}

{% addtoblock "css" preprocessor "sekizai_processors.sass_preprocessor.compilescss" %}<link href="{% static 'myapp/css/mystyle.scss' %}" rel="stylesheet" type="text/css" />{% endaddtoblock %}
```

## Offline compilation

If you want to precompile all occurences of your SASS files, on the command line invoke:

```
./manage.py compilescss
```

This is useful for production environments, where SASS files can't be compiled on the fly. To
simplify the deployment, the compiled ``*.css`` files are stored side-by-side with their
corresponding ``*.scss`` files; just run ``./manage.py collectstatic`` the usual way. In case you
don't want to expose the ``*.scss`` files in a production environment, deploy with
``./manage.py collectstatic --ignore=.scss``.
