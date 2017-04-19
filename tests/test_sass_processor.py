# -*- coding: utf-8
from __future__ import unicode_literals

import os
import py
import shutil
from datetime import datetime
import calendar

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.template import Context
from django.template.loader import get_template


@override_settings(STATIC_ROOT=py.test.ensuretemp('static').strpath)
class SassProcessorTest(TestCase):
    def setUp(self):
        super(SassProcessorTest, self).setUp()
        try:
            os.mkdir(settings.STATIC_ROOT)
        except OSError:
            pass

    def tearDown(self):
        shutil.rmtree(settings.STATIC_ROOT)

    def test_sass_src(self):
        template = get_template('tests/main.html')
        context = Context({})
        css_file = template.render(context)
        self.assertEqual('/static/tests/css/main.css', css_file)
        css_file = os.path.join(settings.STATIC_ROOT, 'tests/css/main.css')
        self.assertTrue(os.path.exists(css_file))
        with open(css_file, 'r') as f:
            output = f.read()
        expected = "#main p{color:#00ff00;width:97%}#main p .redbox{background-color:#ff0000}#main p .redbox:hover{color:#000000}\n\n/*# sourceMappingURL=../../../../../../../../../static/tests/css/main.css.map */"
        self.assertEqual(expected, output)

        # check if compilation is skipped file for a second invocation of `sass_src`
        timestamp = os.path.getmtime(css_file)
        template.render(context)
        self.assertEqual(timestamp, os.path.getmtime(css_file))

        # removing `main.css.map` should trigger a recompilation
        os.remove(css_file + '.map')
        template.render(context)
        self.assertTrue(os.path.exists(css_file + '.map'))

        # if `main.scss` is newer than `main.css`, recompile everything
        longago = calendar.timegm(datetime(2017, 1, 1).timetuple())
        os.utime(css_file, (longago, longago))
        template.render(context)
        self.assertGreater(timestamp, os.path.getmtime(css_file))

    def test_sass_processor(self):
        from sass_processor.processor import sass_processor

        css_file = sass_processor('tests/css/bluebox.scss')
        self.assertEqual('/static/tests/css/bluebox.css', css_file)
        css_file = os.path.join(settings.STATIC_ROOT, 'tests/css/bluebox.css')
        self.assertTrue(os.path.exists(css_file))
        with open(css_file, 'r') as f:
            output = f.read()
        expected = '.bluebox{background-color:#0000ff}\n\n/*# sourceMappingURL=../../../../../../../../../static/tests/css/bluebox.css.map */'
        self.assertEqual(expected, output)

    @override_settings(DEBUG=False)
    def test_use_processor_root(self):
        call_command('compilescss', use_processor_root=True)
        css_file = os.path.join(settings.STATIC_ROOT, 'tests/css/main.css')
        self.assertTrue(os.path.exists(css_file))
        with open(css_file, 'r') as f:
            output = f.read()
        expected = '#main p{color:#00ff00;width:97%}#main p .redbox{background-color:#ff0000}#main p .redbox:hover{color:#000000}\n'
        self.assertEqual(expected, output)

    @override_settings(DEBUG=False)
    def test_management_command(self):
        call_command('compilescss')
        css_file = os.path.join(settings.PROJECT_ROOT, 'static/tests/css/main.css')
        with open(css_file, 'r') as f:
            output = f.read()
        expected = '#main p{color:#00ff00;width:97%}#main p .redbox{background-color:#ff0000}#main p .redbox:hover{color:#000000}\n'
        self.assertEqual(expected, output)
        self.assertFalse(os.path.exists(css_file + '.map'))

        call_command('compilescss', delete_files=True)
        self.assertFalse(os.path.exists(css_file))
