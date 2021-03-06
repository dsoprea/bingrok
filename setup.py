import setuptools
import os

_APP_PATH = os.path.abspath(os.path.dirname(__file__))
_RESOURCES_PATH = os.path.join(_APP_PATH, 'bingrok', 'resources')

with open(os.path.join(_RESOURCES_PATH, 'README.rst')) as f:
      _LONG_DESCRIPTION = f.read()

with open(os.path.join(_RESOURCES_PATH, 'requirements.txt')) as f:
      _INSTALL_REQUIRES = list(map(lambda s: s.strip(), f.readlines()))

with open(os.path.join(_RESOURCES_PATH, 'version.txt')) as f:
      _VERSION = f.read()

_DESCRIPTION = \
    "A tool that allows you to browse binary data by iteratively seeking " \
    "and unpacking."

setuptools.setup(
    name='bingrok',
    version=_VERSION,
    description=_DESCRIPTION,
    long_description=_LONG_DESCRIPTION,
    keywords='unpack binary explore',
    author='Dustin Oprea',
    author_email='myselfasunder@gmail.com',
    url='https://github.com/dsoprea/bingrok',
    license='GPL 2',
    packages=setuptools.find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=_INSTALL_REQUIRES,
    package_data={
        'bingrok': [
            'resources/README.rst',
            'resources/requirements.txt',
            'resources/version.txt',
        ]
    },
    scripts=[
        'bingrok/resources/scripts/bingrok',
    ]
)
