# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import TemplateSyntaxError


def get_setting(key):
    try:
        return getattr(settings, key)
    except AttributeError as e:
        raise TemplateSyntaxError(e.message)
