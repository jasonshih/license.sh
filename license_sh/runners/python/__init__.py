import asyncio
import json
import os
import subprocess
from json import JSONDecodeError

import aiohttp
from anytree import AnyNode
from yaspin import yaspin

from license_sh.helpers import flatten_dependency_tree
from license_sh.reporters.ConsoleReporter import ConsoleReporter


def add_nested_dependencies(dep, parent):
  name = dep['package_name']
  version = dep['installed_version']
  depdendencies = dep['dependencies']

  node = AnyNode(name=name, version=version, parent=parent)
  for dep in depdendencies:
    add_nested_dependencies(dep, node)


PYPI_HOST = 'https://pypi.org/pypi'


class PythonRunner:

  def __init__(self, directory: str, config):
    self.directory = directory
    self.verbose = True
    self.config = config

    self.pipfile_path: str = os.path.join(self.directory, 'Pipfile')
    self.pipfile_lock_path: str = os.path.join(self.directory, 'Pipfile.lock')

  @staticmethod
  def fetch_licenses(all_dependencies):
    license_map = {}

    urls = [f'{PYPI_HOST}/{dependency}/{version}/json' for dependency, version in all_dependencies]

    with yaspin(text="Fetching license info from pypi ...") as sp:
      async def fetch(session, url):
        async with session.get(url) as resp:
          return await resp.text()
          # Catch HTTP errors/exceptions here

      async def fetch_concurrent(urls):
        loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession() as session:
          tasks = []
          for u in urls:
            tasks.append(loop.create_task(fetch(session, u)))

          for result in asyncio.as_completed(tasks):
            try:
              page = json.loads(await result)
              info = page.get('info', {})
              license_map[f"{info.get('name')}@{info.get('version')}"] = info.get('license', 'Unknown')
            except JSONDecodeError:
              # TODO - investiage why does such a thing happen
              pass

      asyncio.run(fetch_concurrent(urls))

    return license_map

  def check(self):
    print(f"Checking {self.directory}")

    result = subprocess.run(['pipdeptree', '--json-tree', '--local-only'], stdout=subprocess.PIPE)
    dep_tree = json.loads(result.stdout)

    root = AnyNode(name='root', version='')

    for dep in dep_tree:
      add_nested_dependencies(dep, root)

    all_dependencies = flatten_dependency_tree(root)
    license_map = PythonRunner.fetch_licenses(all_dependencies)

    ConsoleReporter.output(root, [], license_map)
