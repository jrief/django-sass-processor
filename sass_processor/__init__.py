# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
See PEP 386 (https://www.python.org/dev/peps/pep-0386/)

Release logic:
 1. Remove ".devX" from __version__ (below)
 2. Remove ".devX" latest version in README.md / Changelog
 3. git add sass_processor/__init__.py
 4. git commit -m 'Bump to <version>'
 5. git push
 6. (assure that all tests pass)
 7. git tag <version>
 8. git push --tags
 9. python setup.py sdist upload
10. bump the version, append ".dev0" to __version__
11. Add a new heading to README.md / Changelog, named "<next-version>.dev"
12. git add sass_processor/__init__.py README.md
12. git commit -m 'Start with <version>'
13. git push
"""

__version__ = '0.7.3'

default_app_config = 'sass_processor.apps.SassProcessorConfig'
