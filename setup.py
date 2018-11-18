import os,sys
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop


_here = os.path.abspath(os.path.dirname(__file__))
#dir_mtree = os.path.join(_here,'metricaltree')

def configure_home_dir():
	# make sure directory exists
	from os.path import expanduser
	home = expanduser("~")
	dir_prosodic_home=os.path.join(home,'.prosodic')
	dir_meter_home=os.path.join(dir_prosodic_home,'meters')
	for dir in [dir_prosodic_home,dir_meter_home]:
		if not os.path.exists(dir): os.makedirs(dir)

	# copy defaults
	ipath_config = os.path.join(_here,'prosodic','config.py')
	ipath_meter = os.path.join(_here,'prosodic','meters','meter_default.py')
	opath_config = os.path.join(dir_prosodic_home,'config_default.py')
	opath_meter = os.path.join(dir_meter_home,'meter_default.py')

	# copy
	import shutil
	print '>> copying:',ipath_config,'-->',opath_config
	shutil.copyfile(ipath_config,opath_config)
	print '>> copying:',ipath_meter,'-->',opath_meter
	shutil.copyfile(ipath_meter,opath_meter)



class PostDevelopCommand(develop):
	"""Post-installation for development mode."""
	def run(self):
		configure_home_dir()
		develop.run(self)

class PostInstallCommand(install):
	"""Post-installation for installation mode."""
	def run(self):
		configure_home_dir()
		install.run(self)

with open("README.md", "r") as fh:
	long_description = fh.read()

with open("requirements.txt", "r") as fh:
	requirements = [x.strip() for x in fh.read().split('\n') if x.strip()]

setup(
	name='prosodic',
	version='1.1.22',
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
	classifiers=[
		#'Development Status :: 3 - Alpha',
		#'Intended Audience :: Science/Research',
		#'Programming Language :: Python :: 2.7',
		#'Programming Language :: Python :: 3.6'
	],
	)
