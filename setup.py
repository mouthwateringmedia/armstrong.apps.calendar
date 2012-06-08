import sys

from setuptools import setup, find_packages

setup(
    name = "armstrong.apps.calendar",
    version = '0.2',
    description = "Armstrong Calendar App.",
    url = "https://github.com/mouthwateringmedia/armstrong.apps.calendar",
    author = "Paul Bailey",
    author_email = "paul.m.bailey@gmail.com",
    license = "BSD",
    packages = [
      'armstrong',
      'armstrong.apps',
      'armstrong.apps.calendar',
      'armstrong.apps.calendar.migrations',
      'armstrong.apps.calendar.tests',
    ],
    include_package_data = True,
)

