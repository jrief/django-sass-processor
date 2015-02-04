# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import hashlib
import json
import sass
from django.conf import settings
from django.contrib.staticfiles.finders import get_finders
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.template.base import Context
from django.template import Template
from django.utils.safestring import mark_safe
from django.utils.six.moves.urllib.parse import urlparse
from django.utils.six.moves.urllib.request import url2pathname, pathname2url
from compressor.conf import CompressorConf
from compressor.utils import get_class


class SassFileStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = getattr(settings, 'SEKIZAI_PROCESSORS_ROOT', settings.STATIC_ROOT)
        if base_url is None:
            base_url = settings.STATIC_URL
        super(SassFileStorage, self).__init__(location, base_url, *args, **kwargs)


class SCSSProcessor(object):
    template = Template('<link href="{{ href }}"{% if type %} type="{{ type }}"{% endif %}{% if rel %} rel="{{ rel }}"{% endif %}{% if media %} media="{{ media }}"{% endif %} />')

    def __init__(self):
        self.Parser = get_class(CompressorConf.PARSER)
        self.base_url = urlparse(settings.STATIC_URL)
        self.include_paths = list(getattr(settings, 'SEKIZAI_PROCESSOR_INCLUDE_DIRS', []))
        self.storage = SassFileStorage()
        self.sass_exts = ('.scss', '.sass',)
        self._hash_cache = {}

    def __call__(self, context, data, namespace=None):
        parser = self.Parser(data)
        attribs_list = []
        for elem in parser.css_elems():
            attribs = parser.elem_attribs(elem)
            attribs_list.append(attribs)
            href = attribs.get('href')
            if not (href and href.startswith(self.base_url[2])):
                attribs_list.append(attribs)
            sass_name = url2pathname(href[len(self.base_url[2]):])
            base_name, ext = os.path.splitext(sass_name)
            filename = self.find(sass_name)
            if not filename or ext not in self.sass_exts:
                continue
            # check from timestamps, if we must recompile
            css_filename = base_name + '.css'
            attribs['href'] = self.storage.url(css_filename)
            sourcemap_filename = css_filename + '.map'
            if self.is_latest(sourcemap_filename):
                continue
            # otherwise compile the .scss file into .css and store it
            source_map_url = self.storage.url(sourcemap_filename)
            content, sourcemap = sass.compile(filename=filename,
                source_map_filename=source_map_url, include_paths=self.include_paths)
            if self.storage.exists(css_filename):
                self.storage.delete(css_filename)
            self.storage.save(css_filename, ContentFile(content))
            if self.storage.exists(sourcemap_filename):
                self.storage.delete(sourcemap_filename)
            self.storage.save(sourcemap_filename, ContentFile(sourcemap))
        return mark_safe(''.join(self.template.render(Context(ctx)) for ctx in attribs_list))

    def is_latest(self, sourcemap_filename):
        sourcemap_filename = self.find(sourcemap_filename)
        if not sourcemap_filename or not os.path.isfile(sourcemap_filename):
            return False
        sourcemap_mtime = os.stat(sourcemap_filename).st_mtime
        with open(sourcemap_filename, 'r') as fp:
            sourcemap = json.load(fp)
        for srcfilename in sourcemap.get('sources'):
            components = os.path.normpath(srcfilename).split(os.path.sep)
            srcfilename = ''.join([os.path.sep + c for c in components if c != os.path.pardir])
            if not os.path.isfile(srcfilename) or os.stat(srcfilename).st_mtime > sourcemap_mtime:
                # at least one of the source is younger that the sourcemap referring it, therefore recompile
                return False
        return True

    def compile_offline(self, srcpath):
        sass_name = url2pathname(srcpath)
        sass_filename = self.find(sass_name)
        if not sass_filename:
            return
        base_name, ext = os.path.splitext(sass_filename)
        if ext not in self.sass_exts:
            return
        content = sass.compile(include_paths=self.include_paths, filename=sass_filename, output_style='compact')
        destpath = base_name + '.css'
        with open(destpath, 'w') as fh:
            fh.write(content)
        return destpath

    def find(self, path):
        for finder in get_finders():
            result = finder.find(path)
            if result:
                return result

    def file_hash(self, filename):
        """Currently unused: Hash the content of the file"""
        blocksize = 65536
        if filename in self._hash_cache:
            mtime = os.stat(filename).st_mtime
            if mtime == self._hash_cache[filename][1]:
                return self._hash_cache[filename][0]
        md5 = hashlib.md5()
        with open(filename, 'rb') as content:
            while True:
                buf = content.read(blocksize)
                if len(buf) > 0:
                    md5.update(buf)
                else:
                    break
        hashsum = md5.hexdigest()[:12]
        self._hash_cache[filename] = (hashsum, os.stat(filename).st_mtime)
        return hashsum

compilescss = SCSSProcessor()
