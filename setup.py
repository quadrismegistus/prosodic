import os,sys
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
from distutils.dir_util import copy_tree
from os.path import expanduser






_here = os.path.abspath(os.path.dirname(__file__))
#dir_mtree = os.path.join(_here,'metricaltree')
home = expanduser("~")
default_dir_prosodic_home=os.path.join(home,'prosodic_data')
path_prosodic_home_dir_var = os.path.join(home,'.path_prosodic_data')


import sys,os,imp
path_to_tools = os.path.join(_here,'prosodic','lib','tools.py')
tools = imp.load_source('tools',path_to_tools)


class PostDevelopCommand(develop):
	"""Post-installation for development mode."""
	def run(self):
		tools.configure_home_dir(force=True)
		develop.run(self)

class PostInstallCommand(install):
	"""Post-installation for installation mode."""
	def run(self):
		tools.configure_home_dir(force=True)
		install.run(self)

if __name__ == '__main__':
	with open("README.md", "r") as fh:
		long_description = fh.read()

	with open("requirements.txt", "r") as fh:
		requirements = [x.strip() for x in fh.read().split('\n') if x.strip()]

	setup(
		name='prosodic',
		version='1.3.11',
		description=('PROSODIC: a metrical-phonological parser, written in Python. For English and Finnish, with flexible language support.'),
		long_description=long_description,
		long_description_content_type="text/markdown",
		author='Ryan Heuser',
		author_email='heuser@stanford.edu',
		url='https://github.com/quadrismegistus/prosodic',
		license='MPL-2.0',
		packages=['prosodic','metricaltree'],
		install_requires=requirements,
		include_package_data=True,
		cmdclass={
			'develop': PostDevelopCommand,
			'install': PostInstallCommand,
		},
		scripts=['bin/prosodic'],
		classifiers=[
			#'Development Status :: 3 - Alpha',
			#'Intended Audience :: Science/Research',
			#'Programming Language :: Python :: 2.7',
			#'Programming Language :: Python :: 3.6'
		],
		)


	#
	# nltk==3.4
	# numpy==1.15.4
	# Pyphen==0.9.5
