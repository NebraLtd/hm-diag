# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
import os

base_name='hw_diag'

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name=base_name,
    version='1.0',
    author=u'Nebra Ltd.',
    author_email='nebra.com',
    include_package_data = True,
    packages=find_packages(), # include all packages under this directory
    description='to update',
    long_description="",
    zip_safe=False,

    entry_points = {'console_scripts': [
        'hm_diag = hw_diag.app:main',],},

    # Adds dependencies
    install_requires = ['flask',
                        'Flask-APScheduler',
                        'requests',
                        'dbus-python',
                        ]
)
