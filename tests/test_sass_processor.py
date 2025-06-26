import calendar
import os
import shutil
from datetime import datetime

from django.conf import settings
from django.core.management import call_command
from django.template.loader import get_template
from django.test import TestCase, override_settings


class SassProcessorTest(TestCase):

    def setUp(self):
        super(SassProcessorTest, self).setUp()
        try:
            os.mkdir(settings.STATIC_ROOT)
        except OSError:
            pass

    def tearDown(self):
        shutil.rmtree(settings.STATIC_ROOT)

    def assert_sass_src_engine(self, template_name, engine):
        template = get_template(
            template_name=template_name,
            using=engine
        )
        # Strip the line breaks.
        template_content = template.render({}).strip()
        assert template_content == '/static/tests/css/main.css'

        css_file = settings.STATIC_ROOT / 'tests/css/main.css'
        assert css_file.exists()
        with css_file.open('r') as f:
            output = f.read()
        expected = "#main p{color:#00ff00;width:97%}#main p .redbox{background-color:#ff0000}#main p .redbox:hover{color:#000000}\n\n/*# sourceMappingURL=main.css.map */"
        assert expected == output

        # check if compilation is skipped file for a second invocation of `sass_src`
        timestamp = css_file.stat().st_mtime
        template.render({})
        assert timestamp == css_file.stat().st_mtime

        # removing `main.css.map` should trigger a recompilation
        css_file.with_suffix(css_file.suffix + '.map').unlink()
        template.render({})
        assert css_file.with_suffix(css_file.suffix + '.map').exists()

        # if `main.scss` is newer than `main.css`, recompile everything
        longago = calendar.timegm(datetime(2017, 1, 1).timetuple())
        os.utime(css_file, (longago, longago))
        template.render({})
        assert timestamp > css_file.stat().st_mtime

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
        css_file = settings.STATIC_ROOT / 'tests/css/bluebox.css'
        assert css_file.exists()
        with css_file.open('r') as f:
            output = f.read()
        expected = '.bluebox{background-color:#0000ff;margin:10.0px 5.0px 20.0px 15.0px;color:#fa0a78}\n\n/*# sourceMappingURL=bluebox.css.map */'
        assert expected == output

    def assert_management_command(self, **kwargs):
        call_command(
            'compilescss',
            **kwargs
        )
        if kwargs.get('use_storage', False):
            css_file = settings.STATIC_ROOT / 'tests/css/main.css'
        else:
            css_file = settings.PROJECT_ROOT / 'static/tests/css/main.css'
        with css_file.open('r') as f:
            output = f.read()
        expected = '#main p{color:#00ff00;width:97%}#main p .redbox{background-color:#ff0000}#main p .redbox:hover{color:#000000}\n'
        assert expected == output
        assert not css_file.with_suffix(css_file.suffix + '.map').exists()

        if not kwargs.get('use_storage', False):
            call_command('compilescss', delete_files=True)
            assert not css_file.exists()

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
    def test_use_storage_django(self):
        self.assert_management_command(
            engine='django',
            use_storage=True
        )

    @override_settings(DEBUG=False)
    def test_use_storage_jinja2(self):
        self.assert_management_command(
            engine='jinja2',
            use_storage=True
        )

    @override_settings(DEBUG=False)
    def test_use_storage_multiple(self):
        self.assert_management_command(
            engine=['jinja2', 'django'],
            use_storage=True
        )

    @override_settings(
        DEBUG=False,
        SASS_PROCESSOR_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
        STATICFILES_STORAGE='django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    )
    def test_manifest_static_files_storage(self):
        css_file = settings.PROJECT_ROOT / 'static/tests/css/main.css'
        assert not css_file.exists()
        call_command('compilescss', use_storage=False)
        assert css_file.exists()
        with css_file.open('r') as f:
            output = f.read()
        expected = '#main p{color:#00ff00;width:97%}#main p .redbox{background-color:#ff0000}#main p .redbox:hover{color:#000000}\n'
        assert expected == output
        hashed_css_file = settings.PROJECT_ROOT / 'tmpstatic/tests/css/main.08b498e281f7.css'
        assert not hashed_css_file.exists()
        call_command('collectstatic', interactive=False, ignore_patterns=['*.scss'])
        assert hashed_css_file.exists()
        with hashed_css_file.open('r') as f:
            output = f.read()
        assert expected == output
        call_command('compilescss', use_storage=False, delete_files=True)
