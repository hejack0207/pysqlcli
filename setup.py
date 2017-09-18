#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup, find_packages

install_requires = [
    'click==6.7', 'cx_Oracle==6.0.2'
    ]

setup(name='pysqlcli',
      version='1.1',
      description='Python oracle client',
      author='hejack0207',
      author_email='hejack0207@sina.com',
      url='https://github.com/hejack0207/pysqlcli',
      #packages=['pysqlcli'],
      package_dir = {'': 'lib'},
      packages=find_packages('lib'),
      install_requires=install_requires,
      scripts=['bin/pysqlcli'],
     )
