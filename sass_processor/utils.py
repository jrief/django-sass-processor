# -*- coding: utf-8 -*-
from decimal import Decimal
from django.conf import settings
from django.template import TemplateSyntaxError
from django.utils.module_loading import import_string

try:
    import sass
except ImportError:
    sass = None


def get_setting(*args):
    try:
        return getattr(settings, args[0])
    except AttributeError as e:
        raise TemplateSyntaxError(e.message)


def python_call(*args):
    try:
        func = import_string(args[0])
        result = func(*args[1:])
        if isinstance(result, (int, float, Decimal)):
            return sass.SassNumber(result, type(result).__name__.encode())
        return result
    except Exception as e:
        raise TemplateSyntaxError(str(e))


# add a function to be used from inside SASS
custom_functions = {
    sass.SassFunction('get-setting', ('key',), get_setting),
    sass.SassFunction('python-call0', ('callable',), python_call),
    sass.SassFunction('python-call1', ('callable', 'a'), python_call),
    sass.SassFunction('python-call2', ('callable', 'a', 'b'), python_call),
    sass.SassFunction('python-call3', ('callable', 'a', 'b', 'c'), python_call),
}
