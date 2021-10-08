# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
import os

base_name = 'hw_diag'

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

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

    entry_points={'console_scripts': [
        'hm_diag = hw_diag.app:main', ], },

    # Adds dependencies
    install_requires=['Flask==2.0.1',
                      'Flask-APScheduler==1.12.2',
                      'requests==2.26.0',
                      'hm-pyhelper==0.4',
                      'click==7.1.2'
                      ]
)
