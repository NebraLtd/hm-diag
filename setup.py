# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
import os

base_name = 'hw_diag'

# allow setup.py to be run from any path
here = os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir))
os.chdir(here)

requires = [
    line.strip()
    for line in open(os.path.join(here, "requirements.txt"), "r").readlines()
]

setup(
    name=base_name,
    version='1.0',
    author=u'Nebra Ltd.',
    author_email='sales@nebra.com',
    include_package_data=True,
    packages=find_packages(),  # include all packages under this directory
    description='Diagnostics tool for Nebra Helium Hotspot software.',
    long_description="",
    zip_safe=False,

    entry_points={
        'console_scripts': [
            'hm_diag = hw_diag.app:main',
        ],
    },

    # Adds dependencies
    install_requires=requires
)
