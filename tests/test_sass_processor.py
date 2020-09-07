import calendar
import os
from pathlib import Path
import shutil
from datetime import datetime

import py
from django.conf import settings
from django.core.management import call_command
from django.template.loader import get_template
from django.test import TestCase, override_settings


@override_settings(STATIC_ROOT=py.test.ensuretemp('static').strpath)
class SassProcessorTest(TestCase):

    def setUp(self):
        super(SassProcessorTest, self).setUp()
        Path(settings.STATIC_ROOT).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(settings.STATIC_ROOT)

    def assert_sass_src_engine(self, template_name, engine):
        template = get_template(
            template_name=template_name,
            using=engine
        )
        # Strip the line breaks.
        template_content = template.render({}).strip()
        self.assertEqual('/static/tests/css/main.css', template_content)

        css_filepath = Path(settings.STATIC_ROOT) / 'tests/css/main.css'
        self.assertTrue(css_filepath.is_file())
        output = css_filepath.open().read()
        expected = "#main p{color:#00ff00;width:97%}#main p .redbox{background-color:#ff0000}#main p .redbox:hover{color:#000000}\n\n/*# sourceMappingURL=main.css.map */"
        self.assertEqual(expected, output)

        # check if compilation is skipped file for a second invocation of `sass_src`
        timestamp = css_filepath.stat().st_mtime
        template.render({})
        self.assertEqual(timestamp, css_filepath.stat().st_mtime)

        # removing `main.css.map` should trigger a recompilation
        (css_filepath + '.map').unlink()
        template.render({})
        self.assertTrue((css_filepath + '.map').is_file())

        # if `main.scss` is newer than `main.css`, recompile everything
        longago = calendar.timegm(datetime(2017, 1, 1).timetuple())
        os.utime(css_filepath.resolve(), (longago, longago))
        template.render({})
        self.assertGreater(timestamp, css_filepath.stat().st_mtime)

    def test_sass_src_django(self):
        self.assert_sass_src_engine(
            template_name='tests/django.html',
            engine='django'
        )

    def test_sass_src_jinja2(self):
        self.assert_sass_src_engine(
            template_name='tests/jinja2.html',
            engine='jinja2'
        )

    def test_sass_src_jinja2_variable(self):
        self.assert_sass_src_engine(
            template_name='tests/jinja2_variable.html',
            engine='jinja2'
        )

    def test_sass_processor(self):
        from sass_processor.processor import sass_processor

        css_file = sass_processor('tests/css/bluebox.scss')
        self.assertEqual('/static/tests/css/bluebox.css', css_file)
        css_filepath = Path(settings.STATIC_ROOT) / 'tests/css/bluebox.css'
        self.assertTrue(css_filepath.is_file())
        output = css_filepath.open().read()
        expected = '.bluebox{background-color:#0000ff;margin:10.0px 5.0px 20.0px 15.0px;color:#fa0a78}\n\n/*# sourceMappingURL=bluebox.css.map */'
        self.assertEqual(expected, output)

    def assert_management_command(self, **kwargs):
        call_command(
            'compilescss',
            **kwargs
        )
        if kwargs.get('use_processor_root', False):
            css_filepath = Path(settings.STATIC_ROOT) / 'tests/css/main.css'
        else:
            css_filepath = Path(settings.PROJECT_ROOT) / 'static/tests/css/main.css'
        output = css_filepath.open().read()
        expected = '#main p{color:#00ff00;width:97%}#main p .redbox{background-color:#ff0000}#main p .redbox:hover{color:#000000}\n'
        self.assertEqual(expected, output)
        self.assertFalse((css_filepath + '.map').is_file())

        if not kwargs.get('use_processor_root', False):
            call_command('compilescss', delete_files=True)
            self.assertFalse(css_filepath.is_file())

    @override_settings(DEBUG=False)
    def test_management_command_django(self):
        self.assert_management_command(
            engine='django'
        )

    @override_settings(DEBUG=False)
    def test_management_command_jinja2(self):
        self.assert_management_command(
            engine='jinja2'
        )

    @override_settings(DEBUG=False)
    def test_management_command_multiple(self):
        self.assert_management_command(
            engine=['jinja2', 'django']
        )

    @override_settings(DEBUG=False)
    def test_use_processor_root_django(self):
        self.assert_management_command(
            engine='django',
            use_processor_root=True
        )

    @override_settings(DEBUG=False)
    def test_use_processor_root_jinja2(self):
        self.assert_management_command(
            engine='jinja2',
            use_processor_root=True
        )

    @override_settings(DEBUG=False)
    def test_use_processor_root_multiple(self):
        self.assert_management_command(
            engine=['jinja2', 'django'],
            use_processor_root=True
        )
