#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages, Command
from sys import platform as _platform
from shutil import rmtree
import sys
import os

here = os.path.abspath(os.path.dirname(__file__))
NAME = 'LabelCraft'
REQUIRES_PYTHON = '>=3.8.0'
REQUIRED_DEP = ['pyside6>=6.5.0', 'lxml>=4.9.0']
about = {}

with open(os.path.join(here, 'libs', '__init__.py')) as f:
    exec(f.read(), about)

readme = ''
history = ''
try:
    with open("README.rst", "rb") as readme_file:
        readme = readme_file.read().decode("UTF-8")
except FileNotFoundError:
    try:
        with open("README.md", "rb") as readme_file:
            readme = readme_file.read().decode("UTF-8")
    except FileNotFoundError:
        readme = 'LabelCraft - A modern graphical image annotation tool'

try:
    with open("HISTORY.rst", "rb") as history_file:
        history = history_file.read().decode("UTF-8")
except FileNotFoundError:
    history = ''

SET_REQUIRES = []
if _platform == "darwin":
   SET_REQUIRES.append('py2app')

required_packages = find_packages(exclude=['tests', 'build', 'dist'])

APP = ['main.py']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'resources/icons/app.icns',
    'packages': [
        'PySide6',
        'lxml',
        'xml',
        'xml.etree',
        'json',
        'csv',
        'io',
        'codecs',
    ],
    'excludes': [
        'PySide6.QtNetwork',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
    ]
}

class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'

    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            self.status('Fail to remove previous builds..')
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system(
            '{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag -d v{0}'.format(about['__version__']))
        os.system('git tag v{0}'.format(about['__version__']))
        # os.system('git push --tags')

        sys.exit()


setup(
    app=APP if _platform == "darwin" else None,
    name=NAME,
    version=about['__version__'],
    description="LabelCraft - A modern graphical image annotation tool based on labelImg",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown' if 'README.md' in [f for f in os.listdir(here) if f.startswith('README')] else 'text/x-rst',
    author="LabelCraft Contributors",
    author_email='syd168@users.noreply.github.com',
    url='https://github.com/syd168/LabelCraft',
    python_requires=REQUIRES_PYTHON,
    py_modules=['main', 'labelcraft_ui', 'resources'],
    packages=required_packages,
    entry_points={
        'gui_scripts': [
            'labelcraft=main:main',
        ]
    },
    include_package_data=True,
    install_requires=REQUIRED_DEP,
    license="MIT license",
    zip_safe=False,
    keywords='labelCraft labelImg labelTool development annotation deeplearning',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Multimedia :: Graphics',
    ],
    options={'py2app': OPTIONS} if _platform == "darwin" else {},
    setup_requires=SET_REQUIRES,
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    }
)
