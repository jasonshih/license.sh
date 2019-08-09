#!/usr/bin/env python
"""License.sh

Usage:
  license-sh.py
  license-sh.py <path>
  license-sh.py (-h | --help)
  license-sh.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

VERSION = "1.0.0"

import json

from docopt import docopt

from license_sh.project_identifier import get_project_types, ProjectType
from license_sh.runners.npm import NpmRunner
from license_sh.runners.python import PythonRunner

if __name__ == '__main__':
  arguments = docopt(__doc__, version=VERSION)

  path = arguments['<path>'] or '.'

  try:
    with open('./.license-sh.json') as license_file:
      config = json.load(license_file)

      project_types = get_project_types(path)

      if ProjectType.PYTHON_PIPENV in project_types:
        runner = PythonRunner(path, config)
        runner.check()

      if ProjectType.NPM in project_types:
        runner = NpmRunner(path, config)
        runner.check()

  except FileNotFoundError:
    # TODO = test - file does not exist
    print('File not found')
    exit(1)
    # TODO = test - no permission to read the file
  except PermissionError:
    print('No permission to read the file .license-sh.json')
    exit(2)
