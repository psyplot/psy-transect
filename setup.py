"""Setup file for plugin psy-transect

This file is used to install the package to your python distribution.
Installation goes simply via::

    python setup.py install
"""

from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name="psy-transect",
    version="0.0.1.dev0",
    description="Psyplot plugin for visualizing data along a transect",
    long_description=readme(),
    long_description_content_type="text/x-rst",
    keywords="visualization psyplot",
    license="GPLv3",
    packages=find_packages(exclude=["docs", "tests*", "examples"]),
    install_requires=[
        "psy-maps",
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
      ],
    python_requires=">=3.6",
    project_urls={
        'Documentation': 'https://github.com/psyplot/psy-transect',
        'Source': 'https://github.com/psyplot/psy-transect',
        'Tracker': 'https://github.com/psyplot/psy-transect/issues',
    },
    url='https://github.com/psyplot/psy-transect',
    author='Philipp S. Sommer',
    author_email='philipp.sommer@hzg.de',
    entry_points={"psyplot": ["plugin=psy_transect.plugin"]},
    zip_safe=False,
)
