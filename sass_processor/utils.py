# -*- coding: utf-8 -*-
import inspect
from django.conf import settings
from django.template import TemplateSyntaxError
from django.utils import six
from django.utils.module_loading import import_string

try:
    import sass
except ImportError:
    sass = None


def get_custom_functions():
    """
    Return a dict of function names, to be used from inside SASS
    """
    def get_setting(*args):
        try:
            return getattr(settings, args[0])
        except AttributeError as e:
            raise TemplateSyntaxError(str(e))

    if hasattr(get_custom_functions, '_custom_functions'):
        return get_custom_functions._custom_functions
    get_custom_functions._custom_functions = {sass.SassFunction('get-setting', ('key',), get_setting)}
    for name, func in getattr(settings, 'SASS_PROCESSOR_CUSTOM_FUNCTIONS', {}).items():
        try:
            if isinstance(func, six.string_types):
                func = import_string(func)
        except Exception as e:
            raise TemplateSyntaxError(str(e))
        else:
            if not inspect.isfunction(func):
                raise TemplateSyntaxError("{} is not a Python function".format(func))
            if six.PY2:
                func_args = inspect.getargspec(func).args
            else:
                func_args = inspect.getfullargspec(func).args
            sass_func = sass.SassFunction(name, func_args, func)
            get_custom_functions._custom_functions.add(sass_func)
    return get_custom_functions._custom_functions
